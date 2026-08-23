from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.declaration import Declaration
from app.models.inspection import (
    ComplianceResultStatus,
    Inspection,
    InspectionStatus,
)
from app.models.violation import Violation, ViolationSeverity, ViolationStatus
from app.services.extraction_service import DeclarationExtractor, ExtractedDeclaration
from app.services.inspection_service import InspectionService
from app.services.ocr_service import OCRResult, get_ocr_provider
from compliance_engine.rule_engine import ComplianceResult, LegalMetrologyComplianceEngine


class ComplianceService:
    @staticmethod
    async def run_full_pipeline(
        db: AsyncSession, inspection_id: int, ocr_provider_name: Optional[str] = None
    ) -> Inspection:
        """
        Execute the end-to-end scanning, OCR, declaration extraction,
        rule compliance check, and violation generation pipeline.
        """
        inspection = await InspectionService.get_inspection(db, inspection_id)

        if not inspection.images:
            raise ValidationError(
                f"Inspection #{inspection_id} has no uploaded images. Please upload package images first."
            )

        # Set status to processing
        inspection.status = InspectionStatus.PROCESSING
        await db.commit()

        try:
            ocr_provider = get_ocr_provider(ocr_provider_name)
            all_extracted_declarations: List[ExtractedDeclaration] = []
            mean_confidences: List[float] = []

            # 1. Clear any previous declarations/violations for clean re-run
            for old_dec in list(inspection.declarations):
                await db.delete(old_dec)
            for old_viol in list(inspection.violations):
                await db.delete(old_viol)
            await db.flush()

            # 2. Process each uploaded image
            for img_record in inspection.images:
                logger.info(f"Running OCR on image {img_record.image_path} (Inspection #{inspection_id})")
                ocr_result: OCRResult = await ocr_provider.extract_text(img_record.image_path)
                mean_confidences.append(ocr_result.mean_confidence)

                # Extract declarations
                extracted = DeclarationExtractor.extract_all(
                    ocr_result=ocr_result, image_path=img_record.image_path
                )
                all_extracted_declarations.extend(extracted)

                # Persist declarations to DB
                for ext in extracted:
                    db_decl = Declaration(
                        inspection_id=inspection.id,
                        declaration_type=ext.declaration_type,
                        extracted_value=ext.extracted_value,
                        normalized_value=ext.normalized_value,
                        confidence=ext.confidence,
                        source_image=ext.source_image,
                        bounding_box=ext.bounding_box,
                        is_valid=ext.is_valid,
                    )
                    inspection.declarations.append(db_decl)

            await db.flush()

            # 3. Execute Legal Metrology Rule Compliance Engine
            engine = LegalMetrologyComplianceEngine()
            avg_ocr_conf = sum(mean_confidences) / len(mean_confidences) if mean_confidences else 0.90

            context = {
                "product_name": inspection.product.product_name if inspection.product else None,
                "ocr_mean_confidence": avg_ocr_conf,
            }

            compliance_res: ComplianceResult = engine.evaluate(
                declarations=all_extracted_declarations, context=context
            )

            # 4. Save detected Violations
            for v_data in compliance_res.violations:
                severity_enum = ViolationSeverity(v_data.get("severity", "HIGH"))
                violation = Violation(
                    inspection_id=inspection.id,
                    rule_id=v_data["rule_id"],
                    violation_type=v_data["violation_type"],
                    description=v_data["description"],
                    severity=severity_enum,
                    evidence_image=v_data.get("evidence_image"),
                    detected_value=v_data.get("detected_value"),
                    expected_value=v_data.get("expected_value"),
                    status=ViolationStatus.OPEN,
                )
                inspection.violations.append(violation)

            # 5. Update Inspection results and status
            inspection.compliance_score = compliance_res.score_result.percentage
            inspection.overall_result = compliance_res.score_result.status
            inspection.status = InspectionStatus.COMPLETED

            # Record audit log
            audit = AuditLog(
                user_id=inspection.inspector_id,
                action="COMPLIANCE_EVALUATED",
                entity_type="INSPECTION",
                entity_id=str(inspection.id),
                metadata_json={
                    "score": inspection.compliance_score,
                    "status": inspection.overall_result.value,
                    "violations_count": len(compliance_res.violations),
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(
                f"Inspection #{inspection_id} completed: score={inspection.compliance_score}%, "
                f"result={inspection.overall_result.value}"
            )

            return await InspectionService.get_inspection(db, inspection_id)

        except Exception as e:
            inspection.status = InspectionStatus.FAILED
            await db.commit()
            logger.error(f"Scan pipeline failed for inspection #{inspection_id}: {e}")
            raise

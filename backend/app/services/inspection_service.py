from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.inspection import (
    ComplianceResultStatus,
    Inspection,
    InspectionImage,
    InspectionStatus,
)
from app.models.product import Product
from app.models.violation import Violation
from app.schemas.inspection import InspectionCreate
from app.utils.file_utils import save_upload_image


class InspectionService:
    @staticmethod
    async def create_inspection(
        db: AsyncSession, inspector_id: int, payload: InspectionCreate
    ) -> Inspection:
        """Create a new inspection session."""
        product_id = payload.product_id

        # Auto-create or link product if product info is provided
        if not product_id and payload.product_name:
            if payload.barcode:
                prod_res = await db.execute(
                    select(Product).where(Product.barcode == payload.barcode.strip())
                )
                existing_product = prod_res.scalar_one_or_none()
                if existing_product:
                    product_id = existing_product.id
            
            if not product_id:
                new_product = Product(
                    product_name=payload.product_name.strip(),
                    barcode=payload.barcode.strip() if payload.barcode else None,
                    category=payload.category.strip() if payload.category else None,
                    manufacturer=payload.manufacturer.strip() if payload.manufacturer else None,
                )
                db.add(new_product)
                await db.flush()
                product_id = new_product.id

        elif product_id:
            # Verify product exists
            prod_res = await db.execute(select(Product).where(Product.id == product_id))
            if not prod_res.scalar_one_or_none():
                raise NotFoundError(f"Product with ID {product_id} does not exist")

        inspection = Inspection(
            product_id=product_id,
            inspector_id=inspector_id,
            status=InspectionStatus.PENDING,
            compliance_score=None,
            overall_result=ComplianceResultStatus.PENDING,
        )
        db.add(inspection)
        await db.flush()
        await db.refresh(inspection)

        # Audit log
        audit = AuditLog(
            user_id=inspector_id,
            action="INSPECTION_CREATED",
            entity_type="INSPECTION",
            entity_id=str(inspection.id),
            metadata_json={"product_id": product_id},
        )
        db.add(audit)
        await db.commit()

        return await InspectionService.get_inspection(db, inspection.id)

    @staticmethod
    async def get_inspection(db: AsyncSession, inspection_id: int) -> Inspection:
        """Fetch inspection with all associated entities."""
        stmt = (
            select(Inspection)
            .where(Inspection.id == inspection_id)
            .options(
                selectinload(Inspection.product),
                selectinload(Inspection.images),
                selectinload(Inspection.declarations),
                selectinload(Inspection.violations),
                selectinload(Inspection.report),
            )
        )
        result = await db.execute(stmt)
        inspection = result.scalar_one_or_none()

        if not inspection:
            raise NotFoundError(f"Inspection with ID {inspection_id} not found")

        return inspection

    @staticmethod
    async def list_inspections(
        db: AsyncSession,
        inspector_id: Optional[int] = None,
        status: Optional[InspectionStatus] = None,
        overall_result: Optional[ComplianceResultStatus] = None,
        product_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Inspection], int]:
        """List inspections with filtering and pagination."""
        stmt = select(Inspection).options(selectinload(Inspection.product))
        count_stmt = select(func.count(Inspection.id))

        filters = []
        if inspector_id is not None:
            filters.append(Inspection.inspector_id == inspector_id)

        if status is not None:
            filters.append(Inspection.status == status)

        if overall_result is not None:
            filters.append(Inspection.overall_result == overall_result)

        if product_id is not None:
            filters.append(Inspection.product_id == product_id)

        if search:
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.outerjoin(Product, Inspection.product_id == Product.id)
            count_stmt = count_stmt.outerjoin(Product, Inspection.product_id == Product.id)
            filters.append(
                or_(
                    Product.product_name.ilike(search_pattern),
                    Product.barcode.ilike(search_pattern),
                    Product.manufacturer.ilike(search_pattern),
                )
            )

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total_result = await db.execute(count_stmt)
        total_items = total_result.scalar_one() or 0

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Inspection.id.desc()).offset(offset).limit(page_size)

        result = await db.execute(stmt)
        inspections = list(result.scalars().all())

        return inspections, total_items

    @staticmethod
    async def add_inspection_images(
        db: AsyncSession, inspection_id: int, files: List[UploadFile]
    ) -> List[InspectionImage]:
        """Upload and associate package images with an inspection."""
        inspection = await InspectionService.get_inspection(db, inspection_id)

        if not files:
            raise ValidationError("At least one image file must be uploaded")

        created_images: List[InspectionImage] = []

        for file in files:
            rel_path, file_size, mime_type = await save_upload_image(
                file=file, subfolder=f"inspections/{inspection_id}"
            )
            image_record = InspectionImage(
                inspection_id=inspection.id,
                image_path=rel_path,
                original_filename=file.filename or "unknown.jpg",
                file_size_bytes=file_size,
                mime_type=mime_type,
            )
            db.add(image_record)
            created_images.append(image_record)

        await db.commit()
        for img in created_images:
            await db.refresh(img)

        logger.info(
            f"Uploaded {len(created_images)} image(s) for Inspection #{inspection_id}"
        )
        return created_images

    @staticmethod
    async def get_inspection_violations(
        db: AsyncSession, inspection_id: int
    ) -> List[Violation]:
        """Fetch all violations detected in an inspection."""
        await InspectionService.get_inspection(db, inspection_id)
        result = await db.execute(
            select(Violation)
            .where(Violation.inspection_id == inspection_id)
            .order_by(Violation.id.asc())
        )
        return list(result.scalars().all())

from datetime import datetime
import os
from pathlib import Path
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ReportGenerationError
from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.models.inspection import Inspection
from app.models.report import Report
from app.services.inspection_service import InspectionService


class ReportService:
    """Service for generating official Legal Metrology Compliance Inspection Audit Reports."""

    @staticmethod
    async def generate_inspection_pdf(
        db: AsyncSession, inspection_id: int
    ) -> Report:
        """Generate official PDF compliance report for an inspection."""
        inspection = await InspectionService.get_inspection(db, inspection_id)

        report_dir = settings.report_path
        report_filename = f"inspection_report_{inspection_id}.pdf"
        report_dest = report_dir / report_filename

        try:
            doc = SimpleDocTemplate(
                str(report_dest),
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36,
            )

            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                "DocTitle",
                parent=styles["Heading1"],
                fontSize=18,
                leading=22,
                textColor=colors.HexColor("#1A365D"),
                alignment=1,  # Center
                spaceAfter=4,
            )
            subtitle_style = ParagraphStyle(
                "DocSubtitle",
                parent=styles["Normal"],
                fontSize=10,
                leading=13,
                textColor=colors.HexColor("#4A5568"),
                alignment=1,
                spaceAfter=12,
            )
            section_heading = ParagraphStyle(
                "SectionHeading",
                parent=styles["Heading2"],
                fontSize=12,
                leading=16,
                textColor=colors.HexColor("#2B6CB0"),
                spaceBefore=10,
                spaceAfter=6,
            )
            cell_bold = ParagraphStyle(
                "CellBold",
                parent=styles["Normal"],
                fontSize=9,
                leading=12,
                textColor=colors.HexColor("#2D3748"),
                fontName="Helvetica-Bold",
            )
            cell_normal = ParagraphStyle(
                "CellNormal",
                parent=styles["Normal"],
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor("#2D3748"),
            )

            story = []

            # 1. Header Banner
            story.append(
                Paragraph("NIRIKSHAK AI - LEGAL METROLOGY COMPLIANCE AUDIT", title_style)
            )
            story.append(
                Paragraph(
                    "Statutory Inspection Report under Legal Metrology (Packaged Commodities) Rules, 2011",
                    subtitle_style,
                )
            )
            story.append(
                HRFlowable(
                    width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10
                )
            )

            # 2. Executive Summary Card
            score_val = inspection.compliance_score if inspection.compliance_score is not None else 0.0
            status_val = inspection.overall_result.value

            status_bg = colors.HexColor("#C6F6D5") if status_val == "COMPLIANT" else (
                colors.HexColor("#FEEBC8") if status_val == "WARNING" else colors.HexColor("#FED7D7")
            )
            status_text_color = "#22543D" if status_val == "COMPLIANT" else (
                "#7B341E" if status_val == "WARNING" else "#742A2A"
            )

            summary_data = [
                [
                    Paragraph(f"<b>Inspection ID:</b> #{inspection.id}", cell_normal),
                    Paragraph(f"<b>Date:</b> {inspection.inspection_date.strftime('%d-%b-%Y %H:%M')}", cell_normal),
                ],
                [
                    Paragraph(f"<b>Inspector:</b> {inspection.inspector.name if inspection.inspector else 'N/A'}", cell_normal),
                    Paragraph(f"<b>Compliance Score:</b> <b>{score_val:.1f}%</b>", cell_normal),
                ],
                [
                    Paragraph(
                        f"<b>Overall Status:</b> <font color='{status_text_color}'><b>{status_val}</b></font>",
                        cell_normal,
                    ),
                    Paragraph(f"<b>Total Violations:</b> {len(inspection.violations)}", cell_normal),
                ],
            ]

            summary_table = Table(summary_data, colWidths=[270, 270])
            summary_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EDF2F7")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ])
            )
            story.append(summary_table)
            story.append(Spacer(1, 12))

            # 3. Product Details
            story.append(Paragraph("1. Packaged Product Information", section_heading))
            prod = inspection.product
            prod_data = [
                [
                    Paragraph("Product Name:", cell_bold),
                    Paragraph(prod.product_name if prod else "Not specified", cell_normal),
                    Paragraph("Barcode / EAN:", cell_bold),
                    Paragraph(prod.barcode if prod and prod.barcode else "N/A", cell_normal),
                ],
                [
                    Paragraph("Category:", cell_bold),
                    Paragraph(prod.category if prod and prod.category else "General", cell_normal),
                    Paragraph("Manufacturer:", cell_bold),
                    Paragraph(prod.manufacturer if prod and prod.manufacturer else "N/A", cell_normal),
                ],
            ]
            prod_table = Table(prod_data, colWidths=[100, 170, 100, 170])
            prod_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFFFF")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(prod_table)
            story.append(Spacer(1, 10))

            # 4. Declarations Extracted
            story.append(Paragraph("2. OCR Extracted Declarations", section_heading))
            decl_headers = [
                Paragraph("<b>Declaration Type</b>", cell_bold),
                Paragraph("<b>Detected Label Value</b>", cell_bold),
                Paragraph("<b>Normalized Value</b>", cell_bold),
                Paragraph("<b>Valid</b>", cell_bold),
            ]
            decl_rows = [decl_headers]
            for d in inspection.declarations:
                valid_str = "<font color='green'><b>YES</b></font>" if d.is_valid else "<font color='red'><b>NO</b></font>"
                decl_rows.append([
                    Paragraph(d.declaration_type.replace("_", " ").title(), cell_normal),
                    Paragraph(d.extracted_value or "-", cell_normal),
                    Paragraph(d.normalized_value or "-", cell_normal),
                    Paragraph(valid_str, cell_normal),
                ])

            if len(decl_rows) == 1:
                decl_rows.append([Paragraph("No declarations extracted", cell_normal), Paragraph("-", cell_normal), Paragraph("-", cell_normal), Paragraph("-", cell_normal)])

            decl_table = Table(decl_rows, colWidths=[130, 200, 150, 60])
            decl_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(decl_table)
            story.append(Spacer(1, 10))

            # 5. Detected Violations
            story.append(Paragraph("3. Legal Metrology Violations & Non-Compliances", section_heading))
            viol_headers = [
                Paragraph("<b>Rule ID</b>", cell_bold),
                Paragraph("<b>Violation Type</b>", cell_bold),
                Paragraph("<b>Severity</b>", cell_bold),
                Paragraph("<b>Description & Finding</b>", cell_bold),
            ]
            viol_rows = [viol_headers]
            for v in inspection.violations:
                sev_color = "#E53E3E" if v.severity.value == "CRITICAL" else ("#DD6B20" if v.severity.value == "HIGH" else "#D69E2E")
                viol_rows.append([
                    Paragraph(f"<b>{v.rule_id}</b>", cell_normal),
                    Paragraph(v.violation_type, cell_normal),
                    Paragraph(f"<font color='{sev_color}'><b>{v.severity.value}</b></font>", cell_normal),
                    Paragraph(v.description, cell_normal),
                ])

            if len(viol_rows) == 1:
                viol_rows.append([
                    Paragraph("<font color='green'><b>None</b></font>", cell_normal),
                    Paragraph("No violations detected", cell_normal),
                    Paragraph("-", cell_normal),
                    Paragraph("All tested legal requirements passed successfully.", cell_normal),
                ])

            viol_table = Table(viol_rows, colWidths=[80, 130, 70, 260])
            viol_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ])
            )
            story.append(viol_table)
            story.append(Spacer(1, 16))

            # 6. Statutory Disclaimer & Verification Stamp
            footer_text = (
                "<b>Notice:</b> This compliance report was automatically generated by the Nirikshak AI Legal "
                "Metrology Compliance Engine in accordance with the Legal Metrology (Packaged Commodities) "
                "Rules, 2011. Generated on " + datetime.now().strftime("%d-%b-%Y %H:%M:%S") + "."
            )
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=6))
            story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7.5, leading=10, textColor=colors.HexColor("#718096"))))

            # Build PDF document
            doc.build(story)

            # Persist / Update Report record in DB
            rel_report_path = f"reports/{report_filename}"
            existing_report = await db.execute(
                select(Report).where(Report.inspection_id == inspection.id)
            )
            rep_record = existing_report.scalar_one_or_none()

            if not rep_record:
                rep_record = Report(
                    inspection_id=inspection.id,
                    report_path=rel_report_path,
                    report_type="PDF",
                )
                db.add(rep_record)
            else:
                rep_record.report_path = rel_report_path
                rep_record.generated_at = datetime.now()

            # Record audit log
            audit = AuditLog(
                user_id=inspection.inspector_id,
                action="REPORT_GENERATED",
                entity_type="REPORT",
                entity_id=str(inspection.id),
                metadata_json={"report_path": rel_report_path},
            )
            db.add(audit)
            await db.commit()
            await db.refresh(rep_record)

            logger.info(f"Generated compliance report for Inspection #{inspection_id} at {report_dest}")
            return rep_record

        except Exception as e:
            logger.error(f"Failed to generate report for inspection #{inspection_id}: {e}")
            raise ReportGenerationError(f"PDF generation failed: {str(e)}")

    @staticmethod
    async def get_report_file(db: AsyncSession, inspection_id: int) -> Path:
        """Get absolute path to inspection PDF report, generating if not already present."""
        result = await db.execute(
            select(Report).where(Report.inspection_id == inspection_id)
        )
        report_record = result.scalar_one_or_none()

        report_file = settings.report_path / f"inspection_report_{inspection_id}.pdf"

        if not report_record or not report_file.exists():
            report_record = await ReportService.generate_inspection_pdf(
                db=db, inspection_id=inspection_id
            )
            report_file = settings.report_path / f"inspection_report_{inspection_id}.pdf"

        return report_file

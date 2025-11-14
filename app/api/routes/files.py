"""
File Upload/Download and Report Generation API
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from typing import List, Optional
from datetime import datetime
from loguru import logger

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.system_service import SystemService
from app.services.file_service import FileService
from app.services.report_service import ReportService
from app.api.routes.systems import get_system_service

router = APIRouter(prefix="/files", tags=["Files & Reports"])

file_service = FileService()
report_service = ReportService()


@router.post("/{system_id}/upload")
async def upload_file(
    system_id: str,
    model: str,
    record_id: int,
    file: UploadFile = File(...),
    field_name: str = "attachment",
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Upload file to external system

    Args:
        system_id: System identifier
        model: Model name
        record_id: Record ID to attach file to
        file: File to upload
        field_name: Field name for attachment

    Returns:
        Upload result

    Example:
        ```
        POST /files/odoo-prod/upload?model=res.partner&record_id=42
        Content-Type: multipart/form-data
        file: [binary data]
        ```
    """
    try:
        # Validate file
        file_service.validate_file(
            file,
            allowed_types=['image', 'document'],
            max_size_mb=10
        )

        # Get adapter
        adapter = service.adapters.get(system_id)
        if not adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"System not connected: {system_id}"
            )

        # Upload file
        result = await file_service.upload_file_to_system(
            file=file,
            adapter=adapter,
            model=model,
            record_id=record_id,
            field_name=field_name
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{system_id}/download/{attachment_id}")
async def download_file(
    system_id: str,
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Download file from external system

    Args:
        system_id: System identifier
        attachment_id: Attachment ID

    Returns:
        File content

    Example:
        ```
        GET /files/odoo-prod/download/123
        ```
    """
    try:
        # Get adapter
        adapter = service.adapters.get(system_id)
        if not adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"System not connected: {system_id}"
            )

        # Download file
        content = await file_service.download_file_from_system(
            adapter=adapter,
            model="ir.attachment",
            record_id=attachment_id,
            field_name="datas"
        )

        # Get filename
        attachments = await adapter.search_read(
            model="ir.attachment",
            domain=[["id", "=", attachment_id]],
            fields=["name", "mimetype"]
        )

        filename = attachments[0].get("name", "download") if attachments else "download"
        mimetype = attachments[0].get("mimetype", "application/octet-stream") if attachments else "application/octet-stream"

        return Response(
            content=content,
            media_type=mimetype,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"File download error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{system_id}/attachments")
async def get_attachments(
    system_id: str,
    model: str,
    record_id: int,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Get all attachments for a record

    Args:
        system_id: System identifier
        model: Model name
        record_id: Record ID

    Returns:
        List of attachments

    Example:
        ```
        GET /files/odoo-prod/attachments?model=res.partner&record_id=42
        ```
    """
    try:
        # Get adapter
        adapter = service.adapters.get(system_id)
        if not adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"System not connected: {system_id}"
            )

        # Get attachments
        attachments = await file_service.get_attachments(
            adapter=adapter,
            res_model=model,
            res_id=record_id
        )

        return {
            "success": True,
            "count": len(attachments),
            "attachments": attachments
        }

    except Exception as e:
        logger.error(f"Get attachments error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{system_id}/report/{report_type}")
async def generate_report(
    system_id: str,
    report_type: str,  # sales, inventory, partners
    format: str = "xlsx",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Generate and download report

    Args:
        system_id: System identifier
        report_type: Report type (sales, inventory, partners)
        format: Export format (xlsx, csv, pdf)
        start_date: Start date (for sales report)
        end_date: End date (for sales report)

    Returns:
        Report file

    Example:
        ```
        GET /files/odoo-prod/report/sales?format=xlsx&start_date=2024-01-01&end_date=2024-12-31
        ```
    """
    try:
        # Get adapter
        adapter = service.adapters.get(system_id)
        if not adapter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"System not connected: {system_id}"
            )

        # Generate report based on type
        if report_type == "sales":
            if not start_date or not end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date and end_date are required for sales report"
                )

            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            content = await report_service.generate_sales_report(
                adapter=adapter,
                start_date=start,
                end_date=end,
                format=format
            )
            filename = f"sales_report_{start_date}_{end_date}.{format}"

        elif report_type == "inventory":
            content = await report_service.generate_inventory_report(
                adapter=adapter,
                format=format
            )
            filename = f"inventory_report.{format}"

        elif report_type == "partners":
            content = await report_service.generate_partner_report(
                adapter=adapter,
                format=format
            )
            filename = f"partners_report.{format}"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown report type: {report_type}"
            )

        # Determine content type
        content_types = {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv",
            "pdf": "application/pdf"
        }

        return Response(
            content=content,
            media_type=content_types.get(format, "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{system_id}/export")
async def export_data(
    system_id: str,
    model: str,
    domain: List = [],
    fields: List[str] = [],
    format: str = "xlsx",
    limit: int = 1000,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Export data to Excel/CSV

    Args:
        system_id: System identifier
        model: Model name
        domain: Search filters
        fields: Fields to export
        format: Export format (xlsx, csv)
        limit: Maximum records

    Returns:
        Exported file

    Example:
        ```json
        POST /files/odoo-prod/export
        {
            "model": "res.partner",
            "domain": [["is_company", "=", true]],
            "fields": ["name", "email", "phone"],
            "format": "xlsx"
        }
        ```
    """
    try:
        # Read records
        records = await service.read_records(
            user_id=current_user.id,
            system_id=system_id,
            model=model,
            domain=domain,
            fields=fields,
            limit=limit,
            use_cache=False
        )

        # Export to format
        if format == "xlsx":
            content = await report_service.export_to_excel(records)
        elif format == "csv":
            content = await report_service.export_to_csv(records)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}"
            )

        filename = f"{model}_export.{format}"

        # Determine content type
        content_types = {
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }

        return Response(
            content=content,
            media_type=content_types.get(format, "application/octet-stream"),
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data export error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

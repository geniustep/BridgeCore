"""
File Upload/Download Service

Handle file operations with external systems
"""
from typing import Dict, Any, Optional
from fastapi import UploadFile
from loguru import logger
import base64
import httpx
from pathlib import Path


class FileService:
    """
    Service for file upload/download operations

    Features:
    - File upload to external systems
    - File download from external systems
    - Base64 encoding/decoding
    - File type validation
    """

    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Allowed file types
        self.allowed_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
            'text': ['.txt', '.csv', '.json', '.xml'],
            'archive': ['.zip', '.tar', '.gz', '.rar']
        }

    async def upload_file_to_system(
        self,
        file: UploadFile,
        adapter: Any,
        model: str,
        record_id: int,
        field_name: str = "attachment"
    ) -> Dict[str, Any]:
        """
        Upload file to external system

        Args:
            file: Uploaded file
            adapter: System adapter
            model: Model name
            record_id: Record ID to attach file to
            field_name: Field name for attachment

        Returns:
            Upload result

        Example:
            result = await file_service.upload_file_to_system(
                file=uploaded_file,
                adapter=odoo_adapter,
                model="res.partner",
                record_id=42,
                field_name="image_1920"
            )
        """
        try:
            # Read file content
            content = await file.read()

            # Encode to base64
            encoded_content = base64.b64encode(content).decode('utf-8')

            # Update record with file
            file_data = {
                field_name: encoded_content
            }

            success = await adapter.write(model, record_id, file_data)

            logger.info(f"Uploaded file {file.filename} to {model} {record_id}")

            return {
                "success": success,
                "filename": file.filename,
                "size": len(content),
                "field": field_name
            }

        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            raise

    async def download_file_from_system(
        self,
        adapter: Any,
        model: str,
        record_id: int,
        field_name: str = "datas"
    ) -> bytes:
        """
        Download file from external system

        Args:
            adapter: System adapter
            model: Model name
            record_id: Record ID
            field_name: Field name containing file

        Returns:
            File content as bytes

        Example:
            content = await file_service.download_file_from_system(
                adapter=odoo_adapter,
                model="ir.attachment",
                record_id=123,
                field_name="datas"
            )
        """
        try:
            # Read record with file field
            records = await adapter.search_read(
                model=model,
                domain=[[("id", "=", record_id)]],
                fields=[field_name, "name"]
            )

            if not records:
                raise ValueError(f"Record {record_id} not found")

            record = records[0]
            encoded_content = record.get(field_name)

            if not encoded_content:
                raise ValueError(f"No file found in field {field_name}")

            # Decode from base64
            content = base64.b64decode(encoded_content)

            logger.info(f"Downloaded file from {model} {record_id}")

            return content

        except Exception as e:
            logger.error(f"File download error: {str(e)}")
            raise

    async def create_attachment(
        self,
        file: UploadFile,
        adapter: Any,
        res_model: str,
        res_id: int,
        name: Optional[str] = None
    ) -> int:
        """
        Create attachment record in external system

        Args:
            file: Uploaded file
            adapter: System adapter
            res_model: Resource model
            res_id: Resource ID
            name: Attachment name

        Returns:
            Attachment ID

        Example:
            attachment_id = await file_service.create_attachment(
                file=uploaded_file,
                adapter=odoo_adapter,
                res_model="res.partner",
                res_id=42,
                name="Profile Picture"
            )
        """
        try:
            # Read file content
            content = await file.read()

            # Encode to base64
            encoded_content = base64.b64encode(content).decode('utf-8')

            # Create attachment
            attachment_data = {
                "name": name or file.filename,
                "datas": encoded_content,
                "res_model": res_model,
                "res_id": res_id,
                "mimetype": file.content_type
            }

            attachment_id = await adapter.create("ir.attachment", attachment_data)

            logger.info(f"Created attachment {attachment_id} for {res_model} {res_id}")

            return attachment_id

        except Exception as e:
            logger.error(f"Create attachment error: {str(e)}")
            raise

    async def get_attachments(
        self,
        adapter: Any,
        res_model: str,
        res_id: int
    ) -> list:
        """
        Get all attachments for a record

        Args:
            adapter: System adapter
            res_model: Resource model
            res_id: Resource ID

        Returns:
            List of attachments

        Example:
            attachments = await file_service.get_attachments(
                adapter=odoo_adapter,
                res_model="res.partner",
                res_id=42
            )
        """
        try:
            attachments = await adapter.search_read(
                model="ir.attachment",
                domain=[
                    ["res_model", "=", res_model],
                    ["res_id", "=", res_id]
                ],
                fields=["id", "name", "mimetype", "file_size", "create_date"]
            )

            return attachments

        except Exception as e:
            logger.error(f"Get attachments error: {str(e)}")
            raise

    def validate_file(
        self,
        file: UploadFile,
        allowed_types: list = None,
        max_size_mb: int = 10
    ) -> bool:
        """
        Validate uploaded file

        Args:
            file: Uploaded file
            allowed_types: List of allowed file types
            max_size_mb: Maximum file size in MB

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()

        if allowed_types:
            all_allowed = []
            for type_category in allowed_types:
                all_allowed.extend(self.allowed_extensions.get(type_category, []))

            if file_ext not in all_allowed:
                raise ValueError(
                    f"File type {file_ext} not allowed. "
                    f"Allowed types: {', '.join(all_allowed)}"
                )

        # Check file size
        if hasattr(file, 'size') and file.size:
            max_size_bytes = max_size_mb * 1024 * 1024
            if file.size > max_size_bytes:
                raise ValueError(
                    f"File size {file.size / (1024 * 1024):.2f}MB exceeds "
                    f"maximum allowed size {max_size_mb}MB"
                )

        return True

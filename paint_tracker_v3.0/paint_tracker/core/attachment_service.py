"""
Attachment Service
Manages PDF file uploads and storage for job attachments.

Author: Christopher Lajoie
"""

import hashlib
import shutil
from pathlib import Path
from typing import Tuple, Dict, List
from datetime import datetime
from paint_tracker.data.repository_factory import RepositoryFactory


class AttachmentService:
    """Manages PDF attachments - adding, retrieving, and deleting files."""
    
    def __init__(self, attachments_dir: Path):
        """
        Initialize the attachment service.
        
        Args:
            attachments_dir: Directory to store attachment files
        """
        self.attachments_dir = Path(attachments_dir)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.repository = RepositoryFactory.create_job_repository()
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_unique_filename(self, original_filename: str, file_hash: str) -> str:
        """
        Generate a unique filename based on hash and original extension.
        Format: hash_timestamp.ext
        """
        ext = Path(original_filename).suffix.lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{file_hash[:16]}_{timestamp}{ext}"
    
    def add_attachment(self, job_number: str, source_file_path: str, 
                      description: str = "", uploaded_by: str = "") -> Tuple[bool, str]:
        """
        Add a file attachment to a job.
        
        Args:
            job_number: Job number to attach file to
            source_file_path: Path to the source file
            description: Optional description
            uploaded_by: Username of uploader
            
        Returns:
            Tuple of (success, message)
        """
        try:
            source_path = Path(source_file_path)
            
            # Validate file exists
            if not source_path.exists():
                return False, "Source file does not exist"
            
            # Validate file type (only PDFs for now)
            if source_path.suffix.lower() != '.pdf':
                return False, "Only PDF files are supported"
            
            # Get file size
            file_size = source_path.stat().st_size
            
            # Calculate hash
            file_hash = self._get_file_hash(str(source_path))
            
            # Generate unique filename
            unique_filename = self._get_unique_filename(source_path.name, file_hash)
            
            # Destination path
            dest_path = self.attachments_dir / unique_filename
            
            # Copy file to attachments directory
            shutil.copy2(source_path, dest_path)
            
            # Add to database
            attachment_data = {
                "job_number": job_number,
                "filename": unique_filename,
                "original_filename": source_path.name,
                "file_path": str(dest_path),
                "file_size": file_size,
                "mime_type": "application/pdf",
                "description": description,
                "uploaded_by": uploaded_by
            }
            
            success, message = self.repository.add_attachment(attachment_data)
            
            if not success:
                # Clean up file if database insert failed
                if dest_path.exists():
                    dest_path.unlink()
                return False, f"Database error: {message}"
            
            return True, f"Attachment '{source_path.name}' added successfully"
            
        except Exception as e:
            return False, f"Failed to add attachment: {str(e)}"
    
    def get_attachments(self, job_number: str) -> List[Dict]:
        """
        Get all attachments for a job number.
        
        Args:
            job_number: Job number
            
        Returns:
            List of attachment dictionaries
        """
        try:
            return self.repository.get_attachments(job_number)
        except Exception as e:
            print(f"Error getting attachments: {e}")
            return []
    
    def delete_attachment(self, attachment_id: int) -> Tuple[bool, str]:
        """
        Delete an attachment.
        
        Args:
            attachment_id: ID of attachment to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Delete from database (returns file path)
            success, result = self.repository.delete_attachment(attachment_id)
            
            if not success:
                return False, result
            
            # result contains the file path
            file_path = Path(result)
            
            # Delete physical file
            if file_path.exists():
                file_path.unlink()
                return True, "Attachment deleted successfully"
            else:
                return True, "Attachment deleted from database (file already removed)"
                
        except Exception as e:
            return False, f"Failed to delete attachment: {str(e)}"
    
    def get_attachment_count(self, job_number: str) -> int:
        """Get count of attachments for a job"""
        try:
            return self.repository.get_attachment_count(job_number)
        except Exception:
            return 0


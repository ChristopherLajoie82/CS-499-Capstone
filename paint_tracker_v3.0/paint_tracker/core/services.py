import logging
from typing import Tuple, Dict, List
from datetime import datetime
from paint_tracker.data.repository_factory import RepositoryFactory
from paint_tracker.algorithms import PaintMixCalculator

logger = logging.getLogger(__name__)

class ValidationService:
    @staticmethod
    def validate_job_payload(data: Dict) -> Tuple[bool, str]:
        required = ["job_number", "manufacturer", "paint_code", "mixed_amount"]
        for k in required:
            if not str(data.get(k, "")).strip():
                return False, f"Missing field: {k}"
        # paint version should be like "2.1" format
        pv = (data.get("paint_version") or "1.0").strip()
        if not pv or not all(p.isdigit() for p in pv.split(".") if p != ""):
            return False, "Invalid paint version format"
        try:
            float(data.get("mixed_amount", 0))
        except ValueError:
            return False, "mixed_amount must be numeric"
        return True, "ok"

class ExportService:
    def __init__(self):
        self.repo = RepositoryFactory.create_job_repository()

    def export_to_csv(self, filename: str) -> bool:
        """Export all job entries (not just summaries) to CSV"""
        import csv
        try:
            all_jobs = self.repo.get_all_jobs()
            
            with open(filename, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow([
                    "Job Number", 
                    "Manufacturer", 
                    "Paint Code", 
                    "Paint Version",
                    "Color Name", 
                    "Mixed Amount (g)",
                    "Job Type",
                    "Paint (g)",
                    "Catalyst (g)",
                    "Additive (g)",
                    "Reducer (g)",
                    "Mixed By", 
                    "Notes",
                    "Date/Time"
                ])
                
                # Write each individual job entry
                for job in all_jobs:
                    job_type = job.get("job_type", "").lower()
                    third_amount = job.get("third_component_amount", "")
                    
                    # Determine if third component is additive or reducer
                    additive_amount = 0
                    reducer_amount = 0
                    
                    if third_amount:
                        if job_type == "interior":
                            additive_amount = third_amount
                        elif job_type == "exterior":
                            reducer_amount = third_amount
                    
                    w.writerow([
                        job.get("job_number", ""),
                        job.get("manufacturer", ""),
                        job.get("paint_code", ""),
                        job.get("paint_version", "1.0"),
                        job.get("color_name", ""),
                        job.get("mixed_amount", 0),
                        job.get("job_type", ""),
                        job.get("paint_amount", "") or 0,
                        job.get("catalyst_amount", "") or 0,
                        additive_amount,
                        reducer_amount,
                        job.get("mixed_by", ""),
                        job.get("notes", ""),
                        job.get("created_at", "")
                    ])
            return True
        except Exception as e:
            logger.error(f"CSV Export Error: {e}", exc_info=True)
            return False

    def export_to_json(self, filename: str) -> bool:
        """Export all job entries (not just summaries) to JSON"""
        import json
        try:
            all_jobs = self.repo.get_all_jobs()
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(all_jobs, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"JSON Export Error: {e}", exc_info=True)
            return False

MAX_BACKUPS = 10

class BackupService:
    def __init__(self, db_path: str, backup_dir):
        from pathlib import Path
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> bool:
        from datetime import datetime
        from pathlib import Path
        import shutil
        import os
        
        # Check if database file exists before trying to backup
        if not os.path.exists(self.db_path):
            logger.info(f"Database file does not exist yet, skipping backup: {self.db_path}")
            return True  # Not an error, just nothing to backup yet
        
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = self.backup_dir / f"backup_{ts}.db"
            shutil.copy2(self.db_path, dest)
            backups = sorted(self.backup_dir.glob("backup_*.db"))
            while len(backups) > MAX_BACKUPS:
                old = backups.pop(0)
                old.unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"Backup creation failed: {e}", exc_info=True)
            return False

    def list_backups(self) -> List[Dict]:
        from pathlib import Path
        files = []
        for p in sorted(self.backup_dir.glob("backup_*.db")):
            files.append({
                "filename": p.name,
                "size": p.stat().st_size,
                "created": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
        return files

    def restore_backup(self, filename: str) -> bool:
        import shutil
        try:
            src = self.backup_dir / filename
            shutil.copy2(src, self.db_path)
            return True
        except Exception as e:
            logger.error(f"Backup restore failed: {e}", exc_info=True)
            return False

class JobService:
    def __init__(self):
        self.repository = RepositoryFactory.create_job_repository()

    def get_statistics(self) -> Dict:
        return self.repository.get_statistics()

    def create_job(self, data: Dict) -> Tuple[bool, str]:
        ok, msg = ValidationService.validate_job_payload(data)
        if not ok:
            return False, msg
        return self.repository.create_job(data)

    def update_job(self, row_id: int, data: Dict) -> Tuple[bool, str]:
        ok, msg = ValidationService.validate_job_payload(data)
        if not ok:
            return False, msg
        return self.repository.update_job(row_id, data)
    
    def close(self):
        """Close the repository connection"""
        if hasattr(self.repository, 'close'):
            self.repository.close()

class PaintCalculatorService:
    """
    Service wrapper for paint mixing calculations.
    """
    
    def __init__(self):
        self.calculator = PaintMixCalculator()
    
    def calculate_mix_from_job_type(self, job_type: str, total_volume: float) -> Dict:
        """
        Calculate paint mix components based on job type and volume.
        
        Args:
            job_type: 'interior' or 'exterior'
            total_volume: Total desired volume in ml
            
        Returns:
            Dictionary with component amounts and metadata
        """
        try:
            components = self.calculator.calculate_mix(job_type, total_volume)
            ratio = self.calculator.get_ratio_display(job_type)
            
            return {
                'success': True,
                'components': components,
                'ratio': ratio,
                'total_volume': total_volume,
                'job_type': job_type
            }
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ratio_info(self, job_type: str) -> Dict:
        """Get ratio information for display purposes."""
        try:
            ratio_display = self.calculator.get_ratio_display(job_type)
            component_names = self.calculator.get_component_names(job_type)
            
            return {
                'success': True,
                'ratio': ratio_display,
                'components': component_names
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


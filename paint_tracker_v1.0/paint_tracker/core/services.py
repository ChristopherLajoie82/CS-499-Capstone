from typing import Tuple, Dict, List, Optional
from paint_tracker.data import JobRepository

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
    def __init__(self, db_path: str):
        self.repo = JobRepository(db_path)

    def export_to_csv(self, filename: str) -> bool:
        import csv
        summaries = self.repo.get_job_summaries()
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["Job Number", "Entry Count", "Total Amount", "Colors", "First Mix", "Last Mix"])
                for s in summaries:
                    w.writerow([
                        s["job_number"], s["entry_count"], s["total_amount"],
                        ", ".join(s["colors"]), s["first_mixed"], s["last_mixed"]
                    ])
            return True
        except Exception:
            return False

    def export_to_json(self, filename: str) -> bool:
        import json
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.repo.get_job_summaries(), f, indent=2)
            return True
        except Exception:
            return False

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
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = self.backup_dir / f"backup_{ts}.db"
            shutil.copy2(self.db_path, dest)
            # keep only last 10 backups so we don't fill up the disk
            backups = sorted(self.backup_dir.glob("backup_*.db"))
            while len(backups) > 10:
                old = backups.pop(0)
                old.unlink(missing_ok=True)
            return True
        except Exception:
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
        except Exception:
            return False

class AuthenticationService:
    # TODO: implement real password hashing later
    _hash = None

    @classmethod
    def verify_admin_password(cls, password: str) -> bool:
        # for demo - accepts empty or "admin"
        return password in ("", "admin")

    @classmethod
    def change_admin_password(cls, old_pwd: str, new_pwd: str) -> bool:
        # stub - always returns true for now
        return True

class JobService:
    def __init__(self, db_path: str):
        self.repository = JobRepository(db_path)

    # wrapper methods for UI layer
    def get_statistics(self) -> Dict:
        return self.repository.get_statistics()

    def search_jobs(self, term: str, filter_type: str) -> List[Dict]:
        recent_only = (filter_type == "recent")
        return self.repository.search_jobs(term, recent_only)

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

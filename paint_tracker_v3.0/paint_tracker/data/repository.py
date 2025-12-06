import sqlite3
from typing import List, Dict, Tuple
from datetime import datetime

class JobRepository:
    """
    SQLite repository. Each row represents one paint mix event for a job number.
    Table name remains 'jobs' for compatibility with your earlier code.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self.ensure_schema()

    def ensure_schema(self) -> None:
        cur = self._conn.cursor()
        # Enable foreign keys
        cur.execute("PRAGMA foreign_keys = ON")
        
        # base table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            job_number TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            paint_code TEXT NOT NULL,
            paint_version TEXT DEFAULT '1.0',
            color_name TEXT,
            mixed_amount REAL NOT NULL,
            mixed_by TEXT,
            notes TEXT,
            created_at TEXT,   -- ISO date time string
            updated_at TEXT,
            job_type TEXT,     -- 'interior' or 'exterior'
            paint_amount REAL,     -- calculated paint component amount
            catalyst_amount REAL,  -- calculated catalyst amount
            third_component_amount REAL,  -- additive (interior) or reducer (exterior)
            third_component_name TEXT,    -- name of third component
            user_id INTEGER,              -- Foreign key to users table
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        # add any missing columns
        self._add_column_if_missing(cur, "jobs", "paint_version", "TEXT", "'1.0'")
        self._add_column_if_missing(cur, "jobs", "mixed_by", "TEXT", "NULL")
        self._add_column_if_missing(cur, "jobs", "notes", "TEXT", "NULL")
        self._add_column_if_missing(cur, "jobs", "updated_at", "TEXT", "NULL")
        # algorithm-related columns for mix calculations
        self._add_column_if_missing(cur, "jobs", "job_type", "TEXT", "NULL")
        self._add_column_if_missing(cur, "jobs", "paint_amount", "REAL", "NULL")
        self._add_column_if_missing(cur, "jobs", "catalyst_amount", "REAL", "NULL")
        self._add_column_if_missing(cur, "jobs", "third_component_amount", "REAL", "NULL")
        self._add_column_if_missing(cur, "jobs", "third_component_name", "TEXT", "NULL")
        # User tracking columns
        self._add_column_if_missing(cur, "jobs", "user_id", "INTEGER", "NULL")
        
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_job_number 
        ON jobs(job_number)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_user_id 
        ON jobs(user_id)
        """)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_created_at 
        ON jobs(created_at)
        """)
        
        # Attachments table for PDF files
        cur.execute("""
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_number TEXT NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT DEFAULT 'application/pdf',
            description TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT NOT NULL
        )
        """)
        
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_attachments_job_number 
        ON attachments(job_number)
        """)
        
        self._conn.commit()

    def _add_column_if_missing(self, cur, table: str, col: str, coltype: str, default_sql: str) -> None:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r["name"] for r in cur.fetchall()]
        if col not in cols:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype} DEFAULT {default_sql}")

    # CRUD

    def create_job(self, data: Dict) -> Tuple[bool, str]:
        now = datetime.now().isoformat(timespec="seconds")
        try:
            self._conn.execute("""
                INSERT INTO jobs
                (job_number, manufacturer, paint_code, paint_version,
                 color_name, mixed_amount, mixed_by, notes, created_at, updated_at,
                 job_type, paint_amount, catalyst_amount, third_component_amount, 
                 third_component_name, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("job_number", "").strip(),
                data.get("manufacturer", "").strip(),
                data.get("paint_code", "").strip(),
                (data.get("paint_version") or "1.0").strip(),
                (data.get("color_name") or "").strip(),
                float(data.get("mixed_amount", 0) or 0),
                (data.get("mixed_by") or "").strip(),
                (data.get("notes") or "").strip(),
                now,
                now,
                data.get("job_type"),  # 'interior' or 'exterior'
                data.get("paint_amount"),
                data.get("catalyst_amount"),
                data.get("third_component_amount"),
                data.get("third_component_name"),
                data.get("user_id")  # FK to users table
            ))
            self._conn.commit()
            return True, "Job entry created"
        except Exception as e:
            return False, f"Create failed: {e}"

    def update_job(self, row_id: int, data: Dict) -> Tuple[bool, str]:
        now = datetime.now().isoformat(timespec="seconds")
        try:
            self._conn.execute("""
                UPDATE jobs
                SET job_number = ?, manufacturer = ?, paint_code = ?, paint_version = ?,
                    color_name = ?, mixed_amount = ?, mixed_by = ?, notes = ?, updated_at = ?,
                    job_type = ?, paint_amount = ?, catalyst_amount = ?, 
                    third_component_amount = ?, third_component_name = ?, user_id = ?
                WHERE id = ?
            """, (
                data.get("job_number", "").strip(),
                data.get("manufacturer", "").strip(),
                data.get("paint_code", "").strip(),
                (data.get("paint_version") or "1.0").strip(),
                (data.get("color_name") or "").strip(),
                float(data.get("mixed_amount", 0) or 0),
                (data.get("mixed_by") or "").strip(),
                (data.get("notes") or "").strip(),
                now,
                data.get("job_type"),
                data.get("paint_amount"),
                data.get("catalyst_amount"),
                data.get("third_component_amount"),
                data.get("third_component_name"),
                data.get("user_id"),
                int(row_id)
            ))
            self._conn.commit()
            return True, "Job entry updated"
        except Exception as e:
            return False, f"Update failed: {e}"

    # Queries for UI

    def get_job_summaries(self) -> List[Dict]:
        """
        One row per job_number with totals and dates.
        Returns most recent mixed_by, job_type, paint_code, and color_name for each job.
        """
        cur = self._conn.cursor()
        cur.execute("""
            SELECT
                job_number,
                COUNT(*) AS entry_count,
                IFNULL(SUM(mixed_amount), 0) AS total_amount,
                MAX(created_at) AS last_mixed,
                (SELECT mixed_by FROM jobs j2 
                 WHERE j2.job_number = jobs.job_number 
                 ORDER BY datetime(j2.created_at) DESC LIMIT 1) AS last_mixed_by,
                (SELECT job_type FROM jobs j3
                 WHERE j3.job_number = jobs.job_number
                 ORDER BY datetime(j3.created_at) DESC LIMIT 1) AS last_job_type,
                (SELECT paint_code FROM jobs j4
                 WHERE j4.job_number = jobs.job_number
                 ORDER BY datetime(j4.created_at) DESC LIMIT 1) AS last_paint_code,
                (SELECT color_name FROM jobs j5
                 WHERE j5.job_number = jobs.job_number
                 ORDER BY datetime(j5.created_at) DESC LIMIT 1) AS last_color_name
            FROM jobs
            GROUP BY job_number
            ORDER BY job_number COLLATE NOCASE
        """)
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "job_number": r["job_number"],
                "entry_count": r["entry_count"],
                "total_amount": round(r["total_amount"] or 0, 2),
                "last_mixed": r["last_mixed"] or "",
                "mixed_by": r["last_mixed_by"] or "Unknown",
                "job_type": r["last_job_type"] or "",
                "paint_code": r["last_paint_code"] or "",
                "color_name": r["last_color_name"] or ""
            })
        return out

    def get_job_details(self, job_number: str) -> Dict:
        """Full history for the detail dialog."""
        cur = self._conn.cursor()
        cur.execute("""
            SELECT id, job_number, manufacturer, paint_code, paint_version,
                   color_name, mixed_amount, mixed_by, notes, created_at, job_type
            FROM jobs
            WHERE job_number = ?
            ORDER BY datetime(created_at) ASC, id ASC
        """, (job_number,))
        history = [dict(r) for r in cur.fetchall()]

        # compute summary
        total_amount = round(sum(float(h.get("mixed_amount") or 0) for h in history), 2)
        colors = []
        seen = set()
        for h in history:
            name = (h.get("color_name") or "").strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                colors.append(name)

        date_first = history[0]["created_at"] if history else ""
        date_last = history[-1]["created_at"] if history else ""
        return {
            "job_number": job_number,
            "total_colors": len(colors),
            "total_amount": total_amount,
            "date_range": {"first": date_first, "last": date_last},
            "history": history
        }

    def get_all_jobs(self) -> List[Dict]:
        """Get all individual job entries with full details including component breakdowns"""
        cur = self._conn.cursor()
        cur.execute("""
            SELECT id, job_number, manufacturer, paint_code, paint_version,
                   color_name, mixed_amount, mixed_by, notes, created_at, updated_at,
                   job_type, paint_amount, catalyst_amount, 
                   third_component_amount, third_component_name
            FROM jobs
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        
        jobs = []
        for r in rows:
            jobs.append({
                'id': r['id'],
                'job_number': r['job_number'],
                'manufacturer': r['manufacturer'],
                'paint_code': r['paint_code'],
                'paint_version': r['paint_version'] or '1.0',
                'color_name': r['color_name'] or '',
                'mixed_amount': r['mixed_amount'] or 0,
                'mixed_by': r['mixed_by'] or '',
                'notes': r['notes'] or '',
                'created_at': r['created_at'] or '',
                'updated_at': r['updated_at'] or '',
                'job_type': r['job_type'] or '',
                'paint_amount': r['paint_amount'] or '',
                'catalyst_amount': r['catalyst_amount'] or '',
                'third_component_amount': r['third_component_amount'] or '',
                'third_component_name': r['third_component_name'] or ''
            })
        return jobs
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job entry by ID"""
        try:
            self._conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            self._conn.commit()
            return True
        except Exception:
            return False
    
    def delete_job_by_number(self, job_number: str) -> bool:
        """Delete all entries for a job number"""
        try:
            self._conn.execute("DELETE FROM jobs WHERE job_number = ?", (job_number,))
            self._conn.commit()
            return True
        except Exception:
            return False

    def get_statistics(self) -> Dict:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT job_number) AS total_jobs FROM jobs")
        total_jobs = cur.fetchone()["total_jobs"] or 0

        cur.execute("""
            SELECT COUNT(DISTINCT job_number) AS recent_jobs
            FROM jobs
            WHERE datetime(created_at) >= datetime('now','-30 days')
        """)
        recent_jobs = cur.fetchone()["recent_jobs"] or 0

        cur.execute("SELECT IFNULL(SUM(mixed_amount),0) AS total_paint FROM jobs")
        total_paint = round(cur.fetchone()["total_paint"] or 0, 2)

        avg = round(total_paint / max(total_jobs, 1), 2)
        return {
            "total_jobs": total_jobs,
            "recent_jobs": recent_jobs,
            "total_paint": total_paint,
            "average_paint_per_job": avg
        }
    
    def close(self):
        """Close the database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    # Attachment Methods
    
    def add_attachment(self, data: Dict) -> Tuple[bool, str]:
        """Add a file attachment to a job"""
        now = datetime.now().isoformat(timespec="seconds")
        try:
            self._conn.execute("""
                INSERT INTO attachments
                (job_number, filename, original_filename, file_path, file_size, 
                 mime_type, description, uploaded_by, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("job_number", "").strip(),
                data.get("filename", "").strip(),
                data.get("original_filename", "").strip(),
                data.get("file_path", "").strip(),
                data.get("file_size", 0),
                data.get("mime_type", "application/pdf"),
                data.get("description", "").strip(),
                data.get("uploaded_by", "").strip(),
                now
            ))
            self._conn.commit()
            return True, "Attachment added successfully"
        except Exception as e:
            return False, f"Failed to add attachment: {e}"
    
    def get_attachments(self, job_number: str) -> List[Dict]:
        """Get all attachments for a job number"""
        cur = self._conn.cursor()
        cur.execute("""
            SELECT id, job_number, filename, original_filename, file_path, 
                   file_size, mime_type, description, uploaded_by, uploaded_at
            FROM attachments
            WHERE job_number = ?
            ORDER BY uploaded_at DESC
        """, (job_number,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    
    def delete_attachment(self, attachment_id: int) -> Tuple[bool, str]:
        """Delete an attachment by ID"""
        try:
            # Get file path before deleting
            cur = self._conn.cursor()
            cur.execute("SELECT file_path FROM attachments WHERE id = ?", (attachment_id,))
            row = cur.fetchone()
            if not row:
                return False, "Attachment not found"
            
            file_path = row["file_path"]
            
            # Delete from database
            self._conn.execute("DELETE FROM attachments WHERE id = ?", (attachment_id,))
            self._conn.commit()
            
            return True, file_path  # Return file path so caller can delete the file
        except Exception as e:
            return False, f"Failed to delete attachment: {e}"
    
    def get_attachment_count(self, job_number: str) -> int:
        """Get count of attachments for a job number"""
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM attachments WHERE job_number = ?", (job_number,))
        return cur.fetchone()["count"] or 0


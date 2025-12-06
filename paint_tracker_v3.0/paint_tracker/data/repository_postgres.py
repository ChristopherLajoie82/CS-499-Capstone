"""
PostgreSQL Repository - Data Access Layer for Job Tracking
Replaces SQLite with PostgreSQL for multi-user support and network access.

Author: Christopher Lajoie
CS 499 Enhancement Three: Database Enhancement
"""

import psycopg2
import psycopg2.extras
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class JobRepository:
    """
    PostgreSQL repository for paint job tracking.
    Each row represents one paint mix event for a job number.
    """

    def __init__(self, connection_params: Dict[str, str]):
        """
        Initialize PostgreSQL connection.
        
        Args:
            connection_params: Dict with keys: host, port, database, user, password
        """
        self.connection_params = connection_params
        self._conn = None
        self._connect()
        self.ensure_schema()

    def _connect(self):
        """Establish database connection with connection pooling support"""
        try:
            self._conn = psycopg2.connect(
                host=self.connection_params.get('host', 'localhost'),
                port=self.connection_params.get('port', 5432),
                database=self.connection_params['database'],
                user=self.connection_params['user'],
                password=self.connection_params['password'],
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            self._conn.autocommit = False
        except psycopg2.Error as e:
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def ensure_schema(self) -> None:
        """Create tables and indexes if they don't exist"""
        try:
            with self._conn.cursor() as cur:
                # Create jobs table
                cur.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id SERIAL PRIMARY KEY,
                    job_number TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    paint_code TEXT NOT NULL,
                    paint_version TEXT DEFAULT '1.0',
                    color_name TEXT,
                    mixed_amount NUMERIC(10, 2) NOT NULL,
                    mixed_by TEXT,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    job_type TEXT CHECK (job_type IN ('interior', 'exterior')),
                    paint_amount NUMERIC(10, 2),
                    catalyst_amount NUMERIC(10, 2),
                    third_component_amount NUMERIC(10, 2),
                    third_component_name TEXT,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
                )
                """)
                
                # Create indexes
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
                    id SERIAL PRIMARY KEY,
                    job_number TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT DEFAULT 'application/pdf',
                    description TEXT,
                    uploaded_by TEXT,
                    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_attachments_job_number 
                ON attachments(job_number)
                """)
                
                self._conn.commit()
        except psycopg2.Error as e:
            self._conn.rollback()
            raise Exception(f"Schema creation failed: {e}")

    # CRUD Operations

    def create_job(self, data: Dict) -> Tuple[bool, str]:
        """Create a new job entry"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO jobs
                    (job_number, manufacturer, paint_code, paint_version,
                     color_name, mixed_amount, mixed_by, notes, created_at, updated_at,
                     job_type, paint_amount, catalyst_amount, third_component_amount, 
                     third_component_name, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data.get("job_number", "").strip(),
                    data.get("manufacturer", "").strip(),
                    data.get("paint_code", "").strip(),
                    (data.get("paint_version") or "1.0").strip(),
                    (data.get("color_name") or "").strip(),
                    float(data.get("mixed_amount", 0) or 0),
                    (data.get("mixed_by") or "").strip(),
                    (data.get("notes") or "").strip(),
                    datetime.now(),
                    datetime.now(),
                    data.get("job_type"),
                    data.get("paint_amount"),
                    data.get("catalyst_amount"),
                    data.get("third_component_amount"),
                    data.get("third_component_name"),
                    data.get("user_id")
                ))
                self._conn.commit()
                return True, "Job entry created"
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Create failed: {e}"

    def update_job(self, row_id: int, data: Dict) -> Tuple[bool, str]:
        """Update an existing job entry"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    UPDATE jobs
                    SET job_number = %s, manufacturer = %s, paint_code = %s, paint_version = %s,
                        color_name = %s, mixed_amount = %s, mixed_by = %s, notes = %s, updated_at = %s,
                        job_type = %s, paint_amount = %s, catalyst_amount = %s, 
                        third_component_amount = %s, third_component_name = %s, user_id = %s
                    WHERE id = %s
                """, (
                    data.get("job_number", "").strip(),
                    data.get("manufacturer", "").strip(),
                    data.get("paint_code", "").strip(),
                    (data.get("paint_version") or "1.0").strip(),
                    (data.get("color_name") or "").strip(),
                    float(data.get("mixed_amount", 0) or 0),
                    (data.get("mixed_by") or "").strip(),
                    (data.get("notes") or "").strip(),
                    datetime.now(),
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
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Update failed: {e}"

    # Query Methods for UI

    def get_job_summaries(self) -> List[Dict]:
        """
        One row per job_number with totals and dates.
        Returns most recent mixed_by, job_type, paint_code, and color_name for each job.
        """
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        job_number,
                        COUNT(*) AS entry_count,
                        COALESCE(SUM(mixed_amount), 0) AS total_amount,
                        MAX(created_at) AS last_mixed,
                        (SELECT mixed_by FROM jobs j2 
                         WHERE j2.job_number = jobs.job_number 
                         ORDER BY j2.created_at DESC LIMIT 1) AS last_mixed_by,
                        (SELECT job_type FROM jobs j3
                         WHERE j3.job_number = jobs.job_number
                         ORDER BY j3.created_at DESC LIMIT 1) AS last_job_type,
                        (SELECT paint_code FROM jobs j4
                         WHERE j4.job_number = jobs.job_number
                         ORDER BY j4.created_at DESC LIMIT 1) AS last_paint_code,
                        (SELECT color_name FROM jobs j5
                         WHERE j5.job_number = jobs.job_number
                         ORDER BY j5.created_at DESC LIMIT 1) AS last_color_name
                    FROM jobs
                    GROUP BY job_number
                    ORDER BY job_number
                """)
                rows = cur.fetchall()
                
                out = []
                for r in rows:
                    out.append({
                        "job_number": r["job_number"],
                        "entry_count": r["entry_count"],
                        "total_amount": round(float(r["total_amount"] or 0), 2),
                        "last_mixed": r["last_mixed"].isoformat() if r["last_mixed"] else "",
                        "mixed_by": r["last_mixed_by"] or "Unknown",
                        "job_type": r["last_job_type"] or "",
                        "paint_code": r["last_paint_code"] or "",
                        "color_name": r["last_color_name"] or ""
                    })
                return out
        except psycopg2.Error as e:
            raise Exception(f"Failed to get job summaries: {e}")

    def get_job_details(self, job_number: str) -> Dict:
        """Full history for the detail dialog"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT id, job_number, manufacturer, paint_code, paint_version,
                           color_name, mixed_amount, mixed_by, notes, created_at, job_type
                    FROM jobs
                    WHERE job_number = %s
                    ORDER BY created_at ASC, id ASC
                """, (job_number,))
                history = [dict(r) for r in cur.fetchall()]

                # Convert timestamps to ISO strings
                for h in history:
                    if h.get("created_at"):
                        h["created_at"] = h["created_at"].isoformat()

                # Compute summary
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
        except psycopg2.Error as e:
            raise Exception(f"Failed to get job details: {e}")

    def get_all_jobs(self) -> List[Dict]:
        """Get all individual job entries with full details including component breakdowns"""
        try:
            with self._conn.cursor() as cur:
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
                        'mixed_amount': float(r['mixed_amount'] or 0),
                        'mixed_by': r['mixed_by'] or '',
                        'notes': r['notes'] or '',
                        'created_at': r['created_at'].isoformat() if r['created_at'] else '',
                        'updated_at': r['updated_at'].isoformat() if r['updated_at'] else '',
                        'job_type': r['job_type'] or '',
                        'paint_amount': float(r['paint_amount']) if r['paint_amount'] else '',
                        'catalyst_amount': float(r['catalyst_amount']) if r['catalyst_amount'] else '',
                        'third_component_amount': float(r['third_component_amount']) if r['third_component_amount'] else '',
                        'third_component_name': r['third_component_name'] or ''
                    })
                return jobs
        except psycopg2.Error as e:
            raise Exception(f"Failed to get all jobs: {e}")
    
    def delete_job(self, job_id: int) -> bool:
        """Delete a job entry by ID"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
                self._conn.commit()
                return True
        except psycopg2.Error:
            self._conn.rollback()
            return False
    
    def delete_job_by_number(self, job_number: str) -> bool:
        """Delete all entries for a job number"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("DELETE FROM jobs WHERE job_number = %s", (job_number,))
                self._conn.commit()
                return True
        except psycopg2.Error:
            self._conn.rollback()
            return False

    def get_statistics(self) -> Dict:
        """Get statistics for dashboard"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT COUNT(DISTINCT job_number) AS total_jobs FROM jobs")
                total_jobs = cur.fetchone()["total_jobs"] or 0

                cur.execute("""
                    SELECT COUNT(DISTINCT job_number) AS recent_jobs
                    FROM jobs
                    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                """)
                recent_jobs = cur.fetchone()["recent_jobs"] or 0

                cur.execute("SELECT COALESCE(SUM(mixed_amount), 0) AS total_paint FROM jobs")
                total_paint = round(float(cur.fetchone()["total_paint"] or 0), 2)

                avg = round(total_paint / max(total_jobs, 1), 2)
                
                return {
                    "total_jobs": total_jobs,
                    "recent_jobs": recent_jobs,
                    "total_paint": total_paint,
                    "average_paint_per_job": avg
                }
        except psycopg2.Error as e:
            raise Exception(f"Failed to get statistics: {e}")
    
    def close(self):
        """Close the database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    # Attachment Methods
    
    def add_attachment(self, data: Dict) -> Tuple[bool, str]:
        """Add a file attachment to a job"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO attachments
                    (job_number, filename, original_filename, file_path, file_size, 
                     mime_type, description, uploaded_by, uploaded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data.get("job_number", "").strip(),
                    data.get("filename", "").strip(),
                    data.get("original_filename", "").strip(),
                    data.get("file_path", "").strip(),
                    data.get("file_size", 0),
                    data.get("mime_type", "application/pdf"),
                    data.get("description", "").strip(),
                    data.get("uploaded_by", "").strip(),
                    datetime.now()
                ))
                self._conn.commit()
                return True, "Attachment added successfully"
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Failed to add attachment: {e}"
    
    def get_attachments(self, job_number: str) -> List[Dict]:
        """Get all attachments for a job number"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("""
                    SELECT id, job_number, filename, original_filename, file_path, 
                           file_size, mime_type, description, uploaded_by, uploaded_at
                    FROM attachments
                    WHERE job_number = %s
                    ORDER BY uploaded_at DESC
                """, (job_number,))
                rows = cur.fetchall()
                
                # Convert timestamps to ISO strings
                attachments = []
                for r in rows:
                    attachment = dict(r)
                    if attachment.get("uploaded_at"):
                        attachment["uploaded_at"] = attachment["uploaded_at"].isoformat()
                    attachments.append(attachment)
                return attachments
        except psycopg2.Error as e:
            raise Exception(f"Failed to get attachments: {e}")
    
    def delete_attachment(self, attachment_id: int) -> Tuple[bool, str]:
        """Delete an attachment by ID"""
        try:
            with self._conn.cursor() as cur:
                # Get file path before deleting
                cur.execute("SELECT file_path FROM attachments WHERE id = %s", (attachment_id,))
                row = cur.fetchone()
                if not row:
                    return False, "Attachment not found"
                
                file_path = row["file_path"]
                
                # Delete from database
                cur.execute("DELETE FROM attachments WHERE id = %s", (attachment_id,))
                self._conn.commit()
                
                return True, file_path  # Return file path so caller can delete the file
        except psycopg2.Error as e:
            self._conn.rollback()
            return False, f"Failed to delete attachment: {e}"
    
    def get_attachment_count(self, job_number: str) -> int:
        """Get count of attachments for a job number"""
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM attachments WHERE job_number = %s", (job_number,))
                return cur.fetchone()["count"] or 0
        except psycopg2.Error:
            return 0


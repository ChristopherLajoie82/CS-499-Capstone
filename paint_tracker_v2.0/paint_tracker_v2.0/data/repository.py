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
            third_component_name TEXT     -- name of third component
        )
        """)
        # add any missing columns
        self._add_column_if_missing(cur, "jobs", "paint_version", "TEXT", "'1.0'")
        self._add_column_if_missing(cur, "jobs", "mixed_by", "TEXT", "NULL")
        self._add_column_if_missing(cur, "jobs", "notes", "TEXT", "NULL")
        self._add_column_if_missing(cur, "jobs", "updated_at", "TEXT", "NULL")

        # columns for mix calculations
        self._add_column_if_missing(cur, "jobs", "job_type", "TEXT", "NULL")
        self._add_column_if_missing(cur, "jobs", "paint_amount", "REAL", "NULL")
        self._add_column_if_missing(cur, "jobs", "catalyst_amount", "REAL", "NULL")
        self._add_column_if_missing(cur, "jobs", "third_component_amount", "REAL", "NULL")
        self._add_column_if_missing(cur, "jobs", "third_component_name", "TEXT", "NULL")
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
                 job_type, paint_amount, catalyst_amount, third_component_amount, third_component_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                data.get("third_component_name")
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
                    third_component_amount = ?, third_component_name = ?
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
        Returns most recent mixed_by and job_type for each job.
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
                 ORDER BY datetime(j3.created_at) DESC LIMIT 1) AS last_job_type
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
                "job_type": r["last_job_type"] or ""
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

    def search_jobs(self, term: str, recent_only: bool = False) -> List[Dict]:
        """Return raw rows matching the term. UI will place them in a table if needed."""
        like = f"%{term.strip()}%"
        params = [like, like, like]
        sql = """
            SELECT id, job_number, manufacturer, paint_code, paint_version,
                   color_name, mixed_amount, mixed_by, notes, created_at
            FROM jobs
            WHERE job_number LIKE ? OR color_name LIKE ? OR paint_code LIKE ?
        """
        if recent_only:
            sql += " AND datetime(created_at) >= datetime('now','-30 days')"
        sql += " ORDER BY job_number COLLATE NOCASE, datetime(created_at) DESC"
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

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

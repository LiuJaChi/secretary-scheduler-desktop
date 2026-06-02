from pathlib import Path
from datetime import datetime
import sqlite3
import sys

from database import get_connection


def get_bundle_base_dir():
    """
    取得 bundled 資源目錄：
    - 原始碼執行時：目前檔案所在目錄
    - PyInstaller one-file/one-dir：bundle 展開目錄
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


MIGRATIONS_DIR = get_bundle_base_dir() / "migrations"


def ensure_schema_migrations_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()


def get_applied_versions(conn):
    cur = conn.cursor()
    cur.execute("SELECT version FROM schema_migrations ORDER BY version ASC")
    rows = cur.fetchall()
    return {row["version"] for row in rows}


def get_migration_files():
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted([p for p in MIGRATIONS_DIR.glob("*.sql") if p.is_file()])


def apply_migration(conn, migration_path: Path):
    sql_text = migration_path.read_text(encoding="utf-8").strip()
    if not sql_text:
        return

    cur = conn.cursor()
    cur.executescript("BEGIN;\n" + sql_text + "\nCOMMIT;")

    cur.execute("""
        INSERT INTO schema_migrations (version, applied_at)
        VALUES (?, ?)
    """, (
        migration_path.name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()


def _fetch_duplicate_groups(conn, sql, formatter):
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    return [formatter(row) for row in rows]


def diagnose_duplicate_data(conn):
    diagnostics = []

    holiday_duplicates = _fetch_duplicate_groups(
        conn,
        """
        SELECT date, COUNT(*) AS cnt
        FROM holidays
        GROUP BY date
        HAVING COUNT(*) > 1
        ORDER BY date
        """,
        lambda row: f"- holidays：日期 {row['date']} 重複 {row['cnt']} 筆"
    )
    if holiday_duplicates:
        diagnostics.append("國定假日重複：")
        diagnostics.extend(holiday_duplicates)

    leave_duplicates = _fetch_duplicate_groups(
        conn,
        """
        SELECT secretary_id, leave_date, COUNT(*) AS cnt
        FROM leave_requests
        GROUP BY secretary_id, leave_date
        HAVING COUNT(*) > 1
        ORDER BY secretary_id, leave_date
        """,
        lambda row: f"- leave_requests：secretary_id={row['secretary_id']}，日期 {row['leave_date']} 重複 {row['cnt']} 筆"
    )
    if leave_duplicates:
        diagnostics.append("請假申請重複：")
        diagnostics.extend(leave_duplicates)

    schedule_duplicates = _fetch_duplicate_groups(
        conn,
        """
        SELECT secretary_id, work_date, COUNT(*) AS cnt
        FROM schedules
        GROUP BY secretary_id, work_date
        HAVING COUNT(*) > 1
        ORDER BY secretary_id, work_date
        """,
        lambda row: f"- schedules：secretary_id={row['secretary_id']}，日期 {row['work_date']} 重複 {row['cnt']} 筆"
    )
    if schedule_duplicates:
        diagnostics.append("班表重複：")
        diagnostics.extend(schedule_duplicates)

    comp_duplicates = _fetch_duplicate_groups(
        conn,
        """
        SELECT secretary_id, use_date, COUNT(*) AS cnt
        FROM comp_leave_records
        WHERE status = 'used' AND use_date IS NOT NULL
        GROUP BY secretary_id, use_date
        HAVING COUNT(*) > 1
        ORDER BY secretary_id, use_date
        """,
        lambda row: f"- comp_leave_records：secretary_id={row['secretary_id']}，use_date {row['use_date']} 重複 {row['cnt']} 筆"
    )
    if comp_duplicates:
        diagnostics.append("補休使用紀錄重複：")
        diagnostics.extend(comp_duplicates)

    return diagnostics


def build_migration_error_message(base_error, diagnostics):
    lines = [
        "資料庫 Migration 失敗。",
        f"原因：{base_error}",
    ]

    if diagnostics:
        lines.append("")
        lines.append("偵測到可能造成唯一索引建立失敗的重複資料：")
        lines.extend(diagnostics)
        lines.append("")
        lines.append("可開啟「重複資料清理工具」進行清理。")
    else:
        lines.append("")
        lines.append("未偵測到常見重複資料，請檢查 migration SQL 或資料表結構。")
        lines.append(f"目前 migration 目錄：{MIGRATIONS_DIR}")

    return "\n".join(lines)


def run_migrations():
    conn = get_connection()
    try:
        ensure_schema_migrations_table(conn)
        applied_versions = get_applied_versions(conn)
        migration_files = get_migration_files()

        applied_now = []

        for migration_path in migration_files:
            if migration_path.name in applied_versions:
                continue

            apply_migration(conn, migration_path)
            applied_now.append(migration_path.name)

        return {
            "ok": True,
            "applied": applied_now,
            "message": ""
        }

    except sqlite3.IntegrityError as e:
        conn.rollback()
        diagnostics = diagnose_duplicate_data(conn)
        return {
            "ok": False,
            "applied": [],
            "message": build_migration_error_message(str(e), diagnostics),
            "has_duplicates": bool(diagnostics)
        }

    except Exception as e:
        conn.rollback()
        diagnostics = diagnose_duplicate_data(conn)
        return {
            "ok": False,
            "applied": [],
            "message": build_migration_error_message(str(e), diagnostics),
            "has_duplicates": bool(diagnostics)
        }

    finally:
        conn.close()
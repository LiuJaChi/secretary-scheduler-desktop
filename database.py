import sqlite3
import sys
from pathlib import Path


def get_app_dir():
    """
    取得應用程式資料目錄：
    - 原始碼執行時：目前檔案所在目錄
    - PyInstaller 打包後：exe 所在目錄
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = get_app_dir()
DB_PATH = BASE_DIR / "scheduler.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS secretaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            name TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secretary_id INTEGER NOT NULL,
            work_date TEXT NOT NULL,
            shift_type TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            is_holiday_shift INTEGER NOT NULL DEFAULT 0,
            source_type TEXT,
            remark TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secretary_id INTEGER NOT NULL,
            leave_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS comp_leave_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secretary_id INTEGER NOT NULL,
            use_date TEXT,
            status TEXT NOT NULL,
            note TEXT
        )
    """)

    conn.commit()
    conn.close()
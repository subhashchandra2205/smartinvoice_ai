import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "invoice_history.db"

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            filename TEXT,
            file_hash TEXT,
            vendor_name TEXT,
            invoice_number TEXT,
            invoice_date TEXT,
            po_number TEXT,
            total_amount REAL,
            status TEXT,
            extraction_method TEXT,
            confidence REAL,
            result_json TEXT
        )
        """)

def save_run(filename, file_hash, invoice, result):
    with connect() as conn:
        conn.execute("""
        INSERT INTO runs
        (filename,file_hash,vendor_name,invoice_number,invoice_date,po_number,total_amount,status,extraction_method,confidence,result_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            filename, file_hash, invoice.get("vendor_name"), invoice.get("invoice_number"),
            invoice.get("invoice_date"), invoice.get("po_number"), invoice.get("total_amount"),
            result.get("status"), invoice.get("extraction_method"), invoice.get("confidence"),
            json.dumps(result, default=str)
        ))

def get_runs():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY id DESC").fetchall()
        return [dict(row) for row in rows]

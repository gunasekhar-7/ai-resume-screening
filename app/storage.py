import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = "resume_screening.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screening_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screening_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            score REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES screening_sessions(id)
        )
    ''')
    # Add indexes for speed on large datasets
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_session ON screening_results (session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON screening_sessions (timestamp)')
    conn.commit()
    conn.close()

def save_results(ranked_resumes: List[Dict[str, Any]], job_title: str) -> Optional[int]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('INSERT INTO screening_sessions (job_title, timestamp) VALUES (?, ?)', (job_title, timestamp))
        session_id = cursor.lastrowid
        resume_data = [(session_id, e.get("filename", "Unknown"), e.get("score", 0.0)) for e in ranked_resumes]
        cursor.executemany('INSERT INTO screening_results (session_id, filename, score) VALUES (?, ?, ?)', resume_data)
        conn.commit()
        return session_id
    except sqlite3.Error:
        conn.rollback()
        return None
    finally:
        conn.close()

def fetch_results(limit: int = 100) -> List[Dict[str, Any]]:
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT ss.id AS session_id, ss.job_title, ss.timestamp, sr.filename, sr.score
            FROM screening_results sr JOIN screening_sessions ss ON sr.session_id = ss.id
            ORDER BY ss.timestamp DESC, sr.score DESC LIMIT ?
        ''', (limit,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        conn.close()

def fetch_session_results(session_id: int) -> List[Dict[str, Any]]:
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT sr.filename, sr.score FROM screening_results sr
            WHERE sr.session_id = ? ORDER BY sr.score DESC
        ''', (session_id,))
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        conn.close()

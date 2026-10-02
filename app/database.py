"""
SQLite Database Layer for HealthRisk Application (Phase 3 with Auth & Per-User Isolation)
"""
import sqlite3
import json
import os
import hashlib
import secrets
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "health_risk.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hashes a password using PBKDF2-HMAC-SHA256 with salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_bytes = password.encode('utf-8')
    salt_bytes = bytes.fromhex(salt)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, 100000).hex()
    return pwd_hash, salt


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Assessments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 1,
            patient_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            age_group TEXT NOT NULL,
            family_history TEXT NOT NULL,
            symptoms_json TEXT NOT NULL,
            results_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    """)

    # Migration safe addition of user_id column if assessments already existed
    cursor.execute("PRAGMA table_info(assessments)")
    columns = [col["name"] for col in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE assessments ADD COLUMN user_id INTEGER DEFAULT 1;")

    # Sample Population Dataset Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample_population (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_code TEXT UNIQUE,
            age INTEGER,
            bmi REAL,
            systolic_bp REAL,
            fasting_glucose REAL,
            diabetes_risk_score REAL,
            cardio_risk_score REAL
        );
    """)

    conn.commit()

    # Create Default Demo User if not exists
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@healthrisk.edu",))
    demo = cursor.fetchone()
    if not demo:
        pwd_hash, salt = hash_password("demopass")
        cursor.execute(
            "INSERT INTO users (email, password_hash, salt) VALUES (?, ?, ?)",
            ("demo@healthrisk.edu", pwd_hash, salt)
        )
        conn.commit()

    conn.close()
    seed_sample_population()


def seed_sample_population():
    """Seeds sample dataset of N=20 patients if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sample_population")
    count = cursor.fetchone()[0]

    if count == 0:
        sample_data = [
            ("PAT-001", 28, 21.5, 114, 88, 12.5, 8.4),
            ("PAT-002", 34, 24.2, 120, 92, 18.0, 14.2),
            ("PAT-003", 45, 27.8, 132, 105, 34.5, 28.0),
            ("PAT-004", 52, 31.4, 142, 118, 62.0, 58.5),
            ("PAT-005", 61, 33.1, 150, 135, 78.4, 76.2),
            ("PAT-006", 24, 20.1, 110, 85, 9.2, 6.5),
            ("PAT-007", 39, 26.5, 126, 98, 28.1, 22.4),
            ("PAT-008", 48, 29.0, 138, 112, 45.0, 41.0),
            ("PAT-009", 56, 34.2, 148, 128, 72.8, 70.1),
            ("PAT-010", 63, 35.8, 158, 142, 86.5, 84.0),
            ("PAT-011", 31, 23.0, 118, 90, 15.2, 11.0),
            ("PAT-012", 42, 28.4, 130, 108, 38.0, 32.5),
            ("PAT-013", 50, 30.5, 140, 115, 54.2, 51.0),
            ("PAT-014", 58, 32.7, 146, 124, 69.0, 65.4),
            ("PAT-015", 26, 22.0, 112, 86, 11.0, 7.8),
            ("PAT-016", 37, 25.9, 124, 95, 24.5, 19.2),
            ("PAT-017", 46, 28.9, 136, 110, 42.0, 37.8),
            ("PAT-018", 54, 31.8, 144, 120, 61.5, 59.0),
            ("PAT-019", 67, 36.5, 162, 145, 91.2, 89.5),
            ("PAT-020", 29, 21.8, 116, 89, 13.0, 9.1)
        ]
        cursor.executemany("""
            INSERT INTO sample_population 
            (patient_code, age, bmi, systolic_bp, fasting_glucose, diabetes_risk_score, cardio_risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, sample_data)
        conn.commit()

    conn.close()


def create_user(email: str, password: str) -> Dict[str, Any]:
    email = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("User with this email already exists.")

    pwd_hash, salt = hash_password(password)
    cursor.execute(
        "INSERT INTO users (email, password_hash, salt) VALUES (?, ?, ?)",
        (email, pwd_hash, salt)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"id": user_id, "email": email}


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    email = email.strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash, salt FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return None

    expected_hash, _ = hash_password(password, user["salt"])
    if secrets.compare_digest(expected_hash, user["password_hash"]):
        return {"id": user["id"], "email": user["email"]}
    return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user["id"], "email": user["email"], "created_at": user["created_at"]}
    return None


def save_assessment(
    patient_name: str,
    age: int,
    age_group: str,
    family_history: str,
    symptoms: List[str],
    results: Dict[str, Any],
    user_id: int = 1
) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO assessments (user_id, patient_name, age, age_group, family_history, symptoms_json, results_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        patient_name,
        age,
        age_group,
        family_history,
        json.dumps(symptoms),
        json.dumps(results)
    ))
    conn.commit()
    assessment_id = cursor.lastrowid
    conn.close()
    return assessment_id


def get_all_assessments(user_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute("""
            SELECT id, user_id, patient_name, age, age_group, family_history, symptoms_json, results_json, created_at
            FROM assessments
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT id, user_id, patient_name, age, age_group, family_history, symptoms_json, results_json, created_at
            FROM assessments
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    assessments = []
    for row in rows:
        assessments.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "patient_name": row["patient_name"],
            "age": row["age"],
            "age_group": row["age_group"],
            "family_history": row["family_history"],
            "symptoms": json.loads(row["symptoms_json"]),
            "results": json.loads(row["results_json"]),
            "created_at": row["created_at"]
        })
    return assessments


def get_assessment_by_id(assessment_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute("""
            SELECT id, user_id, patient_name, age, age_group, family_history, symptoms_json, results_json, created_at
            FROM assessments
            WHERE id = ? AND user_id = ?
        """, (assessment_id, user_id))
    else:
        cursor.execute("""
            SELECT id, user_id, patient_name, age, age_group, family_history, symptoms_json, results_json, created_at
            FROM assessments
            WHERE id = ?
        """, (assessment_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "patient_name": row["patient_name"],
        "age": row["age"],
        "age_group": row["age_group"],
        "family_history": row["family_history"],
        "symptoms": json.loads(row["symptoms_json"]),
        "results": json.loads(row["results_json"]),
        "created_at": row["created_at"]
    }


def get_population_metrics() -> Dict[str, List[float]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT bmi, systolic_bp, diabetes_risk_score, cardio_risk_score FROM sample_population")
    rows = cursor.fetchall()
    conn.close()

    return {
        "bmi": [row["bmi"] for row in rows],
        "systolic_bp": [row["systolic_bp"] for row in rows],
        "diabetes_risk_score": [row["diabetes_risk_score"] for row in rows],
        "cardio_risk_score": [row["cardio_risk_score"] for row in rows]
    }

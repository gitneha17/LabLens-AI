
import sqlite3
from pathlib import Path


def get_db(database_path):
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path):
    Path(database_path).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    db = get_db(database_path)

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            email TEXT NOT NULL,

            gender TEXT NOT NULL DEFAULT 'Not specified',

            glucose REAL NOT NULL,
            glucose_test_type TEXT NOT NULL DEFAULT 'Not specified',
            haemoglobin REAL NOT NULL,
            cholesterol REAL NOT NULL,

            glucose_unit TEXT NOT NULL DEFAULT 'Unknown',
            haemoglobin_unit TEXT NOT NULL DEFAULT 'Unknown',
            cholesterol_unit TEXT NOT NULL DEFAULT 'Unknown',

            glucose_custom_unit TEXT,
            haemoglobin_custom_unit TEXT,
            cholesterol_custom_unit TEXT,

            glucose_ref_low REAL,
            glucose_ref_high REAL,

            haemoglobin_ref_low REAL,
            haemoglobin_ref_high REAL,

            cholesterol_ref_low REAL,
            cholesterol_ref_high REAL,

            risk_level TEXT NOT NULL DEFAULT 'Not assessed',
            remarks TEXT NOT NULL DEFAULT '',

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Safely migrate existing databases.
    existing_columns = {
        row["name"]
        for row in db.execute(
            "PRAGMA table_info(patients)"
        ).fetchall()
    }

    migrations = {
        "gender": (
            "ALTER TABLE patients ADD COLUMN "
            "gender TEXT NOT NULL DEFAULT 'Not specified'"
        ),

        "glucose_custom_unit": (
            "ALTER TABLE patients ADD COLUMN glucose_custom_unit TEXT"
        ),

        "haemoglobin_custom_unit": (
            "ALTER TABLE patients ADD COLUMN haemoglobin_custom_unit TEXT"
        ),

        "cholesterol_custom_unit": (
            "ALTER TABLE patients ADD COLUMN cholesterol_custom_unit TEXT"
        ),

        "glucose_test_type": (
            "ALTER TABLE patients ADD COLUMN "
            "glucose_test_type TEXT NOT NULL "
            "DEFAULT 'Not specified'"
        ),

        "glucose_unit": (
            "ALTER TABLE patients ADD COLUMN "
            "glucose_unit TEXT NOT NULL DEFAULT 'Unknown'"
        ),

        "haemoglobin_unit": (
            "ALTER TABLE patients ADD COLUMN "
            "haemoglobin_unit TEXT NOT NULL DEFAULT 'Unknown'"
        ),

        "cholesterol_unit": (
            "ALTER TABLE patients ADD COLUMN "
            "cholesterol_unit TEXT NOT NULL DEFAULT 'Unknown'"
        ),

        "glucose_ref_low": (
            "ALTER TABLE patients ADD COLUMN glucose_ref_low REAL"
        ),

        "glucose_ref_high": (
            "ALTER TABLE patients ADD COLUMN glucose_ref_high REAL"
        ),

        "haemoglobin_ref_low": (
            "ALTER TABLE patients ADD COLUMN haemoglobin_ref_low REAL"
        ),

        "haemoglobin_ref_high": (
            "ALTER TABLE patients ADD COLUMN haemoglobin_ref_high REAL"
        ),

        "cholesterol_ref_low": (
            "ALTER TABLE patients ADD COLUMN cholesterol_ref_low REAL"
        ),

        "cholesterol_ref_high": (
            "ALTER TABLE patients ADD COLUMN cholesterol_ref_high REAL"
        ),

        "risk_level": (
            "ALTER TABLE patients ADD COLUMN "
            "risk_level TEXT NOT NULL DEFAULT 'Not assessed'"
        ),
    }

    for column, sql in migrations.items():
        if column not in existing_columns:
            db.execute(sql)

    db.commit()
    db.close()

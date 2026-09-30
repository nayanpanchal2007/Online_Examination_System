"""SQLite storage and scoring for the examination portal."""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


DB_PATH = Path(__file__).with_name("exam_portal.db")


@contextmanager
def connect(db_path: str | Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}:{digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, expected = stored_hash.split(":", maxsplit=1)
    actual = _hash_password(password, bytes.fromhex(salt_hex)).split(":", maxsplit=1)[1]
    return secrets.compare_digest(actual, expected)


def initialize_database(db_path: str | Path = DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('student', 'admin'))
            );
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
                prompt TEXT NOT NULL,
                options_json TEXT NOT NULL,
                correct_answer TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                exam_id INTEGER NOT NULL REFERENCES exams(id),
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                answers_json TEXT NOT NULL,
                submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO users (username, full_name, password_hash, role) VALUES (?, ?, ?, ?)",
                [
                    ("admin", "Course Administrator", _hash_password("admin123"), "admin"),
                    ("alice", "Alice Johnson", _hash_password("alice123"), "student"),
                    ("sam", "Sam Patel", _hash_password("sam123"), "student"),
                ],
            )
            _seed_exams(connection)


def _seed_exams(connection: sqlite3.Connection) -> None:
    sample_exams = [
        (
            "Python Foundations",
            "Python",
            "Core language concepts, data structures, and functions.",
            [
                ("Which Python type is immutable?", ["list", "dictionary", "tuple", "set"], "tuple"),
                ("What does len([2, 4, 6]) return?", ["2", "3", "4", "6"], "3"),
                ("Which keyword defines a function?", ["func", "def", "function", "lambda"], "def"),
                ("What is the result of 7 // 2?", ["3", "3.5", "4", "1"], "3"),
            ],
        ),
        (
            "Data Science Essentials",
            "Data Science",
            "A short check on data analysis and machine learning fundamentals.",
            [
                ("Which pandas object is a labeled one-dimensional array?", ["DataFrame", "Series", "Index", "Panel"], "Series"),
                ("Which measure is least affected by extreme values?", ["Mean", "Range", "Median", "Variance"], "Median"),
                ("What does a test dataset help estimate?", ["Training speed", "Generalization", "Column count", "Missing values"], "Generalization"),
                ("Which plot is most useful for a numeric distribution?", ["Histogram", "Pie chart", "Network graph", "Map"], "Histogram"),
            ],
        ),
    ]
    for title, subject, description, questions in sample_exams:
        cursor = connection.execute(
            "INSERT INTO exams (title, subject, description) VALUES (?, ?, ?)",
            (title, subject, description),
        )
        connection.executemany(
            "INSERT INTO questions (exam_id, prompt, options_json, correct_answer) VALUES (?, ?, ?, ?)",
            [(cursor.lastrowid, prompt, json.dumps(options), answer) for prompt, options, answer in questions],
        )


def authenticate(username: str, password: str, db_path: str | Path = DB_PATH) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        user = connection.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()
    if user is None or not _verify_password(password, user["password_hash"]):
        return None
    return {"id": user["id"], "username": user["username"], "full_name": user["full_name"], "role": user["role"]}


def list_students(db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, username, full_name, role FROM users WHERE role = 'student' ORDER BY full_name, username"
        ).fetchall()
    return [dict(row) for row in rows]


def add_student(username: str, full_name: str, password: str, db_path: str | Path = DB_PATH) -> int:
    clean_username = username.strip()
    clean_full_name = full_name.strip()
    clean_password = password.strip()
    if not clean_username or not clean_full_name or not clean_password:
        raise ValueError("Username, full name, and password are required.")
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO users (username, full_name, password_hash, role) VALUES (?, ?, ?, 'student')",
            (clean_username, clean_full_name, _hash_password(clean_password)),
        )
        return int(cursor.lastrowid)


def update_student(
    student_id: int,
    username: str | None = None,
    full_name: str | None = None,
    password: str | None = None,
    db_path: str | Path = DB_PATH,
) -> None:
    with connect(db_path) as connection:
        existing = connection.execute(
            "SELECT id, username, full_name, role FROM users WHERE id = ?",
            (student_id,),
        ).fetchone()
        if existing is None or existing["role"] != "student":
            raise ValueError("Student not found.")

        new_username = username.strip() if username is not None else existing["username"]
        new_full_name = full_name.strip() if full_name is not None else existing["full_name"]
        if not new_username or not new_full_name:
            raise ValueError("Username and full name cannot be empty.")

        values: list[Any] = [new_username, new_full_name]
        update_fields = ["username = ?", "full_name = ?"]

        if password is not None:
            clean_password = password.strip()
            if not clean_password:
                raise ValueError("Password cannot be empty.")
            update_fields.append("password_hash = ?")
            values.append(_hash_password(clean_password))

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        values.append(student_id)
        connection.execute(query, tuple(values))


def delete_student(student_id: int, db_path: str | Path = DB_PATH) -> None:
    with connect(db_path) as connection:
        existing = connection.execute("SELECT role FROM users WHERE id = ?", (student_id,)).fetchone()
        if existing is None or existing["role"] != "student":
            raise ValueError("Student not found.")
        connection.execute("DELETE FROM attempts WHERE user_id = ?", (student_id,))
        connection.execute("DELETE FROM users WHERE id = ?", (student_id,))


def list_exams(db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT e.id, e.title, e.subject, e.description, COUNT(q.id) AS question_count
            FROM exams e LEFT JOIN questions q ON q.exam_id = e.id
            GROUP BY e.id ORDER BY e.id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_questions(exam_id: int, db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, prompt, options_json FROM questions WHERE exam_id = ? ORDER BY id",
            (exam_id,),
        ).fetchall()
    return [{**dict(row), "options": json.loads(row["options_json"])} for row in rows]


def add_exam(title: str, subject: str, description: str, db_path: str | Path = DB_PATH) -> int:
    with connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO exams (title, subject, description) VALUES (?, ?, ?)",
            (title.strip(), subject.strip(), description.strip()),
        )
        return int(cursor.lastrowid)


def add_question(
    exam_id: int,
    prompt: str,
    options: list[str],
    correct_answer: str,
    db_path: str | Path = DB_PATH,
) -> None:
    normalized_options = [option.strip() for option in options]
    if len(normalized_options) < 2 or any(not option for option in normalized_options):
        raise ValueError("Add at least two non-empty answer options.")
    if correct_answer not in normalized_options:
        raise ValueError("The correct answer must match one of the options.")
    with connect(db_path) as connection:
        connection.execute(
            "INSERT INTO questions (exam_id, prompt, options_json, correct_answer) VALUES (?, ?, ?, ?)",
            (exam_id, prompt.strip(), json.dumps(normalized_options), correct_answer),
        )


def submit_attempt(
    user_id: int,
    exam_id: int,
    answers: dict[int, str],
    db_path: str | Path = DB_PATH,
) -> dict[str, int]:
    with connect(db_path) as connection:
        questions = connection.execute(
            "SELECT id, correct_answer FROM questions WHERE exam_id = ? ORDER BY id",
            (exam_id,),
        ).fetchall()
        if not questions:
            raise ValueError("This exam does not have any questions yet.")
        score = sum(answers.get(question["id"]) == question["correct_answer"] for question in questions)
        total = len(questions)
        connection.execute(
            "INSERT INTO attempts (user_id, exam_id, score, total, answers_json) VALUES (?, ?, ?, ?, ?)",
            (user_id, exam_id, score, total, json.dumps(answers)),
        )
    return {"score": score, "total": total}


def get_attempts(user_id: int | None = None, db_path: str | Path = DB_PATH) -> list[dict[str, Any]]:
    query = """
        SELECT a.id, a.user_id, u.full_name, u.username, e.title AS exam_title,
               e.subject, a.score, a.total, a.submitted_at
        FROM attempts a
        JOIN users u ON u.id = a.user_id
        JOIN exams e ON e.id = a.exam_id
    """
    parameters: tuple[Any, ...] = ()
    if user_id is not None:
        query += " WHERE a.user_id = ?"
        parameters = (user_id,)
    query += " ORDER BY a.submitted_at DESC, a.id DESC"
    with connect(db_path) as connection:
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]
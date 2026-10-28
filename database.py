
import sqlite3
from pathlib import Path
from datetime import datetime

# Store the database in the project folder.
DB_PATH = Path(__file__).resolve().parent / "stories.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                terms TEXT NOT NULL,
                genre TEXT NOT NULL,
                target_words INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_story(title, content, terms, genre, target_words):
    created_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO stories
            (title, content, terms, genre, target_words, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            content,
            ", ".join(terms),
            genre,
            target_words,
            created_at,
        ))
        return cursor.lastrowid


def get_all_stories():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, title, terms, genre, target_words, created_at
            FROM stories
            ORDER BY id DESC
        """).fetchall()
        return [dict(row) for row in rows]


def get_story(story_id):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM stories WHERE id = ?
        """, (story_id,)).fetchone()
        return dict(row) if row else None


def delete_story(story_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM stories WHERE id = ?",
            (story_id,),
        )


def clear_history():
    with get_connection() as conn:
        conn.execute("DELETE FROM stories")


initialize_database()

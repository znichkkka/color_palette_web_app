import sqlite3
import json
import os
import hashlib
import secrets
from datetime import datetime


DB_FOLDER = "data"
DB_PATH = os.path.join(DB_FOLDER, "app.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def init_db():
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    conn = get_connection()
    cursor = conn.cursor()

    create_users_table(cursor)
    create_sessions_table(cursor)
    create_images_table(cursor)
    add_missing_columns(cursor)

    conn.commit()
    conn.close()


def create_users_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)


def create_sessions_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


def create_images_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            palette TEXT NOT NULL,
            colors_count INTEGER NOT NULL,
            color_format TEXT NOT NULL DEFAULT 'hex',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


def add_missing_columns(cursor):
    cursor.execute("PRAGMA table_info(images)")
    columns = cursor.fetchall()

    column_names = []

    for column in columns:
        column_names.append(column[1])

    if "color_format" not in column_names:
        cursor.execute("""
            ALTER TABLE images
            ADD COLUMN color_format TEXT NOT NULL DEFAULT 'hex'
        """)


def hash_password(password, salt):
    password_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password_bytes,
        salt_bytes,
        100000
    )

    return password_hash.hex()


def create_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    created_at = get_current_time()

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, salt, created_at)
            VALUES (?, ?, ?, ?)
        """, (username, password_hash, salt, created_at))

        conn.commit()
        user_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        conn.close()
        return None

    conn.close()
    return user_id


def check_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, password_hash, salt
        FROM users
        WHERE username = ?
    """, (username,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    user_id = row[0]
    saved_hash = row[1]
    salt = row[2]

    entered_hash = hash_password(password, salt)

    if entered_hash == saved_hash:
        return user_id

    return None


def create_session(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    session_id = secrets.token_hex(32)
    created_at = get_current_time()

    cursor.execute("""
        INSERT INTO sessions (user_id, session_id, created_at)
        VALUES (?, ?, ?)
    """, (user_id, session_id, created_at))

    conn.commit()
    conn.close()

    return session_id


def get_user_by_session(session_id):
    if session_id is None:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT users.id, users.username
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "username": row[1]
    }


def delete_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM sessions
        WHERE session_id = ?
    """, (session_id,))

    conn.commit()
    conn.close()


def save_image(user_id, filename, filepath, palette, colors_count, color_format="hex"):
    conn = get_connection()
    cursor = conn.cursor()

    upload_date = get_current_time()
    palette_text = json.dumps(palette)

    cursor.execute("""
        INSERT INTO images (
            user_id,
            filename,
            filepath,
            upload_date,
            palette,
            colors_count,
            color_format
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        filename,
        filepath,
        upload_date,
        palette_text,
        colors_count,
        color_format
    ))

    image_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return image_id


def get_image(image_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, filename, filepath, upload_date, palette, colors_count, color_format
        FROM images
        WHERE id = ?
    """, (image_id,))

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return create_image_dict(row)


def get_all_images(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, user_id, filename, filepath, upload_date, palette, colors_count, color_format
        FROM images
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    images = []

    for row in rows:
        images.append(create_image_dict(row))

    return images


def create_image_dict(row):
    return {
        "id": row[0],
        "user_id": row[1],
        "filename": row[2],
        "filepath": row[3],
        "upload_date": row[4],
        "palette": json.loads(row[5]),
        "colors_count": row[6],
        "color_format": row[7]
    }


def delete_image(image_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filepath
        FROM images
        WHERE id = ? AND user_id = ?
    """, (image_id, user_id))

    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    filepath = row[0]

    cursor.execute("""
        DELETE FROM images
        WHERE id = ? AND user_id = ?
    """, (image_id, user_id))

    conn.commit()
    conn.close()

    return filepath

def delete_all_user_images(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filepath
        FROM images
        WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()

    cursor.execute("""
        DELETE FROM images
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

    filepaths = []

    for row in rows:
        filepaths.append(row[0])

    return filepaths


def get_user_image_paths(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT filepath
        FROM images
        WHERE user_id = ?
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    filepaths = []

    for row in rows:
        filepaths.append(row[0])

    return filepaths


def get_user_images_count(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM images
        WHERE user_id = ?
    """, (user_id,))

    count = cursor.fetchone()[0]
    conn.close()

    return count


def delete_user_account(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM images
        WHERE user_id = ?
    """, (user_id,))

    cursor.execute("""
        DELETE FROM sessions
        WHERE user_id = ?
    """, (user_id,))

    cursor.execute("""
        DELETE FROM users
        WHERE id = ?
    """, (user_id,))

    conn.commit()
    conn.close()
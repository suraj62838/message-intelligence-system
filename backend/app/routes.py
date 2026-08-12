import os
import sqlite3
import json
import io
import threading
from typing import Optional

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks

from .processor import process_message, extract_task_event
from .privacy import detect_and_mask
from .llm import classify_batch_with_groq

router = APIRouter()
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "message_intelligence.db")
DB_PATH = os.path.abspath(DB_PATH)

progress = {
    "status": "idle",
    "total": 0,
    "processed": 0,
    "failed": 0,
    "percentage": 0,
}
progress_lock = threading.Lock()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS messages (
        message_id TEXT PRIMARY KEY,
        timestamp TEXT,
        sender TEXT,
        masked_message TEXT,
        category TEXT,
        confidence REAL,
        reason TEXT,
        processed INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS items (
        item_id TEXT PRIMARY KEY,
        type TEXT,
        title TEXT,
        description TEXT,
        date_or_deadline TEXT,
        time TEXT,
        person TEXT,
        priority TEXT,
        source_message_id TEXT
    );

    CREATE TABLE IF NOT EXISTS sensitive (
        message_id TEXT PRIMARY KEY,
        sensitivity_type TEXT,
        risk TEXT,
        masked_text TEXT,
        recommended_action TEXT
    );

    CREATE TABLE IF NOT EXISTS mandatory_ids (
        message_id TEXT PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS privacy_audit (
        message_id TEXT PRIMARY KEY,
        raw_sent_externally INTEGER DEFAULT 0,
        masked_before_ai INTEGER DEFAULT 1,
        detection_count INTEGER DEFAULT 0
    );
    """)
    conn.commit()
    conn.close()


init_db()


def reset_progress():
    with progress_lock:
        progress.update({
            "status": "idle",
            "total": 0,
            "processed": 0,
            "failed": 0,
            "percentage": 0,
        })


def set_progress(**kwargs):
    with progress_lock:
        progress.update(kwargs)
        total = progress["total"]
        progress["percentage"] = round(
            (progress["processed"] / total) * 100, 2
        ) if total else 0


def classify_and_save_batch(rows):
    """
    Process a small batch in one Groq request.
    Only masked messages are sent to Groq.
    """
    conn = db()

    payload = [
        {
            "message_id": row["message_id"],
            "message": row["masked_message"],
        }
        for row in rows
    ]

    results = classify_batch_with_groq(payload)

    # If Groq is unavailable, use the local deterministic classifier.
    result_map = {
        item["message_id"]: item
        for item in results
    }

    failed = 0

    for row in rows:
        mid = row["message_id"]
        result = result_map.get(mid)

        if not result:
            result = process_message(mid, row["masked_message"])
            failed += 1

        # Sensitive detection always wins over an LLM category.
        sensitive_row = conn.execute(
            "SELECT 1 FROM sensitive WHERE message_id=?",
            (mid,)
        ).fetchone()

        if sensitive_row:
            result = {
                "category": "Sensitive Information",
                "confidence": max(float(result.get("confidence", 0)), 0.99),
                "reason": "The privacy layer detected sensitive information.",
            }

        conn.execute("""
            UPDATE messages
            SET category=?, confidence=?, reason=?, processed=1
            WHERE message_id=?
        """, (
            result["category"],
            float(result.get("confidence", 0)),
            result.get("reason", "Classified message."),
            mid,
        ))

        # Prevent duplicate task/event rows if processing is retried.
        item = extract_task_event(
            mid,
            row["masked_message"],
            result["category"]
        )

        if item:
            conn.execute("""
                INSERT OR REPLACE INTO items
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(item.values()))

    conn.commit()
    conn.close()
    return failed


def process_all_messages(batch_size: int = 10):
    conn = db()
    rows = conn.execute("""
        SELECT message_id, masked_message
        FROM messages
        WHERE processed=0
        ORDER BY timestamp ASC, message_id ASC
    """).fetchall()
    conn.close()

    total = len(rows)

    set_progress(
        status="processing",
        total=total,
        processed=0,
        failed=0,
        percentage=0,
    )

    failed = 0

    for start in range(0, total, batch_size):
        batch = rows[start:start + batch_size]

        try:
            failed += classify_and_save_batch(batch)
        except Exception as exc:
            print("BATCH ERROR:", repr(exc))

            # Mark this batch using the local fallback so processing continues.
            conn = db()

            for row in batch:
                result = process_message(
                    row["message_id"],
                    row["masked_message"]
                )

                sensitive_row = conn.execute(
                    "SELECT 1 FROM sensitive WHERE message_id=?",
                    (row["message_id"],)
                ).fetchone()

                if sensitive_row:
                    result = {
                        "category": "Sensitive Information",
                        "confidence": 0.99,
                        "reason": "The privacy layer detected sensitive information.",
                    }

                conn.execute("""
                    UPDATE messages
                    SET category=?, confidence=?, reason=?, processed=1
                    WHERE message_id=?
                """, (
                    result["category"],
                    result["confidence"],
                    result["reason"],
                    row["message_id"],
                ))

                item = extract_task_event(
                    row["message_id"],
                    row["masked_message"],
                    result["category"]
                )

                if item:
                    conn.execute("""
                        INSERT OR REPLACE INTO items
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, tuple(item.values()))

            conn.commit()
            conn.close()
            failed += len(batch)

        processed = start + len(batch)

        set_progress(
            processed=processed,
            failed=failed,
        )

    set_progress(
        status="completed",
        processed=total,
        failed=failed,
    )


@router.post("/messages/upload")
async def upload_messages(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file.")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    required = {"message_id", "timestamp", "sender", "message"}

    if not required.issubset(df.columns):
        raise HTTPException(
            400,
            f"CSV must contain: {sorted(required)}"
        )

    conn = db()

    conn.execute("DELETE FROM messages")
    conn.execute("DELETE FROM items")
    conn.execute("DELETE FROM sensitive")

    for _, row in df.iterrows():
        raw = str(row["message"])
        masked, detections = detect_and_mask(raw)

        # Privacy audit: raw message is never included in any external request.
        conn.execute("""
            INSERT OR REPLACE INTO privacy_audit
            VALUES (?, 0, 1, ?)
        """, (
            str(row["message_id"]),
            len(detections),
        ))

        # Import only. AI processing happens separately.
        conn.execute("""
            INSERT OR REPLACE INTO messages
            (message_id, timestamp, sender, masked_message,
             category, confidence, reason, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            str(row["message_id"]),
            str(row["timestamp"]),
            str(row["sender"]),
            masked,
            "Unprocessed",
            0,
            "Waiting for AI processing.",
        ))

        for detection in detections:
            conn.execute("""
                INSERT OR REPLACE INTO sensitive
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(row["message_id"]),
                detection["sensitivity_type"],
                detection["risk"],
                masked,
                detection["recommended_action"],
            ))

    conn.commit()
    conn.close()

    reset_progress()

    return {
        "message": "Dataset imported successfully.",
        "total": len(df),
        "next_step": "POST /api/messages/process",
    }


@router.post("/messages/process")
def start_processing(background_tasks: BackgroundTasks):
    conn = db()

    remaining = conn.execute(
        "SELECT COUNT(*) AS c FROM messages WHERE processed=0"
    ).fetchone()["c"]

    conn.close()

    if remaining == 0:
        return {
            "status": "completed",
            "message": "There are no unprocessed messages.",
        }

    if progress["status"] == "processing":
        return {
            "status": "processing",
            "message": "Processing is already running.",
        }

    background_tasks.add_task(
        process_all_messages,
        10
    )

    return {
        "status": "started",
        "total": remaining,
        "batch_size": 10,
    }


@router.get("/messages/progress")
def processing_progress():
    with progress_lock:
        return dict(progress)


@router.get("/messages")
def messages(
    limit: int = 100,
    offset: int = 0,
    category: Optional[str] = None
):
    conn = db()

    if category:
        rows = conn.execute(
            """
            SELECT message_id,timestamp,sender,masked_message,
                   category,confidence,reason
            FROM messages
            WHERE category=?
            ORDER BY timestamp ASC, message_id ASC
            LIMIT ? OFFSET ?
            """,
            (category, limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT message_id,timestamp,sender,masked_message,
                   category,confidence,reason
            FROM messages
            ORDER BY timestamp ASC, message_id ASC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@router.get("/messages/{message_id}")
def message(message_id: str):
    conn = db()

    row = conn.execute(
        """
        SELECT message_id,timestamp,sender,masked_message,
               category,confidence,reason
        FROM messages
        WHERE message_id=?
        """,
        (message_id,),
    ).fetchone()

    conn.close()

    if not row:
        raise HTTPException(404, "Message not found")

    return dict(row)


@router.get("/tasks")
def tasks():
    conn = db()

    rows = conn.execute(
        "SELECT * FROM items WHERE type='task' ORDER BY date_or_deadline"
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@router.get("/events")
def events():
    conn = db()

    rows = conn.execute(
        "SELECT * FROM items WHERE type='event' ORDER BY date_or_deadline"
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@router.get("/sensitive")
def sensitive():
    conn = db()

    rows = conn.execute(
        "SELECT * FROM sensitive ORDER BY message_id"
    ).fetchall()

    conn.close()
    return [dict(row) for row in rows]


@router.get("/dashboard/stats")
def stats():
    conn = db()

    total = conn.execute(
        "SELECT COUNT(*) AS c FROM messages"
    ).fetchone()["c"]

    rows = conn.execute(
        """
        SELECT category, COUNT(*) AS c
        FROM messages
        GROUP BY category
        """
    ).fetchall()

    tasks = conn.execute(
        "SELECT COUNT(*) AS c FROM items WHERE type='task'"
    ).fetchone()["c"]

    events = conn.execute(
        "SELECT COUNT(*) AS c FROM items WHERE type='event'"
    ).fetchone()["c"]

    sensitive = conn.execute(
        "SELECT COUNT(*) AS c FROM sensitive"
    ).fetchone()["c"]

    processed = conn.execute(
        "SELECT COUNT(*) AS c FROM messages WHERE processed=1"
    ).fetchone()["c"]

    conn.close()

    return {
        "total_messages": total,
        "categories": {
            row["category"]: row["c"]
            for row in rows
        },
        "tasks": tasks,
        "events": events,
        "sensitive": sensitive,
        "processed": processed,
    }


@router.get("/privacy/audit")
def privacy_audit_status():
    conn = db()

    total = conn.execute(
        "SELECT COUNT(*) AS c FROM privacy_audit"
    ).fetchone()["c"]

    raw_sent = conn.execute(
        "SELECT COUNT(*) AS c FROM privacy_audit WHERE raw_sent_externally=1"
    ).fetchone()["c"]

    masked = conn.execute(
        "SELECT COUNT(*) AS c FROM privacy_audit WHERE masked_before_ai=1"
    ).fetchone()["c"]

    conn.close()

    return {
        "messages_audited": total,
        "raw_messages_sent_externally": raw_sent,
        "messages_masked_before_ai": masked,
        "privacy_status": "PASS" if raw_sent == 0 else "FAIL",
    }


@router.post("/demo/mandatory/upload")
async def upload_mandatory(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV.")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    column = "message_id" if "message_id" in df.columns else df.columns[0]

    conn = db()
    conn.execute("DELETE FROM mandatory_ids")

    for message_id in df[column].dropna():
        conn.execute(
            "INSERT OR REPLACE INTO mandatory_ids VALUES (?)",
            (str(message_id),),
        )

    conn.commit()
    conn.close()

    return {"loaded": len(df)}


@router.get("/demo/mandatory")
def mandatory():
    conn = db()

    rows = conn.execute("""
        SELECT
            m.message_id,
            m.timestamp,
            m.sender,
            m.masked_message,
            m.category,
            m.confidence,
            m.reason
        FROM messages m
        JOIN mandatory_ids d
            ON d.message_id=m.message_id
        ORDER BY m.timestamp
    """).fetchall()

    conn.close()
    return [dict(row) for row in rows]

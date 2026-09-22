import os
import sqlite3
from contextlib import closing

from flask import Flask, g, jsonify, request

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "dev")
DB_PATH = os.getenv("DB_PATH", "/data/linkvault.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                tag TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        db.commit()


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": APP_VERSION}), 200


@app.route("/links", methods=["POST"])
def add_link():
    payload = request.get_json(silent=True) or {}
    title = payload.get("title")
    url = payload.get("url")
    tag = payload.get("tag", "")

    if not title or not url:
        return jsonify({"error": "title and url are required"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO links (title, url, tag) VALUES (?, ?, ?)",
        (title, url, tag),
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, "title": title, "url": url, "tag": tag}), 201


@app.route("/links", methods=["GET"])
def list_links():
    tag = request.args.get("tag")
    db = get_db()
    if tag:
        rows = db.execute("SELECT * FROM links WHERE tag = ? ORDER BY id DESC", (tag,)).fetchall()
    else:
        rows = db.execute("SELECT * FROM links ORDER BY id DESC").fetchall()
    return jsonify([dict(row) for row in rows])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
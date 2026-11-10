"""Deliberately flawed API fixture for Aether security & quality evaluation.

Contains 4 intentional security and design flaws:
  1. Broken Object-Level Authorization (BOLA/IDOR): trusts client query param user_id without verification.
  2. SQL injection via unescaped string formatting.
  3. Verbose error handling leaking internal stack traces.
  4. No authentication middleware or CSRF protection.
"""
from __future__ import annotations

import json
import sqlite3
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


def init_db(db_path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, secret_notes TEXT);")
    cur.execute("INSERT INTO users VALUES (1, 'alice', 'alice@corp.internal', 'Alice personal confidential record');")
    cur.execute("INSERT INTO users VALUES (2, 'bob', 'bob@corp.internal', 'Bob personal confidential record');")
    conn.commit()
    return conn


class FlawedAPIHandler(BaseHTTPRequestHandler):
    conn: sqlite3.Connection = None  # type: ignore

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # -------------------------------------------------------------
        # Flaw 1 & 2: IDOR and SQL Injection via unescaped query string
        # -------------------------------------------------------------
        if parsed.path == "/api/user":
            user_id = qs.get("id", [""])[0]
            if not user_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing id parameter"}')
                return

            try:
                # FLAW: String formatting in SQL query
                query = f"SELECT id, username, email, secret_notes FROM users WHERE id = {user_id};"
                cur = self.conn.cursor()
                cur.execute(query)
                row = cur.fetchone()
                if not row:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'{"error": "User not found"}')
                    return

                res = {"id": row[0], "username": row[1], "email": row[2], "secret_notes": row[3]}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                # -------------------------------------------------------------
                # Flaw 3: Stack trace leakage in response
                # -------------------------------------------------------------
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                err_payload = {
                    "error": "Internal Database Error",
                    "exception": str(e),
                    "stack_trace": traceback.format_exc(),  # FLAW
                }
                self.wfile.write(json.dumps(err_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence standard HTTP logs during tests
        pass

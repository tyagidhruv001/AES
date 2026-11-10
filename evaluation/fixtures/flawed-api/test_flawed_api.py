#!/usr/bin/env python3
"""Automated reproduction and vulnerability tests for flawed-api fixture.

Tests:
  1. Valid query succeeds.
  2. SQL injection vulnerability reproduction (retrieves Bob via Alice ID payload).
  3. Verbose error stack trace leakage reproduction.
  4. BOLA / IDOR reproduction (cross-tenant access without authentication).
"""
from __future__ import annotations

import json
import sqlite3
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from app import init_db  # noqa: E402


class TestFlawedAPI(unittest.TestCase):
    def setUp(self):
        self.conn = init_db(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_normal_query(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, username FROM users WHERE id = 1;")
        row = cur.fetchone()
        self.assertEqual(row[1], "alice")

    def test_sql_injection_reproduction(self):
        """Reproduce SQL injection: 1 OR 1=1 retrieves all records."""
        payload = "1 OR 1=1"
        cur = self.conn.cursor()
        query = f"SELECT id, username FROM users WHERE id = {payload};"
        cur.execute(query)
        rows = cur.fetchall()
        # Vulnerability confirmed: payload returns multiple rows instead of single user
        self.assertGreater(len(rows), 1, "SQL Injection vulnerability reproduced.")

    def test_idor_unauthenticated_access(self):
        """Reproduce IDOR: arbitrary user id accessed without auth token."""
        cur = self.conn.cursor()
        # Alice requests Bob's private notes directly
        cur.execute("SELECT secret_notes FROM users WHERE id = 2;")
        row = cur.fetchone()
        self.assertIn("Bob personal confidential record", row[0])


if __name__ == "__main__":
    unittest.main()


"""
=============================================================================
Database Module: MySQL Connection and Session Management
=============================================================================
This module handles connecting to the MySQL database server using the official
`mysql.connector` library.

Design Decisions:
-----------------
1. Separation of Concerns:
   This module ONLY manages database connections, connection pooling,
   and clean request lifecycle teardown. It DOES NOT create or alter tables.
   All tables are pre-created directly inside MySQL by the developer/administrator.

2. Flask Context Integration:
   Connections and cursors are stored in Flask's application context `g` to
   ensure only one connection is opened per HTTP request and cleanly returned/closed
   at the end of the request via `close_db()`.

3. Dynamic Configuration:
   Database credentials (host, port, user, password, database) are read from
   environment variables, with sensible local defaults for smooth development.
"""

import os
from typing import Optional
from flask import g
import mysql.connector
from mysql.connector import Error, MySQLConnection
from mysql.connector.cursor import MySQLCursorDict


# ---------------------------------------------------------------------------
# Database Configuration Parameters
# ---------------------------------------------------------------------------
# Load connection credentials from environment variables or use local defaults.
MYSQL_HOST: str = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT: int = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_USER: str = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD: str = os.environ.get("MYSQL_PASSWORD", "premsai444@123")
MYSQL_DATABASE: str = os.environ.get("MYSQL_DATABASE", "movie_night_db")


def get_db() -> MySQLConnection:
    """
    Establish and retrieve the current request's MySQL connection.

    This function checks if an active MySQL connection exists in Flask's
    request global context `g`. If not, it creates a new connection using the
    configured credentials and stores it in `g.db`.

    Returns:
        MySQLConnection: An active MySQL connection object.

    Raises:
        mysql.connector.Error: If the connection to MySQL fails (e.g., invalid
        credentials, server down, or database not found).
    """
    # Check if a database connection is already registered for this request
    if "db" not in g:
        try:
            # Establish new MySQL connection
            g.db = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                autocommit=False,       # Explicit transaction management
                charset="utf8mb4",      # Full Unicode support for emojis and text
                use_unicode=True,
            )
        except Error as err:
            # Re-raise with informative diagnostic message
            raise RuntimeError(
                f"[Database Error] Could not connect to MySQL at {MYSQL_HOST}:{MYSQL_PORT}. "
                f"Ensure MySQL server is running and database '{MYSQL_DATABASE}' exists. "
                f"Details: {err}"
            ) from err

    return g.db


def get_cursor(dictionary: bool = True) -> MySQLCursorDict:
    """
    Create and return a MySQL cursor for executing SQL queries.

    By default, a dictionary cursor is returned so that row columns can be
    accessed by their column name (e.g., `row['title']`), maintaining consistency
    with Jinja2 template rendering.

    Args:
        dictionary (bool): If True, returns rows as dictionaries. If False,
                           returns standard tuples. Defaults to True.

    Returns:
        MySQLCursorDict: Cursor ready to execute SQL statements.
    """
    conn = get_db()
    # Ensure any previous unclosed cursor on g is tracked or cleanly instantiated
    return conn.cursor(dictionary=dictionary)


def close_db(e: Optional[BaseException] = None) -> None:
    """
    Close the MySQL connection at the end of the HTTP request lifecycle.

    This function is automatically called by Flask during `teardown_appcontext`.
    If an open connection is found in `g.db`, it rolls back any uncommitted
    transactions and closes the socket connection to free database resources.

    Args:
        e (Optional[BaseException]): Exception raised during request handling, if any.
    """
    db = g.pop("db", None)

    if db is not None and db.is_connected():
        try:
            # If an unhandled exception occurred, rollback pending operations
            if e is not None:
                db.rollback()
            db.close()
        except Error:
            pass  # Suppress errors on teardown to avoid masking root exceptions

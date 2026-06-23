import sqlite3
import pathlib
import os
from datetime import datetime


class FileIndexer:
    def __init__(self, db_path="data/file_index.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Creates the SQLite database and tables if they don't exist."""
        pathlib.Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL UNIQUE,
                    extension TEXT,
                    size_bytes INTEGER,
                    last_modified REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def create_search_index(self, start_dir: str = None) -> None:
        """
        Crawls the directory and builds the search index.
        Safely ignores PermissionErrors when scanning restricted folders like system root.
        """
        if start_dir is None:
            start_dir = str(pathlib.Path.cwd())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Clear stale entries before rebuilding to keep the index fresh
            cursor.execute("DELETE FROM files")

            # os.walk with onerror silently skips restricted folders on Windows
            def _on_walk_error(error):
                pass  # Silently skip folders we can't access

            for root, dirs, files in os.walk(start_dir, onerror=_on_walk_error):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    try:
                        stat = os.stat(file_path)
                        extension = pathlib.Path(file_name).suffix
                        cursor.execute(
                            """INSERT OR IGNORE INTO files 
                               (file_name, file_path, extension, size_bytes, last_modified) 
                               VALUES (?, ?, ?, ?, ?)""",
                            (file_name, file_path, extension, stat.st_size, stat.st_mtime)
                        )
                    except (sqlite3.Error, PermissionError, OSError):
                        pass

            conn.commit()

    def search_files(self, query: str, max_results: int = 10):
        """
        Searches for files by filename in the index.

        Args:
            query: The query string to search for
            max_results: The maximum number of results to return

        Returns:
            A list of file paths matching the query
        """
        sql_search_term = f"%{query}%"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Search by file_name so folder names don't pollute results
            cursor.execute(
                "SELECT file_path FROM files WHERE file_name LIKE ? LIMIT ?",
                (sql_search_term, max_results)
            )

            results = cursor.fetchall()
            file_paths = [row[0] for row in results]

        return file_paths
```python
import sqlite3
from pathlib import Path

DB_FILE = "game_tracker.db"
INIT_SQL_FILE = "init.sql"


class Database:
    """Управление подключением к локальной базе данных SQLite."""

    _connection = None

    @classmethod
    def get_connection(cls) -> sqlite3.Connection:
        if cls._connection is None:
            cls._connection = sqlite3.connect(DB_FILE)
            cls._connection.execute("PRAGMA foreign_keys = ON;")
            cls._connection.row_factory = sqlite3.Row
        return cls._connection

    @classmethod
    def close_connection(cls):
        if cls._connection is not None:
            cls._connection.close()
            cls._connection = None

    @classmethod
    def initialize_database(cls, script_path: str = INIT_SQL_FILE):
        """Создает базу и накатывает DDL-скрипт при первом запуске."""
        if not Path(script_path).exists():
            raise FileNotFoundError(f"Файл инициализации {script_path} не найден.")

        conn = cls.get_connection()
        with open(script_path, "r", encoding="utf-8") as f:
            sql_script = f.read()

        cursor = conn.cursor()
        cursor.executescript(sql_script)
        conn.commit()

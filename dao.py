from typing import Any, Dict, List, Optional
from database import Database


class StatusDAO:
    """DAO для работы со справочником статусов."""

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM statuses ORDER BY id ASC;")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(status_id: int) -> Optional[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM statuses WHERE id = ?;", (status_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


class GenreDAO:
    """DAO для работы со справочником жанров."""

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM genres ORDER BY name ASC;")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def insert(name: str) -> int:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO genres (name) VALUES (?);", (name.strip(),))
        conn.commit()
        return cursor.lastrowid


class AuthorDAO:
    """DAO для работы со справочником разработчиков."""

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM authors ORDER BY name ASC;")
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def insert(name: str) -> int:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO authors (name) VALUES (?);", (name.strip(),))
        conn.commit()
        return cursor.lastrowid


class ItemDAO:
    """DAO для работы с играми и связями M:N."""

    SORT_OPTIONS = {
        "newest": "i.id DESC",
        "title_asc": "i.title ASC",
        "year_desc": "i.release_year DESC NULLS LAST",
        "year_asc": "i.release_year ASC NULLS LAST",
        "rating_desc": "i.user_rating DESC NULLS LAST",
        "rating_asc": "i.user_rating ASC NULLS LAST",
    }

    @staticmethod
    def get_by_id(item_id: int) -> Optional[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, release_year, user_rating, status_id, created_at FROM items WHERE id = ?;",
            (item_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        item = dict(row)
        cursor.execute("SELECT genre_id FROM item_genres WHERE item_id = ?;", (item_id,))
        item["genre_ids"] = [r["genre_id"] for r in cursor.fetchall()]

        cursor.execute("SELECT author_id FROM item_authors WHERE item_id = ?;", (item_id,))
        item["author_ids"] = [r["author_id"] for r in cursor.fetchall()]
        return item

    @staticmethod
    def insert(
        title: str,
        release_year: Optional[int],
        user_rating: Optional[int],
        status_id: int,
        genre_ids: List[int],
        author_ids: List[int],
    ) -> int:
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO items (title, release_year, user_rating, status_id)
                VALUES (?, ?, ?, ?);
                """,
                (title, release_year, user_rating, status_id),
            )
            item_id = cursor.lastrowid

            for g_id in genre_ids:
                cursor.execute(
                    "INSERT INTO item_genres (item_id, genre_id) VALUES (?, ?);",
                    (item_id, g_id),
                )

            for a_id in author_ids:
                cursor.execute(
                    "INSERT INTO item_authors (item_id, author_id) VALUES (?, ?);",
                    (item_id, a_id),
                )

            conn.commit()
            return item_id
        except Exception:
            conn.rollback()
            raise

    @staticmethod
    def update(
        item_id: int,
        title: str,
        release_year: Optional[int],
        user_rating: Optional[int],
        status_id: int,
        genre_ids: List[int],
        author_ids: List[int],
    ) -> bool:
        conn = Database.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE items 
                SET title = ?, release_year = ?, user_rating = ?, status_id = ?
                WHERE id = ?;
                """,
                (title, release_year, user_rating, status_id, item_id),
            )
            updated = cursor.rowcount > 0

            cursor.execute("DELETE FROM item_genres WHERE item_id = ?;", (item_id,))
            for g_id in genre_ids:
                cursor.execute(
                    "INSERT INTO item_genres (item_id, genre_id) VALUES (?, ?);",
                    (item_id, g_id),
                )

            cursor.execute("DELETE FROM item_authors WHERE item_id = ?;", (item_id,))
            for a_id in author_ids:
                cursor.execute(
                    "INSERT INTO item_authors (item_id, author_id) VALUES (?, ?);",
                    (item_id, a_id),
                )

            conn.commit()
            return updated
        except Exception:
            conn.rollback()
            raise

    @staticmethod
    def delete(item_id: int) -> bool:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?;", (item_id,))
        conn.commit()
        return cursor.rowcount > 0

    @classmethod
    def get_catalog_view(
        cls,
        search_query: Optional[str] = None,
        status_id: Optional[int] = None,
        genre_id: Optional[int] = None,
        sort_by: str = "newest",
    ) -> List[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()

        order_clause = cls.SORT_OPTIONS.get(sort_by, "i.id DESC")
        sql = f"""
            SELECT 
                i.id,
                i.title,
                i.release_year,
                i.user_rating,
                i.status_id,
                s.name AS status_name,
                COALESCE(GROUP_CONCAT(DISTINCT g.name), '—') AS genres_list,
                COALESCE(GROUP_CONCAT(DISTINCT a.name), '—') AS authors_list
            FROM items i
            INNER JOIN statuses s ON i.status_id = s.id
            LEFT JOIN item_genres ig ON i.id = ig.item_id
            LEFT JOIN genres g ON ig.genre_id = g.id
            LEFT JOIN item_authors ia ON i.id = ia.item_id
            LEFT JOIN authors a ON ia.author_id = a.id
            WHERE 
                (? IS NULL OR i.title LIKE ?)
                AND (? IS NULL OR i.status_id = ?)
                AND (? IS NULL OR i.id IN (SELECT item_id FROM item_genres WHERE genre_id = ?))
            GROUP BY i.id
            ORDER BY {order_clause};
        """
        pattern = f"%{search_query.strip()}%" if search_query else None
        cursor.execute(sql, (pattern, pattern, status_id, status_id, genre_id, genre_id))
        return [dict(row) for row in cursor.fetchall()]


class AnalyticsDAO:
    """DAO для аналитики."""

    @staticmethod
    def get_summary_kpi() -> Dict[str, Any]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS total_items, ROUND(AVG(user_rating), 2) AS average_rating FROM items;")
        row = cursor.fetchone()
        return {
            "total_items": row["total_items"] if row else 0,
            "average_rating": row["average_rating"] if row and row["average_rating"] is not None else 0.0,
        }

    @staticmethod
    def get_status_distribution() -> List[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name AS status_name, COUNT(i.id) AS item_count
            FROM statuses s
            LEFT JOIN items i ON s.id = i.status_id
            GROUP BY s.id, s.name
            ORDER BY s.id ASC;
        """)
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_top_genres(limit: int = 5) -> List[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.name AS name, COUNT(ig.item_id) AS total_items
            FROM genres g
            INNER JOIN item_genres ig ON g.id = ig.genre_id
            GROUP BY g.id, g.name
            ORDER BY total_items DESC LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_top_authors(limit: int = 5) -> List[Dict[str, Any]]:
        conn = Database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.name AS name, COUNT(ia.item_id) AS total_items
            FROM authors a
            INNER JOIN item_authors ia ON a.id = ia.author_id
            GROUP BY a.id, a.name
            ORDER BY total_items DESC LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

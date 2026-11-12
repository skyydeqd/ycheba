import sqlite3
from typing import Any, Dict, List, Optional
from dao import ItemDAO, StatusDAO, GenreDAO, AuthorDAO
from services.exceptions import ValidationError, NotFoundError, DatabaseOperationError


class CatalogService:
    """Сервис бизнес-логики для управления игровой коллекцией."""

    @staticmethod
    def _validate(
        title: str,
        release_year: Optional[int],
        user_rating: Optional[int],
        status_id: int,
        genre_ids: List[int],
        author_ids: List[int],
    ):
        if not title or not title.strip():
            raise ValidationError("Название игры не может быть пустым.")

        if release_year is not None:
            if not isinstance(release_year, int) or release_year < 1970 or release_year > 2030:
                raise ValidationError("Год выхода должен быть целым числом от 1970 до 2030.")

        if user_rating is not None:
            if not isinstance(user_rating, int) or user_rating < 1 or user_rating > 10:
                raise ValidationError("Оценка должна быть целым числом от 1 до 10.")

        if not genre_ids:
            raise ValidationError("Выберите хотя бы один жанр для игры.")

        if not StatusDAO.get_by_id(status_id):
            raise NotFoundError(f"Статус с ID {status_id} не найден.")

        valid_genres = {g["id"] for g in GenreDAO.get_all()}
        for gid in genre_ids:
            if gid not in valid_genres:
                raise NotFoundError(f"Жанр с ID {gid} не существует.")

        valid_authors = {a["id"] for a in AuthorDAO.get_all()}
        for aid in author_ids:
            if aid not in valid_authors:
                raise NotFoundError(f"Разработчик с ID {aid} не существует.")

    @classmethod
    def create_game(
        cls,
        title: str,
        release_year: Optional[int],
        user_rating: Optional[int],
        status_id: int,
        genre_ids: List[int],
        author_ids: Optional[List[int]] = None,
    ) -> int:
        author_ids = author_ids or []
        cls._validate(title, release_year, user_rating, status_id, genre_ids, author_ids)

        try:
            return ItemDAO.insert(
                title=title.strip(),
                release_year=release_year,
                user_rating=user_rating,
                status_id=status_id,
                genre_ids=genre_ids,
                author_ids=author_ids,
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Ошибка БД при сохранении игры: {e}")

    @classmethod
    def update_game(
        cls,
        item_id: int,
        title: str,
        release_year: Optional[int],
        user_rating: Optional[int],
        status_id: int,
        genre_ids: List[int],
        author_ids: Optional[List[int]] = None,
    ) -> bool:
        author_ids = author_ids or []
        if not item_id or item_id <= 0:
            raise ValidationError("Некорректный ID игры.")

        if not ItemDAO.get_by_id(item_id):
            raise NotFoundError(f"Игра с ID {item_id} не найдена.")

        cls._validate(title, release_year, user_rating, status_id, genre_ids, author_ids)

        try:
            return ItemDAO.update(
                item_id=item_id,
                title=title.strip(),
                release_year=release_year,
                user_rating=user_rating,
                status_id=status_id,
                genre_ids=genre_ids,
                author_ids=author_ids,
            )
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Ошибка БД при обновлении игры: {e}")

    @staticmethod
    def delete_game(item_id: int) -> bool:
        if not item_id or item_id <= 0:
            raise ValidationError("Некорректный ID для удаления.")

        if not ItemDAO.get_by_id(item_id):
            raise NotFoundError(f"Игра с ID {item_id} не найдена.")

        try:
            return ItemDAO.delete(item_id)
        except sqlite3.Error as e:
            raise DatabaseOperationError(f"Ошибка БД при удалении игры: {e}")

    @staticmethod
    def get_games(
        search_query: Optional[str] = None,
        status_id: Optional[int] = None,
        genre_id: Optional[int] = None,
        sort_by: str = "newest",
    ) -> List[Dict[str, Any]]:
        return ItemDAO.get_catalog_view(search_query, status_id, genre_id, sort_by)

    @staticmethod
    def get_game_details(item_id: int) -> Dict[str, Any]:
        game = ItemDAO.get_by_id(item_id)
        if not game:
            raise NotFoundError(f"Игра с ID {item_id} не найдена.")
        return game

    @staticmethod
    def add_genre(name: str) -> int:
        if not name or not name.strip():
            raise ValidationError("Название жанра не может быть пустым.")
        try:
            return GenreDAO.insert(name.strip())
        except sqlite3.IntegrityError:
            raise ValidationError("Такой жанр уже существует.")

    @staticmethod
    def add_author(name: str) -> int:
        if not name or not name.strip():
            raise ValidationError("Название разработчика не может быть пустым.")
        try:
            return AuthorDAO.insert(name.strip())
        except sqlite3.IntegrityError:
            raise ValidationError("Такой разработчик уже существует.")

import os
import sqlite3
from database import Database, DB_FILE
from dao import GenreDAO, AuthorDAO, ItemDAO, AnalyticsDAO


def reset_and_seed():
    Database.close_connection()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    Database.initialize_database()

    g_rpg = GenreDAO.insert("RPG")
    g_action = GenreDAO.insert("Экшен")
    g_shooter = GenreDAO.insert("Шутер")
    g_sim = GenreDAO.insert("Симулятор")

    a_cdpr = AuthorDAO.insert("CD Projekt RED")
    a_valve = AuthorDAO.insert("Valve")
    a_fromsoft = AuthorDAO.insert("FromSoftware")
    a_beamng = AuthorDAO.insert("BeamNG GmbH")

    ItemDAO.insert("Cyberpunk 2077", 2020, 9, 3, [g_rpg, g_action], [a_cdpr])
    ItemDAO.insert("Counter-Strike 2", 2023, 8, 2, [g_shooter, g_action], [a_valve])
    ItemDAO.insert("Elden Ring", 2022, 10, 3, [g_rpg, g_action], [a_fromsoft])
    ItemDAO.insert("BeamNG.drive", 2015, 9, 2, [g_sim], [a_beamng])
    ItemDAO.insert("Half-Life 3", 2028, None, 1, [g_shooter], [a_valve])


def print_table(items: list):
    header = f"{'ID':<3} | {'Название':<18} | {'Год':<4} | {'Оценка':<6} | {'Статус':<11} | {'Жанры':<15} | {'Разработчики'}"
    print(header)
    print("-" * len(header))
    for it in items:
        rating = str(it["user_rating"]) if it["user_rating"] is not None else "—"
        year = str(it["release_year"]) if it["release_year"] is not None else "—"
        print(f"{it['id']:<3} | {it['title']:<18} | {year:<4} | {rating:<6} | {it['status_name']:<11} | {it['genres_list']:<15} | {it['authors_list']}")
    print()


if __name__ == "__main__":
    reset_and_seed()
    print("=== Весь каталог (сортировка по оценке) ===")
    print_table(ItemDAO.get_catalog_view(sort_by="rating_desc"))

    print("=== Фильтр: Жанр RPG ===")
    print_table(ItemDAO.get_catalog_view(genre_id=1))

    print("=== Аналитика ===")
    print("KPI:", AnalyticsDAO.get_summary_kpi())
    print("Статусы:", AnalyticsDAO.get_status_distribution())
    print("Топ жанров:", AnalyticsDAO.get_top_genres())

    try:
        ItemDAO.insert("Ошибка", 2020, 15, 1, [], [])
    except sqlite3.IntegrityError:
        print("\n✓ CHECK constraint сработал: оценка > 10 заблокирована.")

    Database.close_connection()

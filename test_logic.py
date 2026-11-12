import os
from database import Database, DB_FILE
from services.catalog_service import CatalogService
from services.analytics_service import AnalyticsService
from services.exceptions import ValidationError, NotFoundError


def run_tests():
    Database.close_connection()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    Database.initialize_database()

    g_rpg = CatalogService.add_genre("RPG")
    g_action = CatalogService.add_genre("Экшен")
    a_cdpr = CatalogService.add_author("CD Projekt RED")

    print("--- 1. Тест создания игры ---")
    game_id = CatalogService.create_game("The Witcher 3", 2015, 10, 3, [g_rpg, g_action], [a_cdpr])
    print(f"✓ Игра создана, ID: {game_id}")

    try:
        CatalogService.create_game("   ", 2020, 8, 1, [g_rpg])
    except ValidationError as e:
        print(f"✓ Ошибка пустого названия перехвачена: {e}")

    try:
        CatalogService.create_game("Тест", 2020, 15, 1, [g_rpg])
    except ValidationError as e:
        print(f"✓ Ошибка оценки > 10 перехвачена: {e}")

    print("\n--- 2. Тест обновления игры ---")
    CatalogService.update_game(game_id, "The Witcher 3: Wild Hunt", 2015, 10, 3, [g_rpg], [a_cdpr])
    print("✓ Игра успешно обновлена")

    try:
        CatalogService.update_game(999, "Призрак", 2020, 5, 1, [g_rpg])
    except NotFoundError as e:
        print(f"✓ Ошибка несуществующего ID перехвачена: {e}")

    print("\n--- 3. Тест статистики ---")
    stats = AnalyticsService.get_statistics()
    print(f"✓ Всего игр: {stats['total_items']}, Средний балл: {stats['average_rating']}")

    print("\n--- 4. Тест удаления ---")
    CatalogService.delete_game(game_id)
    print("✓ Игра удалена")

    empty_stats = AnalyticsService.get_statistics()
    print(f"✓ Статистика на пустой базе без ошибок: всего={empty_stats['total_items']}")

    Database.close_connection()


if __name__ == "__main__":
    run_tests()

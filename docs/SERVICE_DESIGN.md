# Проектирование слоя бизнес-логики (GameTracker)

## 1. Обзор слоя бизнес-логики

Слой бизнес-логики (`services/`) изолирует проверку правил, валидацию данных и координацию транзакций от пользовательского интерфейса и прямых SQL-запросов.

---

## 2. Спецификация бизнес-операций

### Операция 1. Создание игры с привязкой связей (`create_game`)
* **Назначение:** Валидация полей карточки игры, проверка существования выбранных справочников и транзакционное сохранение в БД.
* **Входные данные:** `title: str`, `release_year: int | None`, `user_rating: int | None`, `status_id: int`, `genre_ids: List[int]`, `author_ids: List[int]`.
* **Результат:** `int` (ID новой игры) или исключение `ValidationError` / `NotFoundError`.
* **Используемые DAO:** `StatusDAO.get_by_id`, `GenreDAO.get_all`, `AuthorDAO.get_all`, `ItemDAO.insert`.
* **Проверки и правила:**
  1. Название не может быть пустым (`len(title.strip()) > 0`).
  2. Год выпуска (если указан) в пределах `1970..2030`.
  3. Оценка (если указана) — целое число от `1` до `10`.
  4. Обязательно выбран хотя бы один жанр.
  5. Выбранные статус, жанры и разработчики реально существуют в БД.

#### Псевдокод:
```text
ФУНКЦИЯ create_game(title, year, rating, status_id, genre_ids, author_ids):
    ЕСЛИ Пусто(title): ВЫБРОСИТЬ ValidationError("Введите название игры")
    ЕСЛИ year != NULL И (year < 1970 ИЛИ year > 2030): ВЫБРОСИТЬ ValidationError("Некорректный год")
    ЕСЛИ rating != NULL И (rating < 1 ИЛИ rating > 10): ВЫБРОСИТЬ ValidationError("Оценка от 1 до 10")
    ЕСЛИ Длина(genre_ids) == 0: ВЫБРОСИТЬ ValidationError("Выберите хотя бы один жанр")
    
    ЕСЛИ НЕ СуществуетСтатус(status_id): ВЫБРОСИТЬ NotFoundError("Статус не найден")
    ПРОВЕРИТЬ_СУЩЕСТВОВАНИЕ(genre_ids, author_ids)
    
    ВЕРНУТЬ ItemDAO.insert(title, year, rating, status_id, genre_ids, author_ids)

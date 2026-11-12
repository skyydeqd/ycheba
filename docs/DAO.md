# Спецификация DAO-слоя системы GameTracker

## 1. Архитектура слоя доступа к данным

Слой доступа к данным (DAO) изолирует работу с SQLite от бизнес-логики и графического интерфейса. Все запросы используют параметризацию (`?`) для защиты от SQL-инъекций.

## 2. Стандартные CRUD-методы

### 2.1. StatusDAO (`statuses`)
* `get_all()` $\rightarrow$ `List[Dict]`: `SELECT id, name FROM statuses ORDER BY id ASC;`
* `get_by_id(id)` $\rightarrow$ `Dict | None`: `SELECT id, name FROM statuses WHERE id = ?;`

### 2.2. GenreDAO (`genres`)
* `get_all()` $\rightarrow$ `List[Dict]`: `SELECT id, name FROM genres ORDER BY name ASC;`
* `insert(name)` $\rightarrow$ `int`: `INSERT INTO genres (name) VALUES (?);`
* `delete(id)` $\rightarrow$ `bool`: `DELETE FROM genres WHERE id = ?;`

### 2.3. AuthorDAO (`authors`)
* `get_all()` $\rightarrow$ `List[Dict]`: `SELECT id, name FROM authors ORDER BY name ASC;`
* `insert(name)` $\rightarrow$ `int`: `INSERT INTO authors (name) VALUES (?);`
* `delete(id)` $\rightarrow$ `bool`: `DELETE FROM authors WHERE id = ?;`

### 2.4. ItemDAO (`items`, `item_genres`, `item_authors`)
* `get_by_id(id)` $\rightarrow$ `Dict | None`: `SELECT id, title, release_year, user_rating, status_id, created_at FROM items WHERE id = ?;`
* `insert(title, release_year, user_rating, status_id, genre_ids, author_ids)` $\rightarrow$ `int`: транзакционная вставка в `items`, `item_genres` и `item_authors`.
* `update(item_id, title, release_year, user_rating, status_id, genre_ids, author_ids)` $\rightarrow$ `bool`: обновление полей в `items` и перезапись связей в `item_genres`, `item_authors`.
* `delete(id)` $\rightarrow$ `bool`: `DELETE FROM items WHERE id = ?;` (связи удаляются каскадно).

## 3. SQL-запросы для бизнес-логики и аналитики

### Операция 1. Витрина каталога с поиском, фильтрацией и сортировкой
```sql
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
ORDER BY ...; -- Динамическая подстановка проверенного поля сортировки

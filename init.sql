PRAGMA foreign_keys = ON;

-- 1. Справочник статусов (строго 3 статуса из брифа)
CREATE TABLE IF NOT EXISTS statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 2. Справочник жанров
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 3. Справочник разработчиков / студий
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- 4. Основная таблица игр (без лишних полей)
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK(length(trim(title)) > 0),
    release_year INTEGER CHECK(release_year IS NULL OR (release_year >= 1970 AND release_year <= 2030)),
    user_rating INTEGER CHECK(user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 10)),
    status_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (status_id) REFERENCES statuses(id) ON DELETE RESTRICT
);

-- 5. Связь M:N: Игры <-> Жанры
CREATE TABLE IF NOT EXISTS item_genres (
    item_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, genre_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE RESTRICT
);

-- 6. Связь M:N: Игры <-> Разработчики
CREATE TABLE IF NOT EXISTS item_authors (
    item_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    PRIMARY KEY (item_id, author_id),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE RESTRICT
);

-- 7. Индексы для быстрого поиска, фильтрации и сортировки
CREATE INDEX IF NOT EXISTS idx_items_title ON items(title);
CREATE INDEX IF NOT EXISTS idx_items_status_id ON items(status_id);
CREATE INDEX IF NOT EXISTS idx_items_rating ON items(user_rating);
CREATE INDEX IF NOT EXISTS idx_items_year ON items(release_year);
CREATE INDEX IF NOT EXISTS idx_item_genres_genre_id ON item_genres(genre_id);
CREATE INDEX IF NOT EXISTS idx_item_authors_author_id ON item_authors(author_id);

-- 8. Заполнение справочника статусов
INSERT OR IGNORE INTO statuses (id, name) VALUES
    (1, 'В планах'),
    (2, 'В процессе'),
    (3, 'Завершено');

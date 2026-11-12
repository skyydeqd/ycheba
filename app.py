import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from database import Database
from dao import StatusDAO, GenreDAO, AuthorDAO
from services.catalog_service import CatalogService
from services.analytics_service import AnalyticsService
from services.exceptions import ValidationError, NotFoundError, DatabaseOperationError


class GameFormDialog(tk.Toplevel):
    """SCR-02: Единое модальное окно добавления и редактирования игры."""

    def __init__(self, parent, on_save_callback, game_id: Optional[int] = None):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.game_id = game_id
        self.title("Редактирование игры" if game_id else "Добавление новой игры")
        self.geometry("520x560")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.statuses = StatusDAO.get_all()
        self.genres = []
        self.authors = []

        self._build_ui()
        self._reload_dictionaries()

        if self.game_id is not None:
            self._load_game_data()

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Название
        ttk.Label(main_frame, text="Название игры *:").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var, width=55)
        self.title_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.title_entry.focus()

        # Год и Оценка
        row2 = ttk.Frame(main_frame)
        row2.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(row2, text="Год выхода (1970–2030):").pack(side=tk.LEFT)
        self.year_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.year_var, width=10).pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(row2, text="Оценка:").pack(side=tk.LEFT)
        self.rating_var = tk.StringVar(value="Без оценки")
        rating_values = ["Без оценки"] + [str(i) for i in range(1, 11)]
        ttk.Combobox(row2, textvariable=self.rating_var, values=rating_values, state="readonly", width=12).pack(
            side=tk.LEFT, padx=5
        )

        # Статус
        ttk.Label(main_frame, text="Статус прохождения *:").grid(row=3, column=0, sticky="w", pady=(0, 4))
        self.status_var = tk.StringVar()
        status_names = [s["name"] for s in self.statuses]
        self.status_combo = ttk.Combobox(main_frame, textvariable=self.status_var, values=status_names, state="readonly")
        if status_names:
            self.status_combo.current(0)
        self.status_combo.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # Блок Жанров и Разработчиков
        lists_frame = ttk.Frame(main_frame)
        lists_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        lists_frame.columnconfigure(0, weight=1)
        lists_frame.columnconfigure(1, weight=1)

        # Жанры
        ttk.Label(lists_frame, text="Жанры * (Ctrl/Shift для выбора):").grid(row=0, column=0, sticky="w")
        self.genre_listbox = tk.Listbox(lists_frame, selectmode=tk.MULTIPLE, exportselection=False, height=9)
        self.genre_listbox.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=4)

        add_g_frame = ttk.Frame(lists_frame)
        add_g_frame.grid(row=2, column=0, sticky="ew", padx=(0, 8))
        self.new_genre_var = tk.StringVar()
        ttk.Entry(add_g_frame, textvariable=self.new_genre_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(add_g_frame, text="+ Жанр", width=8, command=self._quick_add_genre).pack(side=tk.RIGHT, padx=(4, 0))

        # Разработчики
        ttk.Label(lists_frame, text="Разработчики / Студии:").grid(row=0, column=1, sticky="w")
        self.author_listbox = tk.Listbox(lists_frame, selectmode=tk.MULTIPLE, exportselection=False, height=9)
        self.author_listbox.grid(row=1, column=1, sticky="nsew", pady=4)

        add_a_frame = ttk.Frame(lists_frame)
        add_a_frame.grid(row=2, column=1, sticky="ew")
        self.new_author_var = tk.StringVar()
        ttk.Entry(add_a_frame, textvariable=self.new_author_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(add_a_frame, text="+ Студия", width=9, command=self._quick_add_author).pack(side=tk.RIGHT, padx=(4, 0))

        # Кнопки Сохранить / Отмена
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=(15, 0))
        ttk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="Сохранить", command=self._save).pack(side=tk.RIGHT)

    def _reload_dictionaries(self, select_genre_id: Optional[int] = None, select_author_id: Optional[int] = None):
        selected_g_ids = {self.genres[i]["id"] for i in self.genre_listbox.curselection()}
        selected_a_ids = {self.authors[i]["id"] for i in self.author_listbox.curselection()}
        if select_genre_id:
            selected_g_ids.add(select_genre_id)
        if select_author_id:
            selected_a_ids.add(select_author_id)

        self.genres = GenreDAO.get_all()
        self.genre_listbox.delete(0, tk.END)
        for idx, g in enumerate(self.genres):
            self.genre_listbox.insert(tk.END, g["name"])
            if g["id"] in selected_g_ids:
                self.genre_listbox.selection_set(idx)

        self.authors = AuthorDAO.get_all()
        self.author_listbox.delete(0, tk.END)
        for idx, a in enumerate(self.authors):
            self.author_listbox.insert(tk.END, a["name"])
            if a["id"] in selected_a_ids:
                self.author_listbox.selection_set(idx)

    def _quick_add_genre(self):
        try:
            new_id = CatalogService.add_genre(self.new_genre_var.get())
            self.new_genre_var.set("")
            self._reload_dictionaries(select_genre_id=new_id)
        except ValidationError as e:
            messagebox.showwarning("Ошибка ввода", str(e), parent=self)

    def _quick_add_author(self):
        try:
            new_id = CatalogService.add_author(self.new_author_var.get())
            self.new_author_var.set("")
            self._reload_dictionaries(select_author_id=new_id)
        except ValidationError as e:
            messagebox.showwarning("Ошибка ввода", str(e), parent=self)

    def _load_game_data(self):
        try:
            game = CatalogService.get_game_details(self.game_id)
            self.title_var.set(game["title"])
            if game["release_year"] is not None:
                self.year_var.set(str(game["release_year"]))
            self.rating_var.set(str(game["user_rating"]) if game["user_rating"] is not None else "Без оценки")

            for idx, s in enumerate(self.statuses):
                if s["id"] == game["status_id"]:
                    self.status_combo.current(idx)
                    break

            for idx, g in enumerate(self.genres):
                if g["id"] in game["genre_ids"]:
                    self.genre_listbox.selection_set(idx)

            for idx, a in enumerate(self.authors):
                if a["id"] in game["author_ids"]:
                    self.author_listbox.selection_set(idx)
        except NotFoundError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            self.destroy()

    def _save(self):
        title = self.title_var.get()

        year_raw = self.year_var.get().strip()
        release_year = None
        if year_raw:
            try:
                release_year = int(year_raw)
            except ValueError:
                messagebox.showerror("Ошибка валидации", "Год выхода должен быть целым числом.", parent=self)
                return

        rating_raw = self.rating_var.get()
        user_rating = None if rating_raw == "Без оценки" else int(rating_raw)

        status_idx = self.status_combo.current()
        status_id = self.statuses[status_idx]["id"] if status_idx >= 0 else 1

        genre_ids = [self.genres[i]["id"] for i in self.genre_listbox.curselection()]
        author_ids = [self.authors[i]["id"] for i in self.author_listbox.curselection()]

        try:
            if self.game_id is None:
                CatalogService.create_game(title, release_year, user_rating, status_id, genre_ids, author_ids)
            else:
                CatalogService.update_game(self.game_id, title, release_year, user_rating, status_id, genre_ids, author_ids)
            self.on_save_callback()
            self.destroy()
        except (ValidationError, NotFoundError, DatabaseOperationError) as e:
            messagebox.showerror("Ошибка сохранения", str(e), parent=self)


class StatisticsDialog(tk.Toplevel):
    """SCR-03: Экран статистики и аналитики коллекции."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Статистика коллекции GameTracker")
        self.geometry("540x460")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ttk.Frame(self, padding=15)
        container.pack(fill=tk.BOTH, expand=True)

        try:
            stats = AnalyticsService.get_statistics()
        except DatabaseOperationError as e:
            messagebox.showerror("Ошибка", str(e), parent=self)
            self.destroy()
            return

        # Карточки KPI
        kpi_frame = ttk.LabelFrame(container, text="Общие показатели", padding=10)
        kpi_frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(
            kpi_frame,
            text=f"Всего игр в коллекции: {stats['total_items']}",
            font=("Segoe UI", 11, "bold"),
        ).pack(side=tk.LEFT, padx=(10, 30))

        ttk.Label(
            kpi_frame,
            text=f"Средняя оценка: {stats['average_rating']} / 10",
            font=("Segoe UI", 11, "bold"),
        ).pack(side=tk.LEFT)

        # Распределение по статусам
        status_frame = ttk.LabelFrame(container, text="Распределение по статусам", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 12))

        for row in stats["status_distribution"]:
            ttk.Label(
                status_frame,
                text=f"• {row['status_name']}: {row['item_count']} игр ({row['percentage']}%)",
            ).pack(anchor="w", pady=2)

        # Топ-5 жанров и разработчиков
        tops_frame = ttk.Frame(container)
        tops_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        tops_frame.columnconfigure(0, weight=1)
        tops_frame.columnconfigure(1, weight=1)

        g_box = ttk.LabelFrame(tops_frame, text="Топ-5 жанров", padding=10)
        g_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        if stats["top_genres"]:
            for idx, g in enumerate(stats["top_genres"], 1):
                ttk.Label(g_box, text=f"{idx}. {g['name']} — {g['total_items']}").pack(anchor="w", pady=2)
        else:
            ttk.Label(g_box, text="Нет данных").pack(anchor="w")

        a_box = ttk.LabelFrame(tops_frame, text="Топ-5 разработчиков", padding=10)
        a_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        if stats["top_authors"]:
            for idx, a in enumerate(stats["top_authors"], 1):
                ttk.Label(a_box, text=f"{idx}. {a['name']} — {a['total_items']}").pack(anchor="w", pady=2)
        else:
            ttk.Label(a_box, text="Нет данных").pack(anchor="w")

        ttk.Button(container, text="← Назад в каталог", command=self.destroy).pack(anchor="e")


class GameTrackerApp(tk.Tk):
    """SCR-01: Главное окно каталога GameTracker."""

    SORT_MAP = {
        "Сначала новые": "newest",
        "По названию (А–Я)": "title_asc",
        "По году (сначала новые)": "year_desc",
        "По году (сначала старые)": "year_asc",
        "По оценке (высокая)": "rating_desc",
        "По оценке (низкая)": "rating_asc",
    }

    def __init__(self):
        super().__init__()
        self.title("GameTracker — Менеджер игровой коллекции")
        self.geometry("960x560")
        self.minsize(820, 480)

        self._init_storage()
        self._build_ui()
        self._refresh_filters()
        self._load_table()

    def _init_storage(self):
        try:
            Database.initialize_database()
            # Если справочники пустые при самом первом запуске — добавляем базовые жанры и студии
            if not GenreDAO.get_all():
                for g in ["RPG", "Экшен", "Шутер", "Стратегия", "Симулятор"]:
                    GenreDAO.insert(g)
            if not AuthorDAO.get_all():
                for a in ["Valve", "CD Projekt RED", "FromSoftware", "Rockstar Games"]:
                    AuthorDAO.insert(a)
        except Exception as e:
            messagebox.showerror("Критическая ошибка БД", f"Не удалось инициализировать базу данных:\n{e}")
            self.destroy()

    def _build_ui(self):
        # Верхняя панель поиска и фильтров
        top_bar = ttk.Frame(self, padding=(12, 10))
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_table())
        ttk.Entry(top_bar, textvariable=self.search_var, width=24).pack(side=tk.LEFT, padx=(5, 12))

        ttk.Label(top_bar, text="Жанр:").pack(side=tk.LEFT)
        self.genre_filter_var = tk.StringVar(value="Все жанры")
        self.genre_filter_combo = ttk.Combobox(top_bar, textvariable=self.genre_filter_var, state="readonly", width=15)
        self.genre_filter_combo.pack(side=tk.LEFT, padx=(5, 12))
        self.genre_filter_combo.bind("<<ComboboxSelected>>", lambda _: self._load_table())

        ttk.Label(top_bar, text="Статус:").pack(side=tk.LEFT)
        self.status_filter_var = tk.StringVar(value="Все статусы")
        self.status_filter_combo = ttk.Combobox(top_bar, textvariable=self.status_filter_var, state="readonly", width=15)
        self.status_filter_combo.pack(side=tk.LEFT, padx=(5, 12))
        self.status_filter_combo.bind("<<ComboboxSelected>>", lambda _: self._load_table())

        ttk.Label(top_bar, text="Сортировка:").pack(side=tk.LEFT)
        self.sort_var = tk.StringVar(value="Сначала новые")
        sort_combo = ttk.Combobox(
            top_bar, textvariable=self.sort_var, values=list(self.SORT_MAP.keys()), state="readonly", width=22
        )
        sort_combo.pack(side=tk.LEFT, padx=(5, 8))
        sort_combo.bind("<<ComboboxSelected>>", lambda _: self._load_table())

        ttk.Button(top_bar, text="Сброс", command=self._reset_filters).pack(side=tk.LEFT)

        # Таблица каталога
        table_frame = ttk.Frame(self, padding=(12, 0))
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "title", "year", "genres", "authors", "status", "rating")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Название игры")
        self.tree.heading("year", text="Год")
        self.tree.heading("genres", text="Жанры")
        self.tree.heading("authors", text="Разработчики")
        self.tree.heading("status", text="Статус")
        self.tree.heading("rating", text="Оценка")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("title", width=220, anchor="w")
        self.tree.column("year", width=65, anchor="center")
        self.tree.column("genres", width=170, anchor="w")
        self.tree.column("authors", width=170, anchor="w")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("rating", width=70, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Нижняя панель кнопок
        bottom_bar = ttk.Frame(self, padding=(12, 10))
        bottom_bar.pack(fill=tk.X)

        ttk.Button(bottom_bar, text="+ Добавить", command=self._open_add_dialog).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bottom_bar, text="Редактировать", command=self._open_edit_dialog).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bottom_bar, text="Удалить", command=self._delete_selected).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(bottom_bar, text="Статистика", command=self._open_stats).pack(side=tk.LEFT, padx=(15, 0))

        self.status_bar_var = tk.StringVar(value="Готово")
        ttk.Label(bottom_bar, textvariable=self.status_bar_var).pack(side=tk.RIGHT)

    def _refresh_filters(self):
        self.genres_map = {g["name"]: g["id"] for g in GenreDAO.get_all()}
        self.genre_filter_combo["values"] = ["Все жанры"] + list(self.genres_map.keys())

        self.statuses_map = {s["name"]: s["id"] for s in StatusDAO.get_all()}
        self.status_filter_combo["values"] = ["Все статусы"] + list(self.statuses_map.keys())

    def _reset_filters(self):
        self.search_var.set("")
        self.genre_filter_var.set("Все жанры")
        self.status_filter_var.set("Все статусы")
        self.sort_var.set("Сначала новые")
        self._load_table()

    def _load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        search_q = self.search_var.get().strip() or None
        genre_id = self.genres_map.get(self.genre_filter_var.get())
        status_id = self.statuses_map.get(self.status_filter_var.get())
        sort_key = self.SORT_MAP.get(self.sort_var.get(), "newest")

        try:
            games = CatalogService.get_games(
                search_query=search_q,
                status_id=status_id,
                genre_id=genre_id,
                sort_by=sort_key,
            )
            for g in games:
                year_str = str(g["release_year"]) if g["release_year"] is not None else "—"
                rating_str = str(g["user_rating"]) if g["user_rating"] is not None else "—"
                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        g["id"],
                        g["title"],
                        year_str,
                        g["genres_list"],
                        g["authors_list"],
                        g["status_name"],
                        rating_str,
                    ),
                )
            self.status_bar_var.set(f"Найдено игр: {len(games)}")
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить каталог:\n{e}")

    def _get_selected_game_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Подсказка", "Выберите игру в таблице.")
            return None
        values = self.tree.item(selected[0], "values")
        return int(values[0])

    def _on_form_saved(self):
        self._refresh_filters()
        self._load_table()

    def _open_add_dialog(self):
        GameFormDialog(self, on_save_callback=self._on_form_saved)

    def _open_edit_dialog(self):
        game_id = self._get_selected_game_id()
        if game_id is not None:
            GameFormDialog(self, on_save_callback=self._on_form_saved, game_id=game_id)

    def _delete_selected(self):
        game_id = self._get_selected_game_id()
        if game_id is None:
            return

        selected = self.tree.selection()[0]
        game_title = self.tree.item(selected, "values")[1]

        if messagebox.askyesno("Подтверждение удаления", f"Удалить игру «{game_title}» из коллекции?"):
            try:
                CatalogService.delete_game(game_id)
                self._load_table()
                self.status_bar_var.set(f"Игра «{game_title}» удалена")
            except (ValidationError, NotFoundError, DatabaseOperationError) as e:
                messagebox.showerror("Ошибка удаления", str(e))

    def _open_stats(self):
        StatisticsDialog(self)


if __name__ == "__main__":
    app = GameTrackerApp()
    app.mainloop()
    Database.close_connection()

class BusinessLogicError(Exception):
    """Базовое исключение бизнес-логики."""
    pass


class ValidationError(BusinessLogicError):
    """Ошибка некорректных входных данных."""
    pass


class NotFoundError(BusinessLogicError):
    """Запись не найдена в базе данных."""
    pass


class DatabaseOperationError(BusinessLogicError):
    """Системный сбой при работе с БД."""
    pass

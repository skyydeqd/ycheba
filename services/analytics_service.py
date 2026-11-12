from typing import Any, Dict
from dao import AnalyticsDAO
from services.exceptions import DatabaseOperationError


class AnalyticsService:
    """Сервис бизнес-логики для расчёта статистики коллекции."""

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        try:
            kpi = AnalyticsDAO.get_summary_kpi()
            statuses = AnalyticsDAO.get_status_distribution()
            top_genres = AnalyticsDAO.get_top_genres(limit=5)
            top_authors = AnalyticsDAO.get_top_authors(limit=5)
        except Exception as e:
            raise DatabaseOperationError(f"Сбой при расчёте статистики: {e}")

        total = kpi.get("total_items", 0)
        avg_rating = float(kpi["average_rating"]) if kpi.get("average_rating") is not None else 0.0

        status_stats = []
        for row in statuses:
            count = row["item_count"]
            percent = round((count / total) * 100, 1) if total > 0 else 0.0
            status_stats.append({
                "status_name": row["status_name"],
                "item_count": count,
                "percentage": percent,
            })

        return {
            "total_items": total,
            "average_rating": avg_rating,
            "status_distribution": status_stats,
            "top_genres": top_genres,
            "top_authors": top_authors,
        }

from datetime import date, timedelta

from backend.fitness_data_service import get_user_daily_history


def get_progress_summary(user_id: str, days: int = 7):
    records = get_user_daily_history(user_id, days)
    totals = {
        "steps": sum(int(record.get("steps", 0) or 0) for record in records),
        "water": sum(int(record.get("water", 0) or 0) for record in records),
        "calories": sum(int(record.get("calories", 0) or 0) for record in records),
        "workout_minutes": sum(int(record.get("workout_minutes", 0) or 0) for record in records),
    }
    workouts_completed = sum(
        1 for record in records if bool(record.get("workout_completed")) or (int(record.get("workout_minutes", 0) or 0) > 0)
    )
    daily = []
    for record in records:
        daily.append({
            "date": record.get("date"),
            "steps": int(record.get("steps", 0) or 0),
            "water": int(record.get("water", 0) or 0),
            "calories": int(record.get("calories", 0) or 0),
            "workout_minutes": int(record.get("workout_minutes", 0) or 0),
            "goal_status": record.get("goal_status") or "On track",
        })

    goal_progress = {
        "steps_goal": 8000,
        "water_goal": 8,
        "calories_goal": 2000,
        "workout_goal": 30,
    }

    return {
        "user_id": user_id,
        "days": max(1, int(days or 7)),
        "totals": totals,
        "daily": daily,
        "workouts_completed": workouts_completed,
        "goal_progress": goal_progress,
        "average_steps_per_day": round(totals["steps"] / max(len(records), 1), 2),
        "average_water_per_day": round(totals["water"] / max(len(records), 1), 2),
    }

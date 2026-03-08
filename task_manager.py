from datetime import datetime, date
import re

PROJECTS = {
    1: {"deadline": datetime(2099, 12, 31)},
    2: {"deadline": datetime(2020, 1, 1)},
    3: {"deadline": datetime.now()},
}

TASKS = {}
TASK_COUNTER = 1


def project_exists(project_id: int) -> bool:
    return project_id in PROJECTS


def task_exists(task_id: int) -> bool:
    return task_id in TASKS


def get_project_deadline(project_id: int):
    if not project_exists(project_id):
        return None
    return PROJECTS[project_id].get("deadline")


def insert_task(project_id: int, title: str, deadline: datetime) -> int:
    global TASK_COUNTER

    task_id = TASK_COUNTER
    TASKS[task_id] = {
        "project_id": project_id,
        "title": title,
        "deadline": deadline,
        "hours": 0.0,
    }
    TASK_COUNTER += 1
    return task_id


def update_task_hours(task_id: int, hours: float) -> float:
    if not task_exists(task_id):
        raise ValueError("Task does not exist")

    TASKS[task_id]["hours"] += hours
    return TASKS[task_id]["hours"]


def smtp_send(email: str, task_info: dict) -> bool:
    return True


def create_task(project_id: int, title: str, deadline: datetime) -> int:
    if not project_exists(project_id):
        raise ValueError("Project does not exist")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Title cannot be empty")

    if not isinstance(deadline, datetime):
        raise ValueError("Deadline must be datetime")

    if deadline <= datetime.now():
        raise ValueError("Deadline cannot be in the past")

    return insert_task(project_id, title, deadline)


def track_time(task_id: int, hours: float) -> float:
    if not task_exists(task_id):
        raise ValueError("Task does not exist")

    if hours < 0:
        raise ValueError("Hours cannot be negative")

    if hours > 1000000:
        raise ValueError("Hours value is too large")

    return update_task_hours(task_id, hours)


def calculate_invoice(hours: float, rate: float, currency: str) -> float:
    supported_currencies = {"USD", "EUR", "RUB"}

    if hours < 0:
        raise ValueError("Hours cannot be negative")

    if rate < 0:
        raise ValueError("Rate cannot be negative")

    if currency not in supported_currencies:
        raise ValueError("Unsupported currency")

    return round(hours * rate, 2)


def check_project_deadline(project_id: int) -> bool:
    deadline = get_project_deadline(project_id)

    if deadline is None:
        raise LookupError("Project not found")

    today = datetime.now().date()

    if isinstance(deadline, datetime):
        return deadline.date() >= today

    if isinstance(deadline, date):
        return deadline >= today

    raise TypeError("Invalid deadline type")


def send_task_notification(email: str, task_info: dict) -> bool:
    if not isinstance(email, str) or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise ValueError("Invalid email")

    if not isinstance(task_info, dict):
        raise ValueError("Task info must be a dictionary")

    return smtp_send(email, task_info)
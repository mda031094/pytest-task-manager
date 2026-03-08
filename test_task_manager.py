from __future__ import annotations

import importlib
import os
from datetime import date, datetime, timedelta

import pytest


MODULE_NAME = os.getenv("TASK_MANAGER_MODULE", "task_manager")
service = importlib.import_module(MODULE_NAME)


@pytest.fixture
def future_deadline() -> datetime:
    return datetime.now() + timedelta(days=3)


@pytest.fixture
def past_deadline() -> datetime:
    return datetime.now() - timedelta(days=1)


@pytest.fixture
def today_date() -> date:
    return date.today()



#create_task tests

@pytest.mark.parametrize(
    "project_id,title",
    [
        (1, "Prepare release notes"),
        (22, "Fix payment bug"),
    ],
)
def test_create_task_positive_returns_task_id(monkeypatch, future_deadline, project_id, title):
    monkeypatch.setattr(service, "project_exists", lambda pid: pid == project_id)
    monkeypatch.setattr(service, "insert_task", lambda pid, t, d: 101)

    result = service.create_task(project_id, title, future_deadline)

    assert result == 101


@pytest.mark.parametrize(
    "title",
    ["Task A", "Task B with details"],
)
def test_create_task_positive_passes_arguments_to_insert(monkeypatch, future_deadline, title):
    captured = {}

    monkeypatch.setattr(service, "project_exists", lambda pid: True)

    def fake_insert(project_id, passed_title, deadline):
        captured["project_id"] = project_id
        captured["title"] = passed_title
        captured["deadline"] = deadline
        return 777

    monkeypatch.setattr(service, "insert_task", fake_insert)

    result = service.create_task(9, title, future_deadline)

    assert result == 777
    assert captured == {
        "project_id": 9,
        "title": title,
        "deadline": future_deadline,
    }


@pytest.mark.parametrize("bad_title", ["", "   "])
def test_create_task_negative_rejects_empty_title(monkeypatch, future_deadline, bad_title):
    monkeypatch.setattr(service, "project_exists", lambda pid: True)

    with pytest.raises((ValueError, AssertionError)):
        service.create_task(1, bad_title, future_deadline)


@pytest.mark.parametrize(
    "project_id,deadline",
    [
        (999, datetime.now() + timedelta(days=2)),
        (1, datetime.now() - timedelta(days=1)),
    ],
)
def test_create_task_negative_rejects_unknown_project_or_past_deadline(monkeypatch, project_id, deadline):
    monkeypatch.setattr(service, "project_exists", lambda pid: pid != 999)

    with pytest.raises((ValueError, LookupError, AssertionError)):
        service.create_task(project_id, "Valid title", deadline)



#track_time tests

@pytest.mark.parametrize("hours", [1.5, 8.0])
def test_track_time_positive_adds_hours(monkeypatch, hours):
    monkeypatch.setattr(service, "task_exists", lambda task_id: True)
    monkeypatch.setattr(service, "update_task_hours", lambda task_id, h: 10 + h)

    result = service.track_time(15, hours)

    assert result == 10 + hours


@pytest.mark.parametrize("hours", [0.0, 1000.0])
def test_track_time_positive_accepts_boundary_valid_values(monkeypatch, hours):
    monkeypatch.setattr(service, "task_exists", lambda task_id: True)
    monkeypatch.setattr(service, "update_task_hours", lambda task_id, h: h)

    result = service.track_time(33, hours)

    assert result == hours


@pytest.mark.parametrize("hours", [-0.1, -5.0])
def test_track_time_negative_rejects_negative_hours(monkeypatch, hours):
    monkeypatch.setattr(service, "task_exists", lambda task_id: True)

    with pytest.raises((ValueError, AssertionError)):
        service.track_time(15, hours)


@pytest.mark.parametrize("task_id", [404, 9999])
def test_track_time_negative_rejects_missing_task(monkeypatch, task_id):
    monkeypatch.setattr(service, "task_exists", lambda current_task_id: False)

    with pytest.raises((ValueError, LookupError, AssertionError)):
        service.track_time(task_id, 2.5)



# calculate_invoice tests

@pytest.mark.parametrize(
    "hours,rate,currency,expected",
    [
        (10, 100, "USD", 1000.0),
        (2.5, 80, "EUR", 200.0),
    ],
)
def test_calculate_invoice_positive_regular_cases(hours, rate, currency, expected):
    assert service.calculate_invoice(hours, rate, currency) == pytest.approx(expected, rel=1e-6)


@pytest.mark.parametrize(
    "hours,rate,currency,expected",
    [
        (0, 100, "USD", 0.0),
        (3.333, 19.99, "USD", 66.63),
    ],
)
def test_calculate_invoice_positive_boundary_and_rounding(hours, rate, currency, expected):
    assert service.calculate_invoice(hours, rate, currency) == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize(
    "hours,rate,currency",
    [
        (5, 100, "BTC"),
        (4, 90, "ABC"),
    ],
)
def test_calculate_invoice_negative_rejects_unknown_currency(hours, rate, currency):
    with pytest.raises((ValueError, KeyError, AssertionError)):
        service.calculate_invoice(hours, rate, currency)


@pytest.mark.parametrize(
    "hours,rate,currency",
    [
        (-1, 100, "USD"),
        (8, -50, "EUR"),
    ],
)
def test_calculate_invoice_negative_rejects_negative_values(hours, rate, currency):
    with pytest.raises((ValueError, AssertionError)):
        service.calculate_invoice(hours, rate, currency)



#check_project_deadline tests


@pytest.mark.parametrize(
    "deadline",
    [
        date.today(),
        date.today() + timedelta(days=1),
    ],
)
def test_check_project_deadline_positive_today_or_future(monkeypatch, deadline):
    monkeypatch.setattr(service, "get_project_deadline", lambda project_id: deadline)

    result = service.check_project_deadline(10)

    assert result is True


@pytest.mark.parametrize(
    "deadline",
    [
        datetime.now(),
        datetime.now() + timedelta(hours=5),
    ],
)
def test_check_project_deadline_positive_supports_datetime(monkeypatch, deadline):
    monkeypatch.setattr(service, "get_project_deadline", lambda project_id: deadline)

    result = service.check_project_deadline(20)

    assert result is True


@pytest.mark.parametrize(
    "deadline",
    [
        date.today() - timedelta(days=1),
        datetime.now() - timedelta(days=2),
    ],
)
def test_check_project_deadline_negative_expired(monkeypatch, deadline):
    monkeypatch.setattr(service, "get_project_deadline", lambda project_id: deadline)

    result = service.check_project_deadline(30)

    assert result is False


@pytest.mark.parametrize("project_id", [404, 999])
def test_check_project_deadline_negative_missing_project(monkeypatch, project_id):
    monkeypatch.setattr(service, "get_project_deadline", lambda current_project_id: None)

    with pytest.raises((ValueError, LookupError, TypeError, AssertionError)):
        service.check_project_deadline(project_id)



#send_task_notification tests


@pytest.mark.parametrize(
    "email,task_info",
    [
        ("user@example.com", {"id": 1, "status": "created", "title": "Task A"}),
        ("manager@test.org", {"id": 2, "status": "completed", "title": "Task B"}),
    ],
)
def test_send_task_notification_positive_sends_email(monkeypatch, email, task_info):
    monkeypatch.setattr(service, "smtp_send", lambda recipient, payload: True)

    result = service.send_task_notification(email, task_info)

    assert result is True


@pytest.mark.parametrize(
    "task_info",
    [
        {"id": 3, "status": "overdue", "title": "Task C"},
        {"id": 4, "status": "created", "title": "Task D", "project": "Internal"},
    ],
)
def test_send_task_notification_positive_passes_task_info(monkeypatch, task_info):
    captured = {}

    def fake_smtp_send(email, payload):
        captured["email"] = email
        captured["payload"] = payload
        return True

    monkeypatch.setattr(service, "smtp_send", fake_smtp_send)

    result = service.send_task_notification("notify@example.com", task_info)

    assert result is True
    assert captured["email"] == "notify@example.com"
    assert captured["payload"] == task_info


@pytest.mark.parametrize("bad_email", ["plainaddress", "user@", "@mail.com"])
def test_send_task_notification_negative_invalid_email(monkeypatch, bad_email):
    monkeypatch.setattr(service, "smtp_send", lambda recipient, payload: True)

    with pytest.raises((ValueError, AssertionError)):
        service.send_task_notification(bad_email, {"id": 1, "status": "created"})


def test_send_task_notification_negative_smtp_failure(monkeypatch):
    def fake_smtp_send(email, payload):
        raise ConnectionError("SMTP server is unavailable")

    monkeypatch.setattr(service, "smtp_send", fake_smtp_send)

    with pytest.raises((ConnectionError, RuntimeError, ValueError)):
        service.send_task_notification(
            "user@example.com",
            {"id": 1, "status": "created", "title": "Task A"},
        )

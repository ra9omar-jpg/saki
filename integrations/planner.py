import requests
from config import config
from integrations.teams import _graph_headers

_REQUEST_TIMEOUT = 15


def get_tasks(plan_id: str) -> list[dict]:
    url = f"https://graph.microsoft.com/v1.0/planner/plans/{plan_id}/tasks"
    r = requests.get(url, headers=_graph_headers(), timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json().get("value", [])


def get_task_details(task_id: str) -> dict:
    url = f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}/details"
    r = requests.get(url, headers=_graph_headers(), timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def get_buckets(plan_id: str) -> list[dict]:
    url = f"https://graph.microsoft.com/v1.0/planner/plans/{plan_id}/buckets"
    r = requests.get(url, headers=_graph_headers(), timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json().get("value", [])


def update_task_status(task_id: str, etag: str, percent_complete: int, preview_type: str = None) -> dict:
    url = f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}"
    headers = _graph_headers()
    headers["If-Match"] = etag
    payload = {"percentComplete": percent_complete}
    if preview_type:
        payload["previewType"] = preview_type
    r = requests.patch(url, json=payload, headers=headers, timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json() if r.text else {}


def get_task_etag(task_id: str) -> str:
    url = f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}"
    r = requests.get(url, headers=_graph_headers(), timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.headers.get("ETag", "")


def move_task_to_bucket(task_id: str, etag: str, bucket_id: str) -> dict:
    url = f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}"
    headers = _graph_headers()
    headers["If-Match"] = etag
    r = requests.patch(url, json={"bucketId": bucket_id}, headers=headers, timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json() if r.text else {}


def add_task_note(task_id: str, etag: str, note: str) -> dict:
    url = f"https://graph.microsoft.com/v1.0/planner/tasks/{task_id}/details"
    headers = _graph_headers()
    headers["If-Match"] = etag
    r = requests.patch(url, json={"description": note}, headers=headers, timeout=_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json() if r.text else {}


def get_tasks_in_bucket(plan_id: str, bucket_id: str) -> list[dict]:
    all_tasks = get_tasks(plan_id)
    return [t for t in all_tasks if t.get("bucketId") == bucket_id]


def get_assigned_tasks(plan_id: str, user_id: str) -> list[dict]:
    all_tasks = get_tasks(plan_id)
    return [t for t in all_tasks if user_id in t.get("assignments", {})]


def sync_tasks_to_db(plan_id: str, app_context) -> None:
    from database.models import Task, TeamMember
    from database.db import db
    from datetime import datetime

    with app_context():
        tasks = get_tasks(plan_id)
        for t in tasks:
            existing = Task.query.filter_by(planner_id=t["id"]).first()
            assigned_to_id = None
            assignments = t.get("assignments", {})
            if assignments:
                first_user_id = next(iter(assignments))
                member = TeamMember.query.filter_by(teams_user_id=first_user_id).first()
                if member:
                    assigned_to_id = member.id

            percent = t.get("percentComplete", 0)
            if percent == 0:
                status = "not_started"
            elif percent == 100:
                status = "done"
            else:
                status = "in_progress"

            due_date = None
            if t.get("dueDateTime"):
                try:
                    due_date = datetime.fromisoformat(t["dueDateTime"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    due_date = None

            if existing:
                existing.status = status
                existing.assigned_to_id = assigned_to_id
                existing.bucket = t.get("bucketId")
                existing.due_date = due_date
                existing.planner_updated_at = datetime.utcnow()
                existing.last_synced_at = datetime.utcnow()
            else:
                task = Task(
                    planner_id=t["id"],
                    title=t.get("title", "Unavngivet opgave"),
                    assigned_to_id=assigned_to_id,
                    status=status,
                    bucket=t.get("bucketId"),
                    due_date=due_date,
                    plan_id=plan_id,
                    last_synced_at=datetime.utcnow(),
                )
                db.session.add(task)

        db.session.commit()

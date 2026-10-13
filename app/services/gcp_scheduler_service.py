import asyncio
import json

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import scheduler_v1

from app.core.config import settings

VALID_SCHEDULE_INTERVALS = [10, 60, 120, 180]  # 분 단위: 10분/1시간/2시간/3시간


def _client() -> scheduler_v1.CloudSchedulerClient:
    return scheduler_v1.CloudSchedulerClient()


def _parent() -> str:
    return f"projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_LOCATION}"


def _job_name(admin_id: str) -> str:
    return f"{_parent()}/jobs/drug-crawl-admin-{admin_id}"


def _cron(schedule_interval: int) -> str:
    if schedule_interval < 60:
        return f"*/{schedule_interval} * * * *"
    hours = schedule_interval // 60
    if hours == 1:
        return "0 * * * *"
    return f"0 */{hours} * * *"


def _build_job(admin_id: str, schedule_interval: int) -> scheduler_v1.Job:
    if not settings.CLOUD_RUN_URL.startswith("https://"):
        raise ValueError("CLOUD_RUN_URL은 HTTPS여야 합니다")
    trigger_url = f"{settings.CLOUD_RUN_URL}/crawl/trigger"
    body = json.dumps({"admin_id": admin_id}).encode("utf-8")

    return scheduler_v1.Job(
        name=_job_name(admin_id),
        schedule=_cron(schedule_interval),
        time_zone="Asia/Seoul",
        http_target=scheduler_v1.HttpTarget(
            uri=trigger_url,
            http_method=scheduler_v1.HttpMethod.POST,
            body=body,
            headers={
                "Content-Type": "application/json",
                "X-Internal-Key": settings.INTERNAL_API_KEY,
            },
        ),
    )


def _create_job_sync(admin_id: str, schedule_interval: int) -> None:
    client = _client()
    job = _build_job(admin_id, schedule_interval)
    try:
        client.create_job(parent=_parent(), job=job)
    except AlreadyExists:
        _update_job_sync(admin_id, schedule_interval)


def _update_job_sync(admin_id: str, schedule_interval: int) -> None:
    client = _client()
    job = _build_job(admin_id, schedule_interval)
    client.update_job(
        job=job,
        update_mask={"paths": ["schedule", "http_target"]},
    )


def _delete_job_sync(admin_id: str) -> None:
    client = _client()
    try:
        client.delete_job(name=_job_name(admin_id))
    except NotFound:
        pass


async def create_job(admin_id: str, schedule_interval: int) -> None:
    await asyncio.to_thread(_create_job_sync, admin_id, schedule_interval)


async def update_job(admin_id: str, schedule_interval: int) -> None:
    await asyncio.to_thread(_update_job_sync, admin_id, schedule_interval)


async def delete_job(admin_id: str) -> None:
    await asyncio.to_thread(_delete_job_sync, admin_id)

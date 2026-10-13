"""
GCP Cloud Scheduler 연동 서비스

관리자별 크롤링 job을 자동으로 생성/수정/삭제한다.
각 job은 POST /crawl/trigger 를 admin_id와 함께 호출한다.
"""

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
    """분 단위 주기를 cron 표현식으로 변환."""
    if schedule_interval < 60:
        return f"*/{schedule_interval} * * * *"
    hours = schedule_interval // 60
    if hours == 1:
        return "0 * * * *"
    return f"0 */{hours} * * *"


def _build_job(admin_id: str, schedule_interval: int) -> scheduler_v1.Job:
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


def create_job(admin_id: str, schedule_interval: int) -> None:
    """관리자 크롤링 job 생성. 이미 존재하면 업데이트."""
    client = _client()
    job = _build_job(admin_id, schedule_interval)
    try:
        client.create_job(parent=_parent(), job=job)
    except AlreadyExists:
        update_job(admin_id, schedule_interval)


def update_job(admin_id: str, schedule_interval: int) -> None:
    """관리자 크롤링 job 스케줄 수정."""
    client = _client()
    job = _build_job(admin_id, schedule_interval)
    client.update_job(
        job=job,
        update_mask={"paths": ["schedule", "http_target"]},
    )


def delete_job(admin_id: str) -> None:
    """관리자 크롤링 job 삭제. 없으면 무시."""
    client = _client()
    try:
        client.delete_job(name=_job_name(admin_id))
    except NotFound:
        pass

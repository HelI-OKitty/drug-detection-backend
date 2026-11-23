"""
Google Cloud Storage 이미지 업로드 및 Signed URL 서비스

Cloud Run의 서비스 계정 ADC(Application Default Credentials)를 사용하므로
별도 인증 설정 없이 동작한다. (서비스 계정에 Storage Object Creator 권한 필요)

저장 형식: gs://{bucket}/{object_name}
조회 형식: Signed URL (시간 제한 임시 URL, 기본 1시간 유효)
"""

import asyncio
import base64
import datetime
import logging

import google.auth
import google.auth.transport.requests
from google.cloud import storage

from app.core.config import settings

logger = logging.getLogger(__name__)

_GCS_PREFIX = f"gs://{settings.GCS_BUCKET_NAME}/"


def _upload_sync(image_bytes: bytes, object_name: str) -> None:
    """GCS에 이미지 업로드 (동기 함수)"""
    client = storage.Client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")


def _generate_signed_url_sync(object_name: str, expiration_minutes: int) -> str:
    """GCS 객체에 대한 Signed URL 생성 (동기 함수)

    Cloud Run 서비스 계정의 ADC를 사용해 서명한다.
    서비스 계정에 iam.serviceAccounts.signBlob 권한이 있어야 한다.
    """
    credentials, _ = google.auth.default()
    auth_request = google.auth.transport.requests.Request()
    credentials.refresh(auth_request)

    client = storage.Client(credentials=credentials)
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)

    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="GET",
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
    )


async def upload_image_to_gcs(b64: str, source_id: str, index: int) -> str:
    """base64 이미지를 GCS에 업로드하고 gs:// URI 반환

    저장 경로: detections/{source_id}/{index}.jpg
    반환값: gs://{bucket}/detections/{source_id}/{index}.jpg
    """
    image_bytes = base64.b64decode(b64)
    object_name = f"detections/{source_id}/{index}.jpg"
    await asyncio.to_thread(_upload_sync, image_bytes, object_name)
    return f"{_GCS_PREFIX}{object_name}"


async def resolve_image_url(image_url: str, expiration_minutes: int = 60) -> str:
    """gs:// URI를 Signed URL로 변환, 외부 URL은 그대로 반환

    - gs:// URI: GCS Signed URL 생성 (기본 1시간 유효)
    - 그 외 (기존 X CDN URL 등): 변환 없이 그대로 반환
    """
    if not image_url.startswith(_GCS_PREFIX):
        return image_url
    object_name = image_url[len(_GCS_PREFIX) :]
    return await asyncio.to_thread(
        _generate_signed_url_sync, object_name, expiration_minutes
    )

"""
Google Cloud Storage 이미지 업로드 서비스

Cloud Run의 서비스 계정 ADC(Application Default Credentials)를 사용하므로
별도 인증 설정 없이 동작한다. (서비스 계정에 Storage Object Creator 권한 필요)
"""

import asyncio
import base64
import logging

from google.cloud import storage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _upload_sync(image_bytes: bytes, object_name: str) -> str:
    """GCS에 이미지 업로드 후 public URL 반환 (동기 함수)"""
    client = storage.Client()
    bucket = client.bucket(settings.GCS_BUCKET_NAME)
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_bytes, content_type="image/jpeg")
    return f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{object_name}"


async def upload_image_to_gcs(b64: str, source_id: str, index: int) -> str:
    """base64 이미지를 GCS에 업로드하고 public URL 반환

    저장 경로: detections/{source_id}/{index}.jpg
    """
    image_bytes = base64.b64decode(b64)
    object_name = f"detections/{source_id}/{index}.jpg"
    return await asyncio.to_thread(_upload_sync, image_bytes, object_name)

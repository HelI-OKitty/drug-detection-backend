from bson import ObjectId
from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.db.mongo import db
from app.schemas.admin import AdminOut, AdminUpdate


def _doc_to_admin_out(doc: dict) -> AdminOut:
    return AdminOut(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        site_url=doc.get("site_url"),
        notification_enabled=doc.get("notification_enabled", False),
        notification_email=doc.get("notification_email"),
        created_at=doc["created_at"],
    )


async def _get_doc(admin_id: str) -> dict:
    try:
        oid = ObjectId(admin_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다.",
        )
    doc = await db.admins.find_one({"_id": oid})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다.",
        )
    return doc


async def get_profile(admin_id: str) -> AdminOut:
    doc = await _get_doc(admin_id)
    return _doc_to_admin_out(doc)


async def update_profile(admin_id: str, data: AdminUpdate) -> AdminOut:
    doc = await _get_doc(admin_id)

    if data.new_password:
        if not verify_password(data.current_password, doc["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="현재 비밀번호가 올바르지 않습니다.",
            )

    update_fields: dict = {}
    if data.name is not None:
        update_fields["name"] = data.name
    if data.new_password is not None:
        update_fields["password"] = hash_password(data.new_password)
    if data.site_url is not None:
        update_fields["site_url"] = data.site_url
    if data.notification_enabled is not None:
        update_fields["notification_enabled"] = data.notification_enabled
    if data.notification_email is not None:
        update_fields["notification_email"] = data.notification_email

    if not update_fields:
        return _doc_to_admin_out(doc)

    oid = ObjectId(admin_id)
    result = await db.admins.find_one_and_update(
        {"_id": oid},
        {"$set": update_fields},
        return_document=True,
    )
    return _doc_to_admin_out(result)

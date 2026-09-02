import hashlib
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.mongo import db
from app.schemas.admin import AdminCreate, AdminLogin, AdminOut, AdminUpdate
from app.schemas.auth import Token


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _doc_to_admin_out(doc: dict) -> AdminOut:
    return AdminOut(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        created_at=doc["created_at"],
    )


async def signup(data: AdminCreate) -> AdminOut:
    hashed = hash_password(data.password)
    doc = {
        "email": data.email,
        "password": hashed,
        "name": data.name,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = await db.admins.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다",
        )
    doc["_id"] = result.inserted_id
    return _doc_to_admin_out(doc)


async def login(data: AdminLogin) -> Token:
    doc = await db.admins.find_one({"email": data.email})
    if doc is None or not verify_password(data.password, doc["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
        )
    admin_id = str(doc["_id"])
    return Token(
        access_token=create_access_token(admin_id),
        refresh_token=create_refresh_token(admin_id),
    )


async def refresh_access_token(refresh_token: str) -> Token:
    token_hash = _hash_token(refresh_token)
    revoked = await db.revoked_tokens.find_one({"token_hash": token_hash})
    if revoked is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그아웃된 토큰입니다",
        )
    payload = decode_token(refresh_token)
    admin_id: str | None = payload.get("sub")
    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )
    return Token(
        access_token=create_access_token(admin_id),
        refresh_token=create_refresh_token(admin_id),
    )


async def logout(refresh_token: str) -> None:
    payload = decode_token(refresh_token)
    exp: int | None = payload.get("exp")
    expires_at = (
        datetime.fromtimestamp(exp, tz=timezone.utc)
        if exp is not None
        else datetime.now(timezone.utc)
    )
    token_hash = _hash_token(refresh_token)
    await db.revoked_tokens.update_one(
        {"token_hash": token_hash},
        {"$setOnInsert": {"token_hash": token_hash, "expires_at": expires_at}},
        upsert=True,
    )


async def get_admin(admin_id: str) -> AdminOut:
    try:
        oid = ObjectId(admin_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다",
        )
    doc = await db.admins.find_one({"_id": oid})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다",
        )
    return _doc_to_admin_out(doc)


async def update_admin(admin_id: str, data: AdminUpdate) -> AdminOut:
    try:
        oid = ObjectId(admin_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다",
        )
    update_fields: dict = {}
    if data.name is not None:
        update_fields["name"] = data.name
    if data.password is not None:
        update_fields["password"] = hash_password(data.password)

    if not update_fields:
        doc = await db.admins.find_one({"_id": oid})
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="관리자를 찾을 수 없습니다",
            )
        return _doc_to_admin_out(doc)

    result = await db.admins.find_one_and_update(
        {"_id": oid},
        {"$set": update_fields},
        return_document=True,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다",
        )
    return _doc_to_admin_out(result)

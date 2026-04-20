from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    verify_token,
    verify_password,
    hash_password,
)
from app.db.redis_client import redis_client
from app.db.session import get_db
from app.models.user import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
)
from app.models.user_table import User

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    user = User(
        username=data.username,
        nickname=data.nickname,
        hashed_password=hash_password(data.password),
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "注册成功",
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "is_active": user.is_active
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    token = create_access_token({
        "sub": str(user.id),
        "username": user.username
    })

    # Redis 可用时：记录当前用户最新 token
    try:
        await redis_client.set(
            f"user:token:{user.id}",
            token,
            ex=7200
        )
    except Exception:
        pass

    return {
        "access_token": token,
        "token_type": "bearer"
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    username = payload.get("username")

    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 信息不完整"
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    # 如果 Redis 可用，则校验当前 token 是否仍然有效
    try:
        saved_token = await redis_client.get(f"user:token:{user.id}")
        if saved_token is None or saved_token != token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已失效，请重新登录"
            )
    except HTTPException:
        raise
    except Exception:
        # Redis 不可用时，降级为仅校验 JWT
        pass

    return user


@router.get("/me", response_model=UserPublic)
async def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 信息不完整"
        )

    try:
        await redis_client.delete(f"user:token:{user_id}")
        return {"message": "退出成功，token 已失效"}
    except Exception:
        return {"message": "退出成功（当前 Redis 不可用，未执行 token 失效控制）"}


@router.get("/redis-test")
async def redis_test():
    try:
        await redis_client.set("hello", "world", ex=60)
        value = await redis_client.get("hello")
        return {"redis": value}
    except Exception as e:
        return {"redis_error": str(e)}
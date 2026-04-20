from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from app.core.config import settings

# 统一的密码处理器：
# - 注册时用它把明文密码转成不可逆哈希
# - 登录时用同一套算法校验明文和哈希是否匹配
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    # 不保存明文密码，数据库里只存哈希结果。
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 用户登录时，把输入的明文密码和数据库中的哈希密码做比对。
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    # 避免直接修改调用方传入的原始数据。
    to_encode = data.copy()

    # 生成过期时间，用于控制 token 的有效期。
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )

    # 标准 JWT 字段：
    # - exp: 过期时间，超过这个时间后 token 不再可用
    # - iat: 签发时间，便于排查问题或后续扩展校验逻辑
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    })

    # 用配置中的密钥和算法对 payload 签名，生成最终 token。
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str):
    try:
        # 解码时会同时校验签名和 exp 是否合法。
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        # token 本身结构正确，但已经超过有效期。
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期"
        )
    except jwt.InvalidTokenError:
        # 包括签名错误、格式错误、payload 非法等情况。
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效"
        )

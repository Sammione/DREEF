import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from fastapi.exceptions import HTTPException
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ISSUER = os.getenv("JWT_ISSUER")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
JWT_ALGORITHM = "HS256"


def _extract_token(request: Request) -> tuple[Optional[str], str]:
    """
    Extract JWT from the request.
    Priority 1: Authorization: Bearer <token> header.
    Priority 2: access_token cookie.
    Returns (token, source) where source is "Header", "Cookie", or "None".
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            return token, "Header"

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token, "Cookie"

    return None, "None"


def _unauthorized_body(request: Request) -> dict:
    return {
        "statusCode": 401,
        "message": "Authentication failed. Token is invalid or expired.",
        "sourceUrl": str(request.url.path),
        "traceId": request.headers.get("X-Request-ID", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def require_auth(request: Request) -> dict:
    """
    FastAPI dependency that mirrors the EMS JwtBearerEvents strategy:
    - Logs incoming request auth state (OnMessageReceived equivalent)
    - Validates JWT against configured issuer, audience, and secret
    - Logs success with auth source and user ID (OnTokenValidated equivalent)
    - Logs warning and raises HTTP 401 on any failure (OnAuthenticationFailed / OnChallenge equivalent)
    Returns the decoded JWT claims payload on success.
    """
    has_cookie = "access_token" in request.cookies
    has_header = "Authorization" in request.headers
    logger.info(
        "OnMessageReceived - Path: %s, HasCookie: %s, HasHeader: %s",
        request.url.path, has_cookie, has_header,
    )

    token, source = _extract_token(request)

    if not token:
        logger.warning("No token found in cookie or header for path: %s", request.url.path)
        raise HTTPException(status_code=401, detail=_unauthorized_body(request))

    logger.info("Token found in %s, length: %d", source, len(token))

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={"leeway": 0},  # ClockSkew = Zero
        )
        user_id = payload.get("sub")
        logger.info(
            "JWT authenticated via %s for user %s on path: %s",
            source, user_id, request.url.path,
        )
        return payload

    except JWTError as exc:
        logger.warning("JWT Authentication failed: %s for path: %s", exc, request.url.path)
        raise HTTPException(status_code=401, detail=_unauthorized_body(request))

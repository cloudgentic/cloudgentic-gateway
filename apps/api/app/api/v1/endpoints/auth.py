import base64
import io

import pyotp
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_token,
    decrypt_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TOTPSetupResponse,
    TOTPVerifyRequest,
    TOTPVerifyResponse,
    TokenResponse,
)
from app.schemas.user import SetupStatusResponse
from app.services.audit import log_action
from app.core.redis import redis_client

router = APIRouter()


@router.get("/setup-status", response_model=SetupStatusResponse)
async def setup_status(db: AsyncSession = Depends(get_db)):
    """Check if initial setup has been completed."""
    result = await db.execute(select(func.count()).select_from(User).where(User.is_admin.is_(True)))
    admin_count = result.scalar()
    return SetupStatusResponse(has_admin=admin_count > 0, setup_complete=admin_count > 0)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. First user becomes admin."""
    from app.core.config import get_settings
    settings = get_settings()

    # Check if this is the first user (becomes admin — always allowed)
    result = await db.execute(select(func.count()).select_from(User))
    user_count = result.scalar()
    is_first_user = user_count == 0

    # After first user, check if registration is open
    if not is_first_user and not settings.allow_registration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled. Contact your admin.",
        )

    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email, User.deleted_at.is_(None)))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        display_name=request.display_name,
        is_admin=is_first_user,
    )
    db.add(user)
    await db.flush()

    await log_action(
        db,
        user_id=user.id,
        action="user.register",
        resource_type="user",
        resource_id=str(user.id),
        detail=f"User registered (admin={is_first_user})",
    )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        requires_2fa_setup=True,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/password + optional TOTP code."""
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    # If TOTP is enabled, require the code
    if user.totp_enabled:
        if not request.totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="TOTP code required",
                headers={"X-Requires-TOTP": "true"},
            )
        totp_secret = decrypt_token(user.totp_secret, str(user.id))
        totp = pyotp.TOTP(totp_secret)
        if not totp.verify(request.totp_code, valid_window=1):
            await log_action(
                db, user_id=user.id, action="auth.login_failed",
                detail="Invalid TOTP code", status="denied",
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")

    await log_action(
        db, user_id=user.id, action="auth.login",
        resource_type="user", resource_id=str(user.id),
    )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        requires_2fa_setup=not user.totp_enabled,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an access token."""
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))

    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def totp_setup(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate TOTP secret and QR code for 2FA setup."""
    if user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP already enabled")

    secret = pyotp.random_base32()
    user.totp_secret = encrypt_token(secret, str(user.id))
    await db.flush()

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="CloudGentic Gateway")

    # Generate QR code
    img = qrcode.make(provisioning_uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return TOTPSetupResponse(
        secret=secret,
        provisioning_uri=provisioning_uri,
        qr_code_base64=qr_base64,
    )


@router.post("/totp/verify", response_model=TOTPVerifyResponse)
async def totp_verify(
    request: TOTPVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify TOTP code to complete 2FA setup."""
    if not user.totp_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Run TOTP setup first")

    totp_secret = decrypt_token(user.totp_secret, str(user.id))
    totp = pyotp.TOTP(totp_secret)
    if not totp.verify(request.code, valid_window=1):
        return TOTPVerifyResponse(success=False, message="Invalid code. Try again.")

    user.totp_enabled = True
    user.setup_complete = True
    await db.flush()

    await log_action(
        db, user_id=user.id, action="auth.totp_enabled",
        resource_type="user", resource_id=str(user.id),
    )

    return TOTPVerifyResponse(success=True, message="2FA enabled successfully")


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the user's password."""
    if not verify_password(request.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    from datetime import datetime, timezone

    user.password_hash = hash_password(request.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    await db.flush()

    await log_action(
        db, user_id=user.id, action="auth.password_changed",
        resource_type="user", resource_id=str(user.id),
    )

    return {"message": "Password changed successfully. Please log in again."}


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset. Generates a reset token stored in Redis.

    In self-hosted mode, the admin retrieves reset tokens via CLI:
        docker exec gateway-api python -m app.cli reset-password <email> <new_password>

    When SMTP is configured, this endpoint will send the reset link via email.
    The token is NEVER returned in the API response to prevent account takeover.
    """
    import secrets
    import logging

    logger = logging.getLogger("cloudgentic.auth")

    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    # Always return the same response to prevent email enumeration
    response_msg = "If an account with that email exists, a password reset has been initiated. Check your email or contact your admin."

    if not user:
        return {"message": response_msg}

    # Generate a reset token, store in Redis with 15-min TTL
    reset_token = secrets.token_urlsafe(48)
    await redis_client.setex(
        f"cgw:reset:{reset_token}",
        900,  # 15 minutes
        str(user.id),
    )

    # Log the token server-side only — admin can retrieve from container logs
    logger.info(f"Password reset token generated for {request.email}: {reset_token}")
    logger.info(f"Reset URL: /auth/reset-password?token={reset_token}")

    await log_action(
        db, user_id=user.id, action="auth.password_reset_requested",
        resource_type="user", resource_id=str(user.id),
    )

    # TODO: When SMTP is configured, send email with reset link
    return {"message": response_msg}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using a valid reset token."""
    from uuid import UUID as PyUUID

    # Look up the token in Redis
    user_id = await redis_client.get(f"cgw:reset:{request.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    result = await db.execute(
        select(User).where(User.id == PyUUID(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

    user.password_hash = hash_password(request.new_password)
    await db.flush()

    # Delete the used token
    await redis_client.delete(f"cgw:reset:{request.token}")

    await log_action(
        db, user_id=user.id, action="auth.password_reset",
        resource_type="user", resource_id=str(user.id),
    )

    return {"message": "Password reset successfully. You can now log in with your new password."}

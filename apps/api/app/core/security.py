import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from app.core.config import get_settings

settings = get_settings()

# --- Password Hashing (Argon2id) ---

ph = PasswordHasher(
    time_cost=settings.argon2_time_cost,
    memory_cost=settings.argon2_memory_cost,
    parallelism=settings.argon2_parallelism,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False


# --- JWT Tokens ---


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.gateway_jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.gateway_jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.gateway_jwt_secret, algorithms=[settings.jwt_algorithm])


# --- AES-256-GCM Encryption (Token Vault) ---


def _get_master_key() -> bytes:
    key_hex = settings.gateway_master_key
    if not key_hex:
        raise ValueError("GATEWAY_MASTER_KEY is not set")
    return bytes.fromhex(key_hex)


def derive_user_key(user_id: str) -> bytes:
    """Derive a per-user encryption key using HKDF."""
    master_key = _get_master_key()
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=f"cloudgentic-gateway-user-{user_id}".encode(),
    )
    return hkdf.derive(master_key)


def encrypt_token(plaintext: str, user_id: str) -> str:
    """Encrypt a token using AES-256-GCM with per-user key."""
    key = derive_user_key(user_id)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    # Format: hex(nonce):hex(ciphertext)
    return nonce.hex() + ":" + ciphertext.hex()


def decrypt_token(encrypted: str, user_id: str) -> str:
    """Decrypt a token using AES-256-GCM with per-user key."""
    key = derive_user_key(user_id)
    nonce_hex, ct_hex = encrypted.split(":")
    nonce = bytes.fromhex(nonce_hex)
    ciphertext = bytes.fromhex(ct_hex)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()


# --- API Key Utilities ---

API_KEY_PREFIX = "cgw_"


def generate_api_key() -> tuple[str, str]:
    """Generate an API key. Returns (raw_key, hashed_key)."""
    raw = API_KEY_PREFIX + secrets.token_urlsafe(32)
    hashed = hash_api_key(raw)
    return raw, hashed


def hash_api_key(raw_key: str) -> str:
    """SHA-256 hash an API key for storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()

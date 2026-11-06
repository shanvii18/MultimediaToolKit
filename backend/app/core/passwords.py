"""
Password hashing with scrypt (Python standard library, memory-hard, no extra dependency).

Stored format: ``scrypt$<n>$<r>$<p>$<salt_b64>$<hash_b64>`` so parameters can be raised later
without invalidating existing hashes.
"""
import base64
import hashlib
import hmac
import secrets

SCRYPT_N = 2 ** 14   # CPU/memory cost (16 MB per hash)
SCRYPT_R = 8
SCRYPT_P = 1
DKLEN = 64
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=DKLEN,
                            maxmem=64 * 1024 * 1024)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        # Still spend the hashing time so response timing does not reveal unknown emails.
        hash_password(password or "x")
        return False
    try:
        scheme, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(hash_b64)
        digest = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt_b64), n=int(n), r=int(r),
                                p=int(p), dklen=len(expected), maxmem=64 * 1024 * 1024)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, expected)


def password_problem(password: str) -> str | None:
    """Return a user-facing reason the password is unacceptable, or None."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
    if password.strip() == "" or len(set(password)) < 4:
        return "Please choose a less predictable password."
    return None

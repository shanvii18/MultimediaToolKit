"""
Admin CLI. Everyday accounts are created by users themselves (public sign-up on the website).

    python -m app.cli set-password --email owner@example.com   # prompts; or MTK_NEW_PASSWORD env var

    python -m app.cli invite --email friend@example.com [--label "Portfolio reviewer"]
    python -m app.cli revoke --email friend@example.com
    python -m app.cli list-users
    python -m app.cli download-models [--whisper tiny base small]

The raw access key is printed ONCE and never stored (only its SHA-256 hash is kept).
Share the printed invite link privately; anyone holding it can use that account.
"""
import argparse
import sys
from urllib.parse import quote

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.migrations import upgrade_database
from app.core.security import create_access_key, revoke_access_keys, DEV_USER_EMAIL
from app.models.entities import AccessKey, User


def _invite(email: str, label: str | None) -> int:
    db = SessionLocal()
    try:
        user, raw_key = create_access_key(db, email, label)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()
    link = f"{settings.FRONTEND_URL.rstrip('/')}/?access_key={quote(raw_key)}"
    print(f"Access key created for {user.email}")
    print("Shown once -- store it safely. Invite link:")
    print(link)
    return 0


def _revoke(email: str) -> int:
    db = SessionLocal()
    try:
        count = revoke_access_keys(db, email)
    finally:
        db.close()
    print(f"Revoked {count} active key(s) for {email}.")
    return 0


def _set_password(email: str) -> int:
    """Give an existing account (e.g. one created by an old invite) a password; data stays intact."""
    import getpass
    import os

    from app.core.passwords import hash_password, password_problem

    password = os.environ.get("MTK_NEW_PASSWORD") or getpass.getpass("New password: ")
    problem = password_problem(password)
    if problem:
        print(f"Error: {problem}", file=sys.stderr)
        return 1
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            print(f"Error: no account for {email}.", file=sys.stderr)
            return 1
        user.password_hash = hash_password(password)
        db.commit()
    finally:
        db.close()
    print(f"Password set for {email}. They can now sign in on the website.")
    return 0


def _list_users() -> int:
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.email != DEV_USER_EMAIL).order_by(User.created_at).all()
        for u in users:
            active = db.query(AccessKey).filter(AccessKey.user_id == u.id, AccessKey.revoked_at.is_(None)).count()
            print(f"{u.email:40} role={u.role:10} password={'yes' if u.password_hash else 'no'} active_tokens={active}")
        if not users:
            print("No users yet.")
    finally:
        db.close()
    return 0


def _download_models(sizes) -> int:
    """Fetch CPU model weights into MODEL_CACHE_DIR (used by Docker builds / first-time setup)."""
    from app.adapters.tts_adapter import tts_adapter
    from app.adapters.whisper_adapter import whisper_adapter

    print(f"Model cache: {settings.MODEL_CACHE_DIR}")
    tts_adapter.ensure_model_files()
    print("Kokoro TTS model: ready")
    for size in sizes:
        whisper_adapter._load(size)
        print(f"Whisper '{size}': ready")
    return 0


def main(argv=None) -> int:
    upgrade_database()
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="MultimediaToolKit invite administration")
    sub = parser.add_subparsers(dest="command", required=True)
    p_inv = sub.add_parser("invite", help="Create a user (if needed) and issue an access key")
    p_inv.add_argument("--email", required=True)
    p_inv.add_argument("--label", default=None)
    p_rev = sub.add_parser("revoke", help="Revoke all active keys of a user")
    p_rev.add_argument("--email", required=True)
    sub.add_parser("list-users", help="List users")
    p_pw = sub.add_parser("set-password", help="Set the password of an existing account")
    p_pw.add_argument("--email", required=True)
    p_dl = sub.add_parser("download-models", help="Download CPU model weights into MODEL_CACHE_DIR")
    p_dl.add_argument("--whisper", nargs="*", default=["tiny", "base"], help="Whisper sizes (tiny base small)")

    args = parser.parse_args(argv)
    if args.command == "invite":
        return _invite(args.email, args.label)
    if args.command == "revoke":
        return _revoke(args.email)
    if args.command == "set-password":
        return _set_password(args.email)
    if args.command == "download-models":
        return _download_models(args.whisper)
    return _list_users()


if __name__ == "__main__":
    sys.exit(main())

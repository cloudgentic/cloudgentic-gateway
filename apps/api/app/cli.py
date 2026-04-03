"""CLI management commands for the gateway."""
import argparse
import asyncio
import sys

from sqlalchemy import select

from app.core.database import async_session
from app.core.security import hash_password
from app.models.user import User


async def reset_password(email: str, new_password: str):
    """Reset a user's password by email."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if not user:
            print(f"Error: No user found with email '{email}'")
            sys.exit(1)

        user.password_hash = hash_password(new_password)
        await db.commit()
        print(f"Password reset successfully for {email}")


async def list_users():
    """List all users."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.deleted_at.is_(None)))
        users = result.scalars().all()
        if not users:
            print("No users found.")
            return
        print(f"{'Email':<40} {'Admin':<8} {'2FA':<8} {'Active':<8}")
        print("-" * 64)
        for u in users:
            print(f"{u.email:<40} {str(u.is_admin):<8} {str(u.totp_enabled):<8} {str(u.is_active):<8}")


async def create_admin(email: str, password: str, display_name: str | None = None):
    """Create a new admin user."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"Error: User '{email}' already exists")
            sys.exit(1)

        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
            is_admin=True,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        print(f"Admin user created: {email}")
        print("Note: 2FA setup will be required on first login.")


async def disable_2fa(email: str):
    """Disable 2FA for a user (emergency recovery)."""
    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == email, User.deleted_at.is_(None)))
        user = result.scalar_one_or_none()
        if not user:
            print(f"Error: No user found with email '{email}'")
            sys.exit(1)

        user.totp_secret = None
        user.totp_enabled = False
        user.setup_complete = False
        await db.commit()
        print(f"2FA disabled for {email}. User will be prompted to set up 2FA on next login.")


def main():
    parser = argparse.ArgumentParser(description="CloudGentic Gateway Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # reset-password
    rp = subparsers.add_parser("reset-password", help="Reset a user's password")
    rp.add_argument("email", help="User email")
    rp.add_argument("password", help="New password")

    # list-users
    subparsers.add_parser("list-users", help="List all users")

    # create-admin
    ca = subparsers.add_parser("create-admin", help="Create a new admin user")
    ca.add_argument("email", help="Admin email")
    ca.add_argument("password", help="Admin password")
    ca.add_argument("--name", help="Display name", default=None)

    # disable-2fa
    d2 = subparsers.add_parser("disable-2fa", help="Disable 2FA for a user (emergency)")
    d2.add_argument("email", help="User email")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "reset-password":
        asyncio.run(reset_password(args.email, args.password))
    elif args.command == "list-users":
        asyncio.run(list_users())
    elif args.command == "create-admin":
        asyncio.run(create_admin(args.email, args.password, args.name))
    elif args.command == "disable-2fa":
        asyncio.run(disable_2fa(args.email))


if __name__ == "__main__":
    main()

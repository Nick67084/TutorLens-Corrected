
"""Student authentication and password security."""

import hashlib
import hmac
import secrets
import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from db.database import get_session
from db.tables import Account, Student


def register(name, login_id, password):
    name = name.strip()
    login_id = login_id.strip().lower()

    if not name or len(name) > 100:
        raise ValueError("Enter a valid full name.")

    if not re.fullmatch(r"[a-z0-9_-]{3,64}", login_id):
        raise ValueError(
            "Enter a valid student ID."
        )

    if not 8 <= len(password) <= 256:
        raise ValueError(
            "Password must contain 8–256 characters."
        )

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt),
        600000,
    ).hex()

    try:
        with get_session() as session:

            student = Student(
                name="account:" + secrets.token_hex(24)
            )

            session.add(student)
            session.flush()

            account = Account(
                student_id=student.id,
                login_id=login_id,
                full_name=name,
                password_hash=salt + ":" + digest,
            )

            session.add(account)

    except IntegrityError:
        raise ValueError(
            "Student ID is already registered."
        ) from None


def authenticate(login_id, password):

    if len(password) > 256:
        return None

    with get_session() as session:

        account = session.scalar(
            select(Account).where(
                Account.login_id
                == login_id.strip().lower()
            )
        )

        salt, expected = (
            account.password_hash.split(":")
            if account
            else ("00" * 16, "00" * 32)
        )

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt),
            600000,
        ).hex()

        if (
            not hmac.compare_digest(actual, expected)
            or account is None
        ):
            return None

        return {
            "id": account.student_id,
            "name": account.full_name,
            "login_id": account.login_id,
        }

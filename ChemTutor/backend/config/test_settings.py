"""Isolated test database; no institutional credentials or running model needed."""
import os
os.environ.setdefault("DB_ENGINE", "sqlite")
from .settings import *  # noqa: F403,E402

if os.environ["DB_ENGINE"] == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
AUTH_TYPE = "NONE"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

#  Copyright (c) 2019 Red Hat, Inc.
#
#  This file is part of ARA Records Ansible.
#
#  ARA is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  ARA is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with ARA.  If not, see <http://www.gnu.org/licenses/>.

import logging
import logging.config
import os
import textwrap

import yaml
from django.utils.crypto import get_random_string
from dynaconf import LazySettings

BASE_DIR = os.environ.get("ARA_BASE_DIR", os.path.expanduser("~/.ara/server"))
DEFAULT_SETTINGS = os.path.join(BASE_DIR, "settings.yaml")

settings = LazySettings(
    GLOBAL_ENV_FOR_DYNACONF="ARA", ENVVAR_FOR_DYNACONF="ARA_SETTINGS", SETTINGS_MODULE_FOR_DYNACONF=DEFAULT_SETTINGS
)

# reread BASE_DIR since it might have gotten changed in the config file.
BASE_DIR = settings.get("BASE_DIR", BASE_DIR)

# Django doesn't set up logging until it's too late to use it in settings.py.
# Set it up from the configuration so we can use it.
DEBUG = settings.get("DEBUG", False, "@bool")

LOG_LEVEL = settings.get("LOG_LEVEL", "INFO")
# fmt: off
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"normal": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "normal",
            "level": LOG_LEVEL,
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "ara": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": 0
        }
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL
    },
}
# fmt: on
logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)
logger.debug("Loaded logging configuration")

# Django built-in server and npm development server
ALLOWED_HOSTS = settings.get("ALLOWED_HOSTS", ["::1", "127.0.0.1", "localhost"])
CORS_ORIGIN_WHITELIST = settings.get("CORS_ORIGIN_WHITELIST", ["127.0.0.1:8000", "localhost:3000"])
CORS_ORIGIN_ALLOW_ALL = settings.get("CORS_ORIGIN_ALLOW_ALL", False)

ADMINS = settings.get("ADMINS", ())

READ_LOGIN_REQUIRED = settings.get("READ_LOGIN_REQUIRED", False, "@bool")
WRITE_LOGIN_REQUIRED = settings.get("WRITE_LOGIN_REQUIRED", False, "@bool")
EXTERNAL_AUTH = settings.get("EXTERNAL_AUTH", False, "@bool")


def get_secret_key():
    if not settings.get("SECRET_KEY"):
        logger.warn(f"No setting found for SECRET_KEY. Generating a random key...")
        return get_random_string(length=50)
    return settings.get("SECRET_KEY")


SECRET_KEY = get_secret_key()

# We're not expecting ARA to use multiple concurrent databases.
# Make it easier for users to specify the configuration for a single database.
DATABASE_ENGINE = settings.get("DATABASE_ENGINE", "django.db.backends.sqlite3")
DATABASE_NAME = settings.get("DATABASE_NAME", os.path.join(BASE_DIR, "ansible.sqlite"))
DATABASE_USER = settings.get("DATABASE_USER", None)
DATABASE_PASSWORD = settings.get("DATABASE_PASSWORD", None)
DATABASE_HOST = settings.get("DATABASE_HOST", None)
DATABASE_PORT = settings.get("DATABASE_PORT", None)

DATABASES = {
    "default": {
        "ENGINE": DATABASE_ENGINE,
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
    }
}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "ara.api",
    "ara.server.apps.AraAdminConfig",
]

EXTERNAL_AUTH_MIDDLEWARE = []
if EXTERNAL_AUTH:
    EXTERNAL_AUTH_MIDDLEWARE = ["django.contrib.auth.middleware.RemoteUserMiddleware"]
    AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.RemoteUserBackend"]

# fmt: off
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
] + EXTERNAL_AUTH_MIDDLEWARE + [
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware"
]
# fmt: on

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Note (dmsimard): attempting to use timezones causes drifts in log timestamps
# because there is a minimal logging configuration that is loaded first and then
# it is reloaded with timezone data. It's likely safer and more reliable to use
# the local system timezone instead.
USE_TZ = False
TIME_ZONE = None

# We do not currently support internationalization and localization, turn these
# off.
USE_I18N = False
USE_L10N = False

# whitenoise serves static files without needing to use "collectstatic"
WHITENOISE_USE_FINDERS = True
STATIC_URL = settings.get("STATIC_URL", "/static/")
STATIC_ROOT = settings.get("STATIC_ROOT", os.path.join(BASE_DIR, "www", "static"))

# Create STATIC_ROOT if it doesn't exist to avoid a warning from whitenoise
# https://github.com/evansd/whitenoise/issues/215
if not os.path.isdir(STATIC_ROOT):
    os.makedirs(STATIC_ROOT, mode=0o755)

MEDIA_URL = settings.get("MEDIA_URL", "/media/")
MEDIA_ROOT = settings.get("MEDIA_ROOT", os.path.join(BASE_DIR, "www", "media"))

WSGI_APPLICATION = "ara.server.wsgi.application"
ROOT_URLCONF = "ara.server.urls"
APPEND_SLASH = False

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework.authentication.BasicAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("ara.api.auth.APIAccessPermission",),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

ARA_SETTINGS = os.getenv("ARA_SETTINGS", DEFAULT_SETTINGS)
logger.info(f"Using settings file: {ARA_SETTINGS}")

# TODO: Split this out to a CLI command (django-admin command ?)

# Ensure default base configuration/data directory exists
if not os.path.isdir(BASE_DIR):
    logger.info(f"Creating data & configuration directory: {BASE_DIR}")
    os.makedirs(BASE_DIR, mode=0o700)

if not os.path.exists(DEFAULT_SETTINGS) and "ARA_SETTINGS" not in os.environ:
    SETTINGS = dict(
        BASE_DIR=BASE_DIR,
        ALLOWED_HOSTS=ALLOWED_HOSTS,
        CORS_ORIGIN_WHITELIST=CORS_ORIGIN_WHITELIST,
        CORS_ORIGIN_ALLOW_ALL=CORS_ORIGIN_ALLOW_ALL,
        SECRET_KEY=SECRET_KEY,
        DATABASES=DATABASES,
        DEBUG=DEBUG,
        LOG_LEVEL=LOG_LEVEL,
        LOGGING=LOGGING,
        READ_LOGIN_REQUIRED=READ_LOGIN_REQUIRED,
        WRITE_LOGIN_REQUIRED=WRITE_LOGIN_REQUIRED,
    )
    with open(DEFAULT_SETTINGS, "w+") as settings_file:
        comment = f"""
        ---
        # This is a default settings template generated by ARA.
        # To use a settings file such as this one, you need to export the
        # ARA_SETTINGS environment variable like so:
        #   $ export ARA_SETTINGS="{DEFAULT_SETTINGS}"

        """
        logger.info(f"Writing default settings to {DEFAULT_SETTINGS}")
        settings_file.write(textwrap.dedent(comment))
        yaml.dump({"default": SETTINGS}, settings_file, default_flow_style=False)
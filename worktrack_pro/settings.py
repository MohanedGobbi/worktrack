"""
Django settings for worktrack_pro project.
"""

import os
from pathlib import Path
from datetime import timedelta
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

import sys as _sys
_TESTING = len(_sys.argv) > 1 and _sys.argv[1] == 'test'

# SECURITY WARNING: don't run with debug turned on in production!
# Off unless .env says DEBUG=True (local development only).
DEBUG = config('DEBUG', default=False, cast=bool)

# SECURITY WARNING: keep the secret key used in production secret!
_INSECURE_KEY = 'django-insecure-dev-key-change-in-production'
SECRET_KEY = config('SECRET_KEY', default=_INSECURE_KEY)
if SECRET_KEY == _INSECURE_KEY and not (DEBUG or _TESTING):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured(
        'SECRET_KEY is not set. Add a long random SECRET_KEY to .env (see .env.example), '
        'or set DEBUG=True for local development.'
    )

# Host checking is done per install by core.middleware.DynamicHostMiddleware
# (AllowedHost table), so Django's own list defaults to '*'. Narrow it in .env
# if the install does not use the host-management table.
ALLOWED_HOSTS = [h.strip() for h in config('ALLOWED_HOSTS', default='*').split(',') if h.strip()]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    
]

_PROJECT_APPS = [
    ('users', 'users.apps.UsersConfig'),
    ('tasks', 'tasks.apps.TasksConfig'),
    ('submissions', 'submissions.apps.SubmissionsConfig'),
    ('kpi', 'kpi.apps.KpiConfig'),
    ('notifications', 'notifications.apps.NotificationsConfig'),
    ('audit', 'audit.apps.AuditConfig'),
    ('dashboards', 'dashboards.apps.DashboardsConfig'),
    ('work_modules', 'work_modules.apps.WorkModulesConfig'),
    ('archives', 'archives.apps.ArchivesConfig'),
    ('core', 'core.apps.CoreConfig'),
    ('attendance', 'attendance.apps.AttendanceConfig'),
    ('messaging', 'messaging.apps.MessagingConfig'),
]

for app_dir, app_config in _PROJECT_APPS:
    if (BASE_DIR / app_dir).exists():
        INSTALLED_APPS.append(app_config)

try:
    import django_celery_beat
    INSTALLED_APPS.append('django_celery_beat')
except ImportError:
    pass

MIDDLEWARE = [
    'core.middleware.DynamicHostMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ↓ MUST be last so it post-processes fully-rendered HTML
    'core.middleware.DynamicTranslationMiddleware',
]

ROOT_URLCONF = 'worktrack_pro.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.sidebar_modules',
                'core.context_processors.site_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'worktrack_pro.wsgi.application'

# Database configuration
db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')

if 'mysql' in db_engine:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='worktrack_pro'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='127.0.0.1'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            },
        }
    }
elif 'postgresql' in db_engine:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='worktrack_pro'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='127.0.0.1'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    db_name = config('DB_NAME', default='')
    db_file = Path(db_name) if db_name and os.path.isabs(db_name) else BASE_DIR / (db_name or 'db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_file,
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# WorkTrack Pro 3D Studio saves its config (incl. embedded background / lightweight
# homepage images as data URLs) to /api/admin-config/. Django's 2.5 MB default
# rejected these payloads, so the homepage never received the uploaded image.
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
WHITENOISE_MANIFEST_STRICT = False

# Tests (and local DEBUG runs) render templates without a collectstatic manifest,
# so the hashed-name lookup would fail. Use plain storage there; production
# (DEBUG=False, not testing) keeps the compressed manifest storage.
if _TESTING or DEBUG:
    STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Media files
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = Path(config('MEDIA_ROOT', default=str(BASE_DIR / 'media')))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache backend – use file-based so version survives dev-server reloads
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': str(BASE_DIR / '.translation_cache'),
        'TIMEOUT': None,
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# CORS and CSRF Configuration
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://localhost:8000').split(',')
CORS_ALLOW_CREDENTIALS = True

# Crash-Proof CSRF Origin Loader
CSRF_TRUSTED_ORIGINS = [
    'https://dhetasks.com', 'https://www.dhetasks.com',
    'http://dhetasks.com', 'http://www.dhetasks.com',
    'http://localhost:8000', 'http://127.0.0.1:8000',
    'http://localhost:3000', 'http://127.0.0.1:3000',
    'http://localhost', 'http://127.0.0.1',
    'http://0.0.0.0:8000', 'http://0.0.0.0',
    'https://localhost:8000', 'https://127.0.0.1:8000',
]
_env_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if _env_origins:
    CSRF_TRUSTED_ORIGINS.extend([o.strip() for o in _env_origins.split(',') if o.strip()])

# Reverse proxy SSL & Host headers: Only enable when not running in local debug mode
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    # Opt-in: only once the site is reliably served over HTTPS.
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)

CSRF_FAILURE_VIEW = 'core.views.csrf_failure_view'

CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Crash-Proof HTTPS Cookie Enforcer
_env_secure = str(os.getenv('SECURE_COOKIES', 'False')).lower()
CSRF_COOKIE_SECURE = _env_secure in ('true', '1', 't', 'y', 'yes')
SESSION_COOKIE_SECURE = _env_secure in ('true', '1', 't', 'y', 'yes')

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)

# Smart Port Resolution: Port 465 requires SSL, Port 587 requires TLS
if EMAIL_PORT == 465 and not EMAIL_USE_TLS and not EMAIL_USE_SSL:
    EMAIL_USE_SSL = True
elif EMAIL_PORT == 587 and not EMAIL_USE_SSL and not EMAIL_USE_TLS:
    EMAIL_USE_TLS = True

EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@worktrackpro.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'worktrack_pro.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Allow iframes from the same origin (required for Live Widget Preview)
X_FRAME_OPTIONS = 'SAMEORIGIN'
# Trigger reload

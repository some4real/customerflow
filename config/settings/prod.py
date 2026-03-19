from .base import *
import os
from dotenv import load_dotenv
load_dotenv()


DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv("DATABASE_URL")
        )

}

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
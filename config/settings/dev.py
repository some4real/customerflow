from .base import *

# Use SQLite locally
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  
    }
}

DEBUG = True
ALLOWED_HOSTS = ['*']
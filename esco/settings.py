from __future__ import with_statement
import os

#
# Configuration file must contain:
#
# DEBUG
# DATABASE_ENGINE
# DATABASE_NAME
# DATABASE_USER
# DATABASE_PASSWORD
# DATABASE_HOST
# DATABASE_PORT
# SECRET_KEY
# TIME_ZONE
# LANGUAGE_CODE
# USE_I18N
# EMAIL_HOST
# EMAIL_PORT
# DEFAULT_FROM_EMAIL
# MEDIA_ROOT
# ABSTRACTS_PATH
# ADMINS
#
# See Django documentation for possible values.
#

path = os.path.expanduser('~/esco-2012.conf')

if os.path.exists(path):
    with open(path) as conf:
        exec conf.read()
else:
    raise RuntimeError('configuration not found at %s' % path)

TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS

SITE_ID = 1

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'esco.contrib.nocache.NoCacheIfAuthenticatedMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'esco.site',
)

ROOT_URLCONF = 'esco.urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

MEDIA_URL  = '/media/'
LOGIN_URL  = '/account/login/'

ADMIN_MEDIA_PREFIX = MEDIA_URL + 'admin/'

DEFAULT_CONTENT_TYPE = 'text/html'

MIN_PASSWORD_LEN = 6
CHECK_STRENGTH = True

CAPTCHA = {
    'fgcolor': '#254b6f',
    'imagesize': (200, 50),
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
AUTH_PROFILE_MODULE = 'site.UserProfile'

AUTHENTICATION_BACKENDS = (
    'esco.contrib.emailauth.EmailBackend',
)

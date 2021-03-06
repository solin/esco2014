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
# ENABLE_ABSTRACT_SUBMISSION
# SEND_EMAIL
# ADMINS
#
# See Django documentation for possible values.
#

path = os.path.expanduser(os.path.join(os.path.dirname(__file__), '../../esco-2014.conf'))

if os.path.exists(path):
    with open(path) as conf:
        exec conf.read()
else:
    raise RuntimeError('configuration not found at %s' % path)

TEMPLATE_DEBUG = DEBUG
MANAGERS = ADMINS

SITE_ID = 1

# for Django 1.2
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

## for Django 1.4
#TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.Loader',
#    'django.template.loaders.app_directories.Loader',
#)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'conference.contrib.nocache.NoCacheIfAuthenticatedMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'conference.site',
)

ROOT_URLCONF = 'conference.urls'

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

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

TEMPLATE_CONTEXT_PROCESSORS += (
    'conference.contrib.context_processors.enable_abstract_submission',
)

AUTHENTICATION_BACKENDS = (
    'conference.contrib.emailauth.EmailBackend', 'django.contrib.auth.backends.ModelBackend'
)

"""These settings rely on various environment variables being set
"""

import os
import sys
import raven


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['bustimes.org', 'localhost', 'reblochon.local', '192.168.1.66']

DEBUG = bool(os.environ.get('DEBUG', False)) or 'test' in sys.argv

SERVER_EMAIL = 'contact@bustimes.org.uk'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'haystack',
    'busstops',
    'multigtfs',
    'pipeline',
    'antispam',
    'email_obfuscator',
    'raven.contrib.django.raven_compat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'busstops.middleware.real_ip_middleware',
    'busstops.middleware.not_found_redirect_middleware',
]

if DEBUG and 'runserver' in sys.argv:
    INTERNAL_IPS = ['127.0.0.1']
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'buses.urls'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    } if DEBUG else {
        'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
        'INCLUDE_SPELLING': True,
    },
}
HAYSTACK_IDENTIFIER_METHOD = 'buses.utils.get_identifier'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME', 'bustimes'),
        'CONN_MAX_AGE': None
    }
}

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

STATIC_URL = '/static/'
STATIC_ROOT = os.environ.get('STATIC_ROOT', os.path.join(BASE_DIR, '..', 'bustimes-static'))
MEDIA_URL = '/media/'
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, '..', 'bustimes-media'))

if DEBUG:
    STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
else:
    STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)
PIPELINE = {
    'COMPILERS': [
        'busstops.compilers.AutoprefixerSASSCompiler',
    ],
    'STYLESHEETS': {
        'main': {
            'source_filenames': (
                'css/style.scss',
            ),
            'output_filename': 'css/style.css',
        },
        'ie': {
            'source_filenames': (
                'css/ie.scss',
            ),
            'output_filename': 'css/ie.css',
        }
    },
    'JAVASCRIPT': {
        'frontpage': {
            'source_filenames': (
                'js/frontpage.js',
            ),
            'output_filename': 'js/frontpage.min.js',
            'extra_context': {
                'async': True
            }
        },
        'map': {
            'source_filenames': (
                'js/bower_components/loadjs/dist/loadjs.min.js',
                'js/map.js',
            ),
            'output_filename': 'js/map.min.js',
            'extra_context': {
                'async': True
            }
        },
        'global': {
            'source_filenames': (
                'js/global.js',
            ),
            'output_filename': 'js/global.min.js',
            'extra_context': {
                'async': True
            }
        },
        'timetable': {
            'source_filenames': (
                'js/timetable.js',
            ),
            'output_filename': 'js/timetable.min.js',
            'extra_context': {
                'async': True
            }
        },
        'hugemap': {
            'source_filenames': (
                'js/bower_components/leaflet.markercluster/dist/leaflet.markercluster.js',
                'js/bower_components/reqwest/reqwest.min.js',
                'js/bower_components/jquery-throttle-debounce/jquery.ba-throttle-debounce.min.js',
                'js/hugemap.js',
            ),
            'output_filename': 'js/hugemap.min.js',
            'extra_context': {
                'async': True
            }
        },
        'vehicles': {
            'source_filenames': (
                'js/bower_components/reqwest/reqwest.min.js',
                'js/bower_components/jquery-throttle-debounce/jquery.ba-throttle-debounce.min.js',
                'js/vehicles.js',
            ),
            'output_filename': 'js/vehicles.min.js',
            'extra_context': {
                'async': True
            }
        },
        'livemap': {
            'source_filenames': (
                'js/bower_components/leaflet/dist/leaflet.js',
                'js/bower_components/reqwest/reqwest.min.js',
                'js/livemap.js',
            ),
            'output_filename': 'js/livemap.min.js',
            'extra_context': {
                'async': True
            }
        },

    },
    'YUGLIFY_BINARY': os.path.join(BASE_DIR, 'node_modules', '.bin', 'yuglify'),
    'CSS_COMPRESSOR': None,
    'SASS_ARGUMENTS': '--style compressed --sourcemap=none',
}
PIPELINE_AUTOPREFIXER_BINARY = os.path.join(BASE_DIR, 'node_modules', '.bin', 'postcss')

TEMPLATE_MINIFER_STRIP_FUNCTION = 'buses.utils.minify'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'debug': DEBUG,
            'loaders': (
                'django.template.loaders.app_directories.Loader' if DEBUG else (
                    'django.template.loaders.cached.Loader', (
                        'template_minifier.template.loaders.app_directories.Loader',
                    )
                ),
            ),
            'context_processors': (
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'busstops.context_processors.amp',
            )
        }
    }
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    } if DEBUG else {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211'
    }
}

TIME_FORMAT = 'H:i'
DATE_FORMAT = 'l j F Y'
DATETIME_FORMAT = 'j F Y H:i'
TIME_ZONE = 'Europe/London'
USE_TZ = True
USE_I18N = False

if not DEBUG and 'test' not in sys.argv:
    RAVEN_CONFIG = {
        'dsn': os.environ.get('SENTRY_DSN'),
        'release': raven.fetch_git_sha(BASE_DIR)
    }

    INSTALLED_APPS.append('ddtrace.contrib.django')
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'root': {
            'level': 'WARNING',
            'handlers': ['sentry'],
        },
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s '
                          '%(process)d %(thread)d %(message)s'
            },
        },
        'handlers': {
            'sentry': {
                'level': 'ERROR',
                'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            },
        },
    }

    DATADOG_TRACE = {
        'DEFAULT_SERVICE': 'bustimes',
        'TAGS': {'env': 'production'},
    }

STREETVIEW_KEY = os.environ.get('STREETVIEW_KEY')
STREETVIEW_SECRET = os.environ.get('STREETVIEW_SECRET')

TRANSPORTAPI = {
   'app_id': os.environ.get('TRANSPORTAPI_APP_ID'),
   'app_key': os.environ.get('TRANSPORTAPI_APP_KEY')
}
TFL = {
    'app_id': os.environ.get('TFL_APP_ID'),
    'app_key': os.environ.get('TFL_APP_KEY')
}
TFWM = {
    'app_id': os.environ.get('TFWM_APP_ID'),
    'app_key': os.environ.get('TFWM_APP_KEY')

}

SINGAPORE_KEY = os.environ.get('SINGAPORE_KEY')

DATA_DIR = os.path.join(BASE_DIR, 'data')
TNDS_DIR = os.path.join(DATA_DIR, 'TNDS')

VIGLINK_KEY = '63dc39b879576a255e9dcee17b6c1929'

AKISMET_API_KEY = os.environ.get('AKISMET_API_KEY')
AKISMET_SITE_URL = 'https://bustimes.org'

IE_COLLECTIONS = (
    'luasbus', 'dublinbus', 'kenneallys', 'locallink', 'irishrail', 'ferries',
    'manda', 'finnegans', 'citylink', 'nitelink', 'buseireann', 'mcgeehan',
    'mkilbride', 'expressbus', 'edmoore', 'collins', 'luas', 'sro',
    'dublincoach', 'burkes', 'mhealy', 'kearns', 'josfoley', 'buggy',
    'jjkavanagh', 'citydirect', 'aircoach', 'matthews', 'wexfordbus',
    'dualway', 'tralee', 'sbloom', 'mcginley', 'swordsexpress', 'suirway',
    'sdoherty', 'pjmartley', 'mortons', 'mgray', 'mcgrath', 'mangan',
    'lallycoach', 'halpenny', 'eurobus', 'donnellys', 'cmadigan', 'bkavanagh',
    'ptkkenneally', 'farragher', 'fedateoranta', 'ashbourneconnect'
)

SITE_ID = 1

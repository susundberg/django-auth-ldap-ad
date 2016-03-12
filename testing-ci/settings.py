DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.sqlite3',
            'NAME':     'travisdb',  
            'USER':     '',
            'PASSWORD': '',
            'HOST':     'localhost',
            'PORT':     '',
        }
}

INSTALLED_APPS=["django-auth-ldap-ad","django.contrib.auth", "django.contrib.contenttypes"]
DEBUG=True

SECRET_KEY="92f7zw@-pl+pc2seg=*sfc7hkrx3h-8+jgsfzay#p)9$t(6@@t"


# -*- coding: utf-8 -*-

AUTHENTICATION_BACKENDS = [
  #'django.contrib.auth.backends.RemoteUserBackend',
  'django.contrib.auth.backends.BaseBackend',
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
INSTALLED_APPS = [
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'pistoke.Pistoke',
  'sivuvahti',
  'testit',
]
MIDDLEWARE = [
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.contrib.auth.middleware.AuthenticationMiddleware',
  'pistoke.ohjain.WebsocketOhjain',
]
SECRET_KEY = 'epäjärjestelmällistyttämättömyydellänsäkäänköhän'
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
USE_TZ = True

# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
  setup_requires='git-versiointi>=1.6rc4',
  name='django-sivuvahti',
  description='Django-laajennos avoinna olevien sivujen seuraamiseen',
  url='https://github.com/an7oine/django-sivuvahti.git',
  author='Antti Hautaniemi',
  author_email='antti.hautaniemi@me.com',
  licence='MIT',
  packages=find_packages(exclude=['testit']),
  include_package_data=True,
  python_requires='>=3.8',
  install_requires=['celery', 'django-pistoke', 'websockets'],
  entry_points={
    'django.sovellus': ['sivuvahti = sivuvahti'],
    'django.osoitteisto': ['sivuvahti = sivuvahti'],
  },
  zip_safe=False,
)

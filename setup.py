#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

PACKAGE       = 'pyral'
VERSION       = '1.6.0'
OFFICIAL_NAME = 'Python toolkit for Rally REST API'
PKG_URL_NAME  = 'python-toolkit-rally-rest-api'
AUTHOR        = 'Kip Lehman (Broadcom, Agile Operations Division)'
AUTHOR_EMAIL  = 'kip.lehman@broadcom.com'
LICENSE       = 'BSD'
KEYWORDS      = ['rally', 'api']
GITHUB_SITE   = 'https://github.com/RallyTools/RallyRestToolkitForPython'
GITHUB_DISTS  = '%s/raw/master/dists' % GITHUB_SITE
DOWNLOADABLE_ZIP = '%s/%s-%s.zip' % (GITHUB_DISTS, PACKAGE, VERSION)
SHORT_DESCRIPTION = 'README.short'
FULL_DESCRIPTION  = 'README.rst'

from os import path
desc_file = path.join(path.abspath(path.dirname(__file__)), FULL_DESCRIPTION)
with open(desc_file, encoding='utf-8') as df: long_description = df.read()

MINIMUM_REQUESTS_VERSION = '2.28.1'
REQUIRES      = [ 'requests>=%s' % MINIMUM_REQUESTS_VERSION ]
PLATFORM      = 'any'

CLASSIFIERS   =  [ 'Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3.9',
                   'Programming Language :: Python :: 3.10',
                   'Programming Language :: Python :: 3.11',
                   'Programming Language :: Python :: 3.12',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Software Development :: Libraries',
                 ]
DOCUMENTATION = 'http://pyral.readthedocs.io/en/latest/'

setup(name=PACKAGE,
      packages=[PACKAGE],
      version=VERSION,
      description=OFFICIAL_NAME,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=GITHUB_SITE,
      download_url=DOWNLOADABLE_ZIP,
      long_description=long_description,
      long_description_content_type='text/x-rst',
      license=LICENSE,
      keywords=KEYWORDS,
      install_requires=REQUIRES,
      classifiers=CLASSIFIERS,
      python_requires='>=3.9'
     )

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

#try:
#    from distutils2.core import setup
#except:
#    try:
#        from distutils.core import setup
#    except:
#        from setuptools import setup

from setuptools import setup

PACKAGE       = 'pyral'
VERSION       = '1.2.4'
OFFICIAL_NAME = 'Python toolkit for Rally REST API'
PKG_URL_NAME  = 'python-toolkit-rally-rest-api'
AUTHOR        = 'Kip Lehman (Rally Software Development)'
AUTHOR_EMAIL  = 'klehman@rallydev.com'
LICENSE       = 'BSD'
GITHUB_SITE   = 'https://github.com/RallyTools/RallyRestToolkitForPython'
GITHUB_DISTS  = '%s/raw/master/dists' % GITHUB_SITE
DOWNLOADABLE_ZIP = '%s/%s-%s.zip' % (GITHUB_DISTS, PACKAGE, VERSION)
SHORT_DESCRIPTION = 'README.short'
FULL_DESCRIPTION  = 'README.rst'
KEYWORDS      = ['rally', 'agilecentral', 'api']

MINIMUM_REQUESTS_VERSION = '2.8.1'  # test this with 2.12.5
REQUIRES      = ['six', 
                 'requests>=%s' % MINIMUM_REQUESTS_VERSION
                ]
PLATFORM      = 'any'

CLASSIFIERS   =  [ 'Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.5',
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
      long_description=open(FULL_DESCRIPTION, 'r').read(),
      license=LICENSE,
      keywords=KEYWORDS,
      install_requires=REQUIRES,
      classifiers=CLASSIFIERS
    )
        

#!/usr/bin/env python
# -*- coding: utf-8 -*-

#try:
#    from distutils2.core import setup
#except:
#    try:
#        from distutils.core import setup
#    except:
#        from setuptools import setup

from setuptools import setup

PACKAGE       = 'pyral'
VERSION       = '1.5.0'
OFFICIAL_NAME = 'Python toolkit for Rally REST API'
PKG_URL_NAME  = 'python-toolkit-rally-rest-api'
AUTHOR        = 'Kip Lehman (Broadcom, Enterprise Software Division)'
AUTHOR_EMAIL  = 'kip.lehman@broadcom.com'
LICENSE       = 'BSD'
KEYWORDS      = ['rally', 'api']
GITHUB_SITE   = 'https://github.com/RallyTools/RallyRestToolkitForPython'
GITHUB_DISTS  = '%s/raw/master/dists' % GITHUB_SITE
DOWNLOADABLE_ZIP = '%s/%s-%s.zip' % (GITHUB_DISTS, PACKAGE, VERSION)
SHORT_DESCRIPTION = 'README.short'
FULL_DESCRIPTION  = 'README.rst'
LONG_DESCRIPTION  = ""
with open(FULL_DESCRIPTION, 'r') as d:
    LONG_DESCRIPTION = d.read()

MINIMUM_REQUESTS_VERSION = '2.12.5'  # although 2.22.x is recommended
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
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
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
      long_description=LONG_DESCRIPTION,
      long_description_type='text/x-rst',
      license=LICENSE,
      keywords=KEYWORDS,
      install_requires=REQUIRES,
      classifiers=CLASSIFIERS
     )


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

try:
    from distutils2.core import setup
except:
    try:
        from distutils.core import setup
    except:
        from setuptools import setup

PACKAGE       = 'pyral'
VERSION       = '1.0.2'
OFFICIAL_NAME = 'Python toolkit for Rally REST API'
PKG_URL_NAME  = 'python-toolkit-rally-rest-api'
AUTHOR        = 'Kip Lehman (Rally Software Development)'
AUTHOR_EMAIL  = 'klehman@rallydev.com'
GITHUB_SITE   = 'https://github.com/RallyTools/RallyRestToolkitForPython'
GITHUB_DISTS  = '%s/blob/master/dists' % GITHUB_SITE
DOWNLOADABLE_ZIP = '%s/%s-%s.zip' % (GITHUB_DISTS, PACKAGE, VERSION)

MINIMUM_REQUESTS_VERSION = '2.0.0'

setup(name=PACKAGE,
      version=VERSION,
      description=OFFICIAL_NAME,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=GITHUB_SITE,
      download_url=DOWNLOADABLE_ZIP,
      long_description=open('README.rst').read(),
      packages=[PACKAGE],
      license='BSD',
      requires=["python (< 3.0)"],
      #install_requires=['requests>=%s' % MINIMUM_REQUESTS_VERSION],
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Topic :: Internet :: WWW/HTTP',
            'Topic :: Software Development :: Libraries',
        ],
      #documentation='http://readthedocs.org/docs/pyral'
    )
        

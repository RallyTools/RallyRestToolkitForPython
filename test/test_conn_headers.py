#!/usr/bin/env python

import sys, os
import types
import time
import re

import pyral
from pyral import Rally

##################################################################################################

from rally_targets import RALLY, APIKEY

##################################################################################################

def test_basic_connection_with_a_header():
    """
        Using a known valid Rally server and access credentials, issue a simple query 
        request against a known valid Rally entity.
    """
    headers = {'name': 'Fungibles Goods Burn Up/Down', 'vendor': 'Archimedes', 'version': '1.2.3'}
    rally = Rally(RALLY, apikey=APIKEY, headers=headers)
    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200
    time.sleep(1)



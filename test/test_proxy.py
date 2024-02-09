#!/usr/bin/env python

import sys, os
import types
import py
import pytest
import time
import re

import pyral
from pyral import Rally

RallyRESTAPIError  = pyral.context.RallyRESTAPIError
RallyResponseError = pyral.rallyresp.RallyResponseError

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD   #, HTTPS_PROXY
from rally_targets import PROD, APIKEY
from rally_targets import PROD_USER, PROD_PSWD

HTTPS_PROXY = 'localhost:8899'

##################################################################################################

def test_basic_connection():
    """
        Using a known valid Rally server and access credentials, issue a simple query 
        request against a known valid Rally entity.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200
    time.sleep(1)

def test_basic_proxied_connection():
    """
        Using a known valid Rally server and access credentials, issue a simple query 
        request against a known valid Rally entity via use of https_proxy.
    """
    os.environ['https_proxy'] = "http://%s" % HTTPS_PROXY

    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200

    os.environ['https_proxy'] = ""
    del os.environ['https_proxy']
    time.sleep(1)

#def test_connection_proxy_with_api_key():
#    """
#        Using a known valid Rally server and access credentials, issue a simple query 
#        request against a known valid Rally entity via use of https_proxy.
#    """
#    os.environ['https_proxy'] = "http://%s" % HTTPS_PROXY
#
#    rally = Rally(server=RALLY, apikey=API_KEY)
#    rally.setWorkspace('Rally')
#    projects = rally.getProjects()
#    project_names = sorted([proj.Name for proj in projects])
#    AWESOME_PROJECT = 'Alligator Tiers'
#    assert AWESOME_PROJECT in project_names
#    response = rally.get('Project', fetch=False, limit=10)
#    assert response != None
#    assert response.status_code == 200
#    rally.setProject(AWESOME_PROJECT)
#    project = rally.getProject()
#    assert project.Name == AWESOME_PROJECT
    


##########################################################################################


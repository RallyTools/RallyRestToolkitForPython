#!/usr/bin/env python

import sys, os
import types
import py
import time
import re

import pyral
from pyral import Rally

RallyRESTAPIError  = pyral.context.RallyRESTAPIError
RallyResponseError = pyral.rallyresp.RallyResponseError

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD, HTTPS_PROXY
from rally_targets import PROD, APIKEY
from rally_targets import PROD_USER, PROD_PSWD

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

#def test_basic_proxied_connection():
#    """
#        Using a known valid Rally server and access credentials, issue a simple query 
#        request against a known valid Rally entity via use of https_proxy.
#    """
#    os.environ['https_proxy'] = "http://%s" % HTTPS_PROXY
#
#    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
#    response = rally.get('Project', fetch=False, limit=10)
#    assert response != None
#    assert response.status_code == 200
#
#    os.environ['https_proxy'] = ""
#    del os.environ['https_proxy']
#    time.sleep(1)

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
    

def test_basic_connection_with_apikey():
    """
        Using a known valid Rally server and valid API Key value, 
        issue a simple query request against a known valid Rally target.
    """
    rally = Rally(server=PROD, apikey=APIKEY)
    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200
    time.sleep(1)

def test_basic_connection_with_user_password_and_apikey():
    """
        Using a known valid Rally server and mush user and password values along
        with a valid API Key value, issue a simple query request against a known valid
        Rally target.
    """
    rally = Rally(PROD, "mush?", "mush!", apikey=APIKEY)
    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200
    time.sleep(1)


def test_basic_connection_with_bad_api_key():
    """
        Using a known valid Rally server and bogus API Key value, 
        issue a simple query request against a known valid Rally target.

        The result should be that the attempt raises an exception.
    """
    BOGUS_API_KEY = "_ABC123DEF456GHI789JKL012MNO345PQR678STUVZ"
    expectedErrMsg = 'Invalid credentials'
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(PROD, "zooka@fluffernetter.com", "manict0X0", apikey=BOGUS_API_KEY)
    actualErrVerbiage = excinfo.value.args[0]
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg == actualErrVerbiage
    time.sleep(1)

def test_basic_connection_with_good_up_and_bad_api_key():
    """
        Using a known valid Rally server and bogus API Key value, 
        but providing a valid user name and password, observe
        that the attempt to obtain a pyral Rally instance results
        in an exception raised that identifies Invalid credentials as the culprit.
    """
    BOGUS_API_KEY = "_ABC123DEF456GHI789JKL012MNO345PQR678STUVZ"
    expectedErrMsg = 'Invalid credentials'
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(PROD, user=PROD_USER, password=PROD_PSWD, apikey=BOGUS_API_KEY)
    actualErrVerbiage = excinfo.value.args[0]
    assert expectedErrMsg == actualErrVerbiage
    time.sleep(1)
    
def test_nonexistent_server():
    """
        Using a known invalid server specification, obtain a Rally instance.
        An exception should be generated with verbiage about the hostname
        being non-existent or unreachable.
        Use the py.test context manager idiom to catch the generated exception
        and do the relevant assertions.
    """
    bogus_server = "bogus.notreally.bug"
    expectedErrMsg = "Target Rally host: '%s' non-existent or unreachable" % bogus_server
    #print expectedErrMsg
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=bogus_server)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    #print actualErrVerbiage
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    #assert actualErrVerbiage == expectedErrMsg
    assert expectedErrMsg == actualErrVerbiage
    time.sleep(1)


def test_non_rally_server():
    """
        Use a known valid server reachable on the Internet that 
        *doesn't* service Rally REST API requests. 
        Do the same test using default access credentials and known correct
        valid credentials to an existing Rally server.
        The attempt must generate an Exception
    """
    non_rally_server = 'www.irs.gov'
    #non_rally_server = 'www.espn.com'

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=non_rally_server, timeout=5)
    print("Exception typename: %s" % excinfo.typename)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    print(actualErrVerbiage)
    expectedErrMsg = "Target host: '%s' is either not reachable or " % non_rally_server
    ex_value_mo = re.search(expectedErrMsg, actualErrVerbiage)
    assert ex_value_mo is not None
    time.sleep(1)


def test_bad_server_spec():
    """
        Use a known to be invalid server name using prohibited characters in the
        server name.
        Do the same test using default access credentials and known correct
        valid credentials to an existing Rally server.
        The status_code in the response must indicate a non-success condition.
    """
    bad_server = "ww!w.\fo,o\r\n.c%om"
    expectedErrMsg = "404 Target host: 'ww!w.\x0co,o\r\n.c%om' is either not reachable or doesn't support the Rally WSAPI"
    print("expectedErrMesssage |{0}|".format(expectedErrMsg))
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=bad_server, timeout=3)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    print("actualErrVerbiage   |{0}|".format(actualErrVerbiage))
    assert actualErrVerbiage == expectedErrMsg
    time.sleep(1)


def test_insuff_credentials():
    """
        good  username, empty  password
        empty username, doofus password
        empty username, empty  password
        'guest' username, empty  password
        'guest' username, doofus password

        Explicit None values for username, password, apikey
        Explicit None values for username and password, doofus apikey value

        test for HTTP code associated with 'not authorized' (401)
    """
    expectedErrMsg = 'Invalid credentials'

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=RALLY, user=RALLY_USER, password="")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected valid user, missing password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=RALLY, user="", password="doofus")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected blank user, invalid password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=RALLY, user="", password="")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected blank user and password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=RALLY, user="guest", password="")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected invalid user, blank password condition"
    time.sleep(1)
    
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=RALLY, user="guest", password="doofus")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected invalid user, invalid password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=RALLY, user="guest")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected invalid user, missing password condition"

##########################################################################################

#test_basic_connection()
#test_nonexistent_server()
#test_non_rally_server()
#test_bad_server_spec()
#test_insuff_credentials()


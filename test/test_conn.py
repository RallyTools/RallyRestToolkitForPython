#!/usr/local/bin/python2.7

import sys, os
import types
import py
import time

import pyral
from pyral import Rally

RallyRESTAPIError = pyral.context.RallyRESTAPIError

##################################################################################################

TRIAL = "trial.rallydev.com"
PROD  = "us1.rallydev.com"

#TRIAL_USER = "usernumbernine@acme.com"
#TRIAL_PSWD = "********"

HTTPS_PROXY = "127.0.0.1:9654"

##################################################################################################

def test_basic_connection():
    """
        Using a known valid Rally server and access credentials, issue a simple query 
        request against a known valid Rally entity.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
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

    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200

    os.environ['https_proxy'] = ""
    del os.environ['https_proxy']
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
    expectedErrMsg = "ping: cannot resolve %s: Unknown host" % bogus_server
    #print expectedErrMsg
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=bogus_server)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    #print actualErrVerbiage
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    #assert actualErrVerbiage == expectedErrMsg
    assert expectedErrMsg in actualErrVerbiage
    time.sleep(1)


#def test_nonexistent_bad_server_with_proxy():
#    """
#        Same as above test but this time going through a proxy.
#    """
#    os.environ['https_proxy'] = HTTPS_PROXY
#
#    bogus_server = "bogus.notreally.bug"
#    expectedErrMsg = "ping: cannot resolve %s: Unknown host" % bogus_server
#    with py.test.raises(RallyRESTAPIError) as excinfo:
#        rally = Rally(server=bogus_server)
#    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
#    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
#    assert actualErrVerbiage == expectedErrMsg
#
#    os.environ['https_proxy'] = ""
#    del os.environ['https_proxy']
#    time.sleep(1)


def test_non_rally_server():
    """
        Use a known valid server reachable on the Internet that 
        *doesn't* service Rally REST API requests. 
        Do the same test using default access credentials and known correct
        valid credentials to an existing Rally server.
        The attempt must generate an Exception
        The status_code in the response must indicate a non-success condition.
    """
    non_rally_server = 'www.irs.gov'
    expectedErrMsg = "404 Target host: '%s' doesn't support the Rally WSAPI" % non_rally_server
    timeoutMsg     = "Request timed out on attempt to reach %s" % non_rally_server
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=non_rally_server, timeout=5)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    #print "     expectedErrMsg: %s" % expectedErrMsg
    #print "  actualErrVerbiage: %s" % actualErrVerbiage
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert (actualErrVerbiage == expectedErrMsg or actualErrVerbiage == timeoutMsg)

    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=non_rally_server, 
                            user=TRIAL_USER, 
                            password=TRIAL_PSWD, timeout=5)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == expectedErrMsg
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
    expectedErrMsg = "Unknown host"
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=bad_server, timeout=3)
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert 'cannot resolve' in actualErrVerbiage and 'Unknown host' in actualErrVerbiage
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=bad_server, 
                            user=TRIAL_USER, 
                            password=TRIAL_PSWD, timeout=3)
        response = rally.get('Project', fetch=False, limit=5)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert 'cannot resolve' in actualErrVerbiage and 'Unknown host' in actualErrVerbiage
    time.sleep(1)

def test_insuff_credentials():
    """
        good  username, empty  password
        empty username, doofus password
        empty username, empty  password
        'guest' username, empty  password
        'guest' username, doofus password

        test for HTTP code associated with 'not authorized' (401)
    """
    expectedErrMsg = u"401 An Authentication object was not found in the SecurityContext"
    expectedErrMsg = u"The username or password you entered is incorrect"

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=TRIAL, user=TRIAL_USER, password="")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected valid user, missing password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=TRIAL, user="", password="doofus")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected blank user, invalid password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=TRIAL, user="", password="")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected blank user and password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=TRIAL, user="guest", password="")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected invalid user, blank password condition"
    time.sleep(1)
    
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=TRIAL, user="guest", password="doofus")
        response = rally.get('Project', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert expectedErrMsg in actualErrVerbiage
    #print "detected invalid user, invalid password condition"
    time.sleep(1)

    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally = Rally(server=TRIAL, user="guest")
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


#!/usr/bin/env python

import sys, os
import types
import py

from pyral import Rally
import pyral

InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError

##################################################################################################

from internal_rally_targets import APIKEY, WORKSPACE, PROJECT

##################################################################################################

def test_basic_search():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple search query (basic qualifying criteria).
    """
    rally = Rally(apikey=APIKEY, workspace=WORKSPACE, project=PROJECT)
    #
    #expectedErrMsg = u'The new search functionality is not turned on for your subscription'
    #
    #with py.test.raises(RallyRESTAPIError) as excinfo:
    #    response = rally.search('wombat', limit=10)
    #    actualErrVerbiage = excinfo.value.args[0]
    #    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    #    assert expectedErrMsg in actualErrVerbiage
    response = rally.search('bogus', limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount > 0
    print(response.resultCount)
    for entry in response:
        print(entry.ObjectID, entry.FormattedID, entry.Name)
        print("|" + entry.MatchingText + "|")


#def test_simple_named_fields_query():
#    """
#        Using a known valid Rally server and known valid access credentials,
#        issue a simple query (no qualifying criteria) for a known valid 
#        Rally entity. The fetch specifies a small number of known valid
#        attributes on the Rally entity.
#    """
#    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
#    response = rally.search('yellow display", limit=10)
#    assert response.status_code == 200
#    assert len(response.errors) == 0
#    assert len(response._page) > 0

#test_basic_search()
#test_simple_named_fields_query()

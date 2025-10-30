#!/usr/bin/env python

import sys, os
import types
import urllib

from pyral import Rally
import pyral

InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError
from pyral.query_builder import RallyUrlBuilder, RallyQueryFormatter

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD
from rally_targets import DEFAULT_WORKSPACE, NON_DEFAULT_PROJECT

##################################################################################################

def test_basic_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple filtering query targeting RecycleBinEntry items
        whose Name value does not contain a specific value.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    response = rally.get('RecycleBinEntry', fetch="ObjectID,ID,Name", 
                          query='Name = "Gone but not forgotten with the wind"',
                          limit=100)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount > 0
   #print(response.resultCount)
   #for entry in response:
   #    print("{:14d}  {:8s}  {:s}".format(entry.ObjectID, entry.ID, entry.Name))

#test_basic_query()


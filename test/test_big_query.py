#!/usr/bin/env python

import sys, os
import types
import urllib
import py

try:
    from urllib import unquote
except:
    from urllib.parse import unquote

import pyral
Rally = pyral.Rally
from pyral.cargotruck import CargoTruck

##################################################################################################

from rally_targets import AGICEN, AGICEN_USER, AGICEN_PSWD
#from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT, NON_DEFAULT_PROJECT
#from rally_targets import ORG_LEVEL_PROJECT
ORG_LEVEL_PROJECT = 'AC Engineering'

##################################################################################################

def test_multiple_page_response_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) against a Rally entity
        (Story) known to have more than 5 items.  Set the pagesize to 5 to
        force pyral to retrieve multiple pages to satisfy the query.
    """
    APIKEY    = '_x6CZhqQgiist6kTtwthsAAKHtjWE7ivqimQdpP3T4'
    WORKSPACE = 'Rally'
    PROJECT   = 'AC Engineering'
    rally = Rally(server=AGICEN, apikey=APIKEY, workspace=WORKSPACE, project=PROJECT)
    """
    response = rally.get('Story', fetch='ObjectID,FormattedID,Name', pagesize=100, limit=1500, projectScopeDown=True)
    count = 0
    for ix, story in enumerate(response):
        count += 1

    assert response.resultCount > 1000
    assert count <= response.resultCount
    assert count == 1500

    response = rally.get('Story', fetch='ObjectID,FormattedID,Name', pagesize=200, limit=11500, start=500, projectScopeDown=True)
    stories = [story for story in response]

    assert response.resultCount > 11000
    assert len(stories) <= response.resultCount
    assert len(stories) == 11500
    assert response.startIndex == 11900
    """

    response = rally.get('Story', fetch='ObjectID,FormattedID,Name', pagesize=1000, projectScopeDown=True)
    count = 0
    for istory in response:
        count += 1

    assert response.resultCount > 15000
    assert count == response.resultCount


def test_cargo_truck_init():
    cgo = CargoTruck(['a', 'b'], 2)
    assert len(cgo.orders) == 2
    assert cgo.orders[0] == 'a'
    assert cgo.num_loaders == 2
    print("at the end of the rope")

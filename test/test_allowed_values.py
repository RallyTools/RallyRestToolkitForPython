#!/usr/local/bin/python2.7

import sys, os
import types
import py

import pyral
from pyral import Rally

RallyRESTAPIError = pyral.context.RallyRESTAPIError

##################################################################################################

from rally_targets import AGICEN, AGICEN_USER, AGICEN_PSWD
from rally_targets import API_KEY

EXAMPLE_ATTACHMENT_CONTENT = "The quck brown fox eluded the lumbering sloth\n"

##################################################################################################

def test_getAllowedValues_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request allowed value information for the State field of the Defect entity.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    avs = rally.getAllowedValues('Defect', 'State')
    assert len(avs) > 0
    assert len(avs) >= 4
    assert 'Open' in avs
    assert 'Closed' in avs

    avs = rally.getAllowedValues('Defect', 'PrimaryColor')
    assert len(avs) > 0
    assert len(avs) >= 6 and len(avs) <= 8
    assert 'Red' in avs
    assert 'Magenta' in avs


def test_getAllowedValues_for_UserStory():
    """
        Using a known valid Rally server and known valid access credentials,
        request allowed value information for the Milestones field of the UserStory entity.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    avs = rally.getAllowedValues('Story', 'Milestones')
    assert len(avs) == 1
    assert avs == [True]


def test_getAllowedValues_for_custom_collections_field_Defect():
    rally = Rally(server=AGICEN, apikey=API_KEY, workspace='Rally', project='Rally')
    avs = rally.getAllowedValues('Defect', 'MobileOS')
    assert len(avs) > 0
    target_value = 'Android'
    assert len([v for v in avs if v == target_value]) == 1

##########################################################################################



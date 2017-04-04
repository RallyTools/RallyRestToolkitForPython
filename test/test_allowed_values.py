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
from rally_targets import LARGE_WORKSPACE, LARGE_PROJECT_TREE_BASE

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
    assert 'Open'   in avs
    assert 'Closed' in avs

    avs = rally.getAllowedValues('Defect', 'PrimaryColor')
    assert len(avs) > 0
    assert len(avs) >= 6 and len(avs) <= 8
    assert 'Red'     in avs
    assert 'Magenta' in avs


def test_getAllowedValues_for_UserStory_Milestone():
    """
        Using a known valid Rally server and known valid access credentials,
        request allowed value information for the Milestones field of the UserStory entity.
        The Milestones field is a standard field of schema type COLLECTION whose value
        is entirely context dependent on the specific artifact so getting allowed values
        doesn't really make sense in the same way as an attribute like State or Severity
        that has a finite set of possible values that are the same for every Story or Defect
        in the workspace.  Because of that characteristic, we return no allowed values for
        the Milestones attribute on the Story type.  There are numerous other standard attributes
        with the same sort of semantic that are excluded from chasing the COLLECTION url and
        returning some list of values.  (like, Changesets, Discussions, Tags, etc.)
    """
    rally = Rally(server=AGICEN, apikey=API_KEY)
    response = rally.get('Milestone', fetch=True, workspace=LARGE_WORKSPACE,
                           project=LARGE_PROJECT_TREE_BASE, projectScopeDown=True)
    milestones = [item for item in response]
    assert len(milestones) > 150

    avs = rally.getAllowedValues('Story', 'Milestone')
    assert avs is None


def test_getAllowedValues_for_custom_collections_field_Defect():
    rally = Rally(server=AGICEN, apikey=API_KEY, workspace='Rally', project='Rally')
    avs = rally.getAllowedValues('Defect', 'MobileOS')
    assert len(avs) > 0
    target_value = 'Android'
    assert len([v for v in avs if v == target_value]) == 1

##########################################################################################



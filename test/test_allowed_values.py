#!/usr/bin/env python

import sys, os
import types
import py

import pyral
from pyral import Rally

RallyRESTAPIError = pyral.context.RallyRESTAPIError

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD
#from rally_targets import APIKEY
from internal_rally_targets import APIKEY
from rally_targets import LARGE_WORKSPACE, LARGE_PROJECT_TREE_BASE

##################################################################################################

def test_getAllowedValues_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request the allowed value information for the State field of the Defect entity and
        request the allowed value information for the PrimaryColor field of the Defect entity.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
        in the workspace.  Because of that characteristic, we return a list with a single True
        value ( [True] ) to designate that yes, technically the Milestones field has allowed
        values but that asking for them on a specific AC artifact short-circuits.  The proper
        way to get all of the AllowedValues for Milestones is to query the Milestone entity 
        itself.  There are numerous other standard attributes
        with the same sort of semantic that are excluded from chasing the COLLECTION url and
        returning some list of values.  (like, Changesets, Discussions, Tags, etc.)
    """
    rally = Rally(server=RALLY, apikey=APIKEY)

    avs = rally.getAllowedValues('Story', 'Milestones')
    assert avs == [True]

    response = rally.get('Milestone', fetch=True, workspace=LARGE_WORKSPACE,
                           project=LARGE_PROJECT_TREE_BASE, projectScopeDown=True)
    milestones = [item for item in response]
    assert len(milestones) > 150

    # Given the singular name of the target field (which is invalid...) return a None value
    avs = rally.getAllowedValues('Story', 'Milestone')
    assert avs is None


def test_getAllowedValues_for_custom_collections_field_Defect():
    rally = Rally(server=RALLY, apikey=APIKEY, workspace='Rally', project='Rally')
    avs = rally.getAllowedValues('Defect', 'MobileOS')
    assert len(avs) > 0
    target_value = 'Android'
    assert len([v for v in avs if v == target_value]) == 1

    pavs = rally.getAllowedValues('Defect', 'RootCause')
    assert [av for av in pavs if av == 'Implementation']
    assert [av for av in pavs if av == 'Performance']
    assert [av for av in pavs if av == 'Usability']

##########################################################################################



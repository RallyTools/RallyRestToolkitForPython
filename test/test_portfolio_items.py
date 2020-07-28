#!/usr/bin/env python

import sys, os
import types
import pprint

from pyral import Rally

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD, API_KEY
from rally_targets import RALLY_NICKNAME, DEFAULT_WORKSPACE

##################################################################################################

def test_getSchemaInfo():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and call the getSchemaInfo method for the
        default workspace.
    """
    rally = Rally(server=RALLY, apikey=API_KEY)
    rally.setWorkspace('NMTest')
    schema_info = rally.getSchemaInfo(rally.getWorkspace())
    assert type(schema_info) == list
    assert len(schema_info) > 50
    subs_schema = [item for item in schema_info if item['Name'] == 'Subscription']
    assert subs_schema != None
    assert len(subs_schema) == 1
    assert type(subs_schema) == list
    assert u'Attributes' in subs_schema[0]
    assert len(subs_schema[0][u'Attributes']) > 15

    epic_schema = [item for item in schema_info if item['Name'] == 'Epic']
    assert epic_schema != None


def test_typedef():
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.typedef convenience method using 'Portfolio/Epic'
        as a target.
    """
    rally = Rally(server=RALLY, apikey=API_KEY)
    rally.setWorkspace('NMTest')
    target_type = 'PortfolioItem/Epic'
    td = rally.typedef(target_type)
    assert td != None
    assert td._type == 'TypeDefinition'
    assert td.TypePath == 'PortfolioItem/Epic'
    assert td.ref.startswith('typedefinition/')

def test_epic_creation():
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.create method to create an Epic instance and be handed
        back a usable pyral.entity representing the newly created Epic PortfoloItem instance.
    """
    rally = Rally(server=RALLY, apikey=API_KEY)
    rally.setWorkspace('NMTest')
    target_workspace = rally.getWorkspace()
    rally.setProject('Unbearable MFA music')
    target_project = rally.getProject()
    #response = rally.get('Feature', fetch=True, workspace=target_workspace.Name, project=None, instance=True)
    #if response.resultCount == 0:
    #    raise Exception("Unable to retrieve any Feature items...  so sad")
    #features = [f for f in response]
    #feature = [f for f in features if f.FormattedID == 'F1']

    feature = rally.get('Feature', fetch=True, query='FormattedID = F1', workspace=target_workspace.Name, project=None, instance=True)
    info = {
             "Workspace"   : target_workspace._ref,
             "Project"     : target_project._ref,
             "Name"        : "VacuumHajCracklings",
             "Description" : "420 CuHectare capacity.  It is a big place and partygoers are sloppy.  Big fast clean mandatory."
             #"Notes"       : "Hoover or Dustmatic it makes no difference",
             #"Ready"       : False,
             #"Parent"      : feature._ref
           }

    print("Creating Epic ...")
    epic = rally.put('Epic', info)
    assert epic
    assert epic.Name == 'VacuumHajCracklings'
    print("Created  Epic: %s   OID: %s  Name: %s   Description: %s" % (epic.FormattedID, epic.oid, epic.Name, epic.Description))
    assert epic.Ready == False

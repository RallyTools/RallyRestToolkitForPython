#!/usr/bin/env python

import sys, os
import types
import pprint

from pyral import Rally

##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD
from rally_targets import TRIAL_NICKNAME, DEFAULT_WORKSPACE

##################################################################################################

def test_getSchemaInfo():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and call the getSchemaInfo method for the
        default workspace.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    schema_info = rally.getSchemaInfo(rally.getWorkspace())
    assert isinstance(schema_info, list)
    assert len(schema_info) > 50
    subs_schema = [item for item in schema_info if item['Name'] == 'Subscription']
    assert subs_schema != None
    assert len(subs_schema) == 1
    assert isinstance(subs_schema, list)
    assert 'Attributes' in subs_schema[0]
    assert len(subs_schema[0]['Attributes']) > 15

def test_getWorkspace():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity. The fetch specifies a small number of known valid
        attributes on the Rally entity.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert int(workspace.oid) > 10000
    assert len(workspace.Name) > 6
    assert workspace.ref.startswith('workspace/')

def test_getProject():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, version="v2.0")
    response = rally.get('Project', fetch=False, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []

    assert response.resultCount > 0
    proj_rec = next(response)
    #print proj_rec._ref
    #print proj_rec.ref
    #print proj_rec.oid
    assert proj_rec.oid > 0

def test_getUserInfo_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request the information associated with a single username.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifiers = rally.getUserInfo(username=TRIAL_USER)
    assert len(qualifiers) == 1
    user = qualifiers.pop()
    assert user.Name     == TRIAL_NICKNAME
    assert user.UserName == TRIAL_USER
    assert user.UserProfile.DefaultWorkspace.Name == DEFAULT_WORKSPACE
    #assert user.Role == 'CONTRIBUTOR'  # or this may be set to ORGANIZER
    #assert user.Role == 'Developer'  # not set for yeti@rallydev.com on the trial instance...
    #ups = [up for up in user.UserPermissions]
    #assert len(ups) > 0
    #up = ups.pop(0)
    #assert up.Role == 'Admin'

def test_getAllUsers_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request information about every user associated with the current subscription.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    everybody = rally.getAllUsers()
    assert len(everybody) > 0
    assert len([user for user in everybody if user.DisplayName == 'Integrations Test']) == 1

def test_getAllowedValues_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request allowed value information for the State field of the Defect entity.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    avs = rally.getAllowedValues('Defect', 'State')
    assert len(avs) > 0
    assert len(avs) == 6
    assert 'Open' in avs
    assert 'Closed' in avs

def test_typedef():
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.typedef convenience method using 'Portfolio/Feature' 
        as a target.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    target_type = 'PortfolioItem/Feature'
    td = rally.typedef(target_type)
    assert td != None
    assert td._type == 'TypeDefinition'
    assert td.TypePath == 'PortfolioItem/Feature'
    assert td.ref.startswith('typedefinition/')

def test_getStates():
    """
        Using a known valid Rally server and known valid access credentials,
        get all the State entity instances for Thme via the
        Rally.getStates convenience method.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    target_entity = 'Theme'
    states = rally.getStates(target_entity)
    assert len(states) == 4
    discovering = [state.Name for state in states if state.Name == "Discovering"]
    assert len(discovering) == 1

def test_getCollection():
    """
        Using a known valid Rally server and known valid access credentials,
        get the default workspace record and confabulate the projects collection
        url using the workspace.ObjectID.
        Call the rally.getCollection with the confabulated collection url.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace is not None
    proj_collection_url = "http://%s/slm/webservice/v2.0/Workspace/%s/Projects" % (TRIAL, workspace.ObjectID)
    response = rally.getCollection(proj_collection_url)
    assert response.__class__.__name__ == 'RallyRESTResponse'
    projects = [proj for proj in response]
    assert len(projects) > 30
    assert projects.pop(0).__class__.__name__ == 'Project'
    

#test_getSchemaInfo()
#test_getWorkspace()
#test_getProject()
#test_getUserInfo_query()
#test_getAllUsers_query()
#test_getAllowedValues_query()
#test_typedef
#test_getStates
#test_getCollection

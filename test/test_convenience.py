#!/usr/bin/env python

import sys, os
import types
import pprint

from pyral import Rally

##################################################################################################

from rally_targets import AGICEN, AGICEN_USER, AGICEN_PSWD
from rally_targets import AGICEN_NICKNAME, DEFAULT_WORKSPACE

##################################################################################################

def test_getSchemaInfo():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and call the getSchemaInfo method for the
        default workspace.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    schema_info = rally.getSchemaInfo(rally.getWorkspace())
    assert type(schema_info) == list
    assert len(schema_info) > 50
    subs_schema = [item for item in schema_info if item['Name'] == 'Subscription']
    assert subs_schema != None
    assert len(subs_schema) == 1
    assert type(subs_schema) == list
    assert u'Attributes' in subs_schema[0]
    assert len(subs_schema[0][u'Attributes']) > 15

def test_getWorkspace():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity. The fetch specifies a small number of known valid
        attributes on the Rally entity.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
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
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD, version="v2.0")
    response = rally.get('Project', fetch=False, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []

    assert response.resultCount > 0
    proj_rec = response.next()
    #print proj_rec._ref
    #print proj_rec.ref
    #print proj_rec.oid
    assert proj_rec.oid > 0

def test_getUserInfo_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request the information associated with a single username.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    qualifiers = rally.getUserInfo(username=AGICEN_USER)
    assert len(qualifiers) == 1
    user = qualifiers.pop()
    assert user.Name     == AGICEN_NICKNAME
    assert user.UserName == AGICEN_USER
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
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    everybody = rally.getAllUsers()
    assert len(everybody) > 0
    assert len([user for user in everybody if user.DisplayName == 'da Kipster']) == 1

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

def test_typedef():
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.typedef convenience method using 'Portfolio/Feature' 
        as a target.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    target_type = 'PortfolioItem/Feature'
    td = rally.typedef(target_type)
    assert td != None
    assert td._type == 'TypeDefinition'
    assert td.TypePath == 'PortfolioItem/Feature'
    assert td.ref.startswith('typedefinition/')

def test_getStates():
    """
        Using a known valid Rally server and known valid access credentials,
        get all the State entity instances for Initiative via the
        Rally.getStates convenience method.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    target_entity = 'Initiative'
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
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    workspace = rally.getWorkspace()
    assert workspace is not None
    proj_collection_url = "http://%s/slm/webservice/v2.0/Workspace/%s/Projects" % (AGICEN, workspace.ObjectID)
    response = rally.getCollection(proj_collection_url)
    assert response.__class__.__name__ == 'RallyRESTResponse'
    projects = [proj for proj in response]
    assert len(projects) >= 2
    assert projects.pop(0).__class__.__name__ == 'Project'
    for project in projects:
        print(project.details())
        print('')
        print('--------------------------------------------------------')
        print('')
    

#test_getSchemaInfo()
#test_getWorkspace()
#test_getProject()
#test_getUserInfo_query()
#test_getAllUsers_query()
#test_getAllowedValues_query()
#test_typedef
#test_getStates
#test_getCollection

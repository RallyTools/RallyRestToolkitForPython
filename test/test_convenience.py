#!/opt/local/bin/python2.6

import sys, os
import types

from pyral import Rally

##################################################################################################

PREVIEW = "preview.rallydev.com"
DEMO    = "demo.rallydev.com"
PROD    = "rally1.rallydev.com"

PREVIEW_USER = "usernumbernine@acme.com"
PREVIEW_PSWD = "************"

##################################################################################################

def test_get_workspace():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity. The fetch specifies a small number of known valid
        attributes on the Rally entity.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    workspace = rally.getWorkspace()
    assert int(workspace.oid) > 10000
    assert len(workspace.Name) > 6
    assert workspace.ref.startswith('workspace/')

def test_get_project():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('Project', fetch=False, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount > 0
    proj_rec = response.next()
    print proj_rec._ref
    print proj_rec.ref
    print proj_rec.oid

def test_user_info_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request the information associated with a single username.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    qualifiers = rally.getUserInfo(username='paul@acme.com')
    assert len(qualifiers) == 1
    user = qualifiers.pop()
    assert user.Name == 'Paul'
    assert user.UserName == 'paul@acme.com'
    assert user.UserProfile.DefaultWorkspace.Name == 'User Story Pattern'
    assert user.Role == 'ORGANIZER'
    ups = [up for up in user.UserPermissions]
    assert len(ups) > 0
    up = ups.pop(0)
    assert up.Role == 'Admin'

def test_all_users_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request information about every user associated with the current subscription.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    everybody = rally.getAllUsers()
    assert len(everybody) > 0
    assert len([user for user in everybody if user.DisplayName == 'Sara']) == 1


def test_allowed_values_query():
    """
        Using a known valid Rally server and known valid access credentials,
        request allowed value information for the State field of the Defect entity.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    avs = rally.getAllowedValues('Defect', 'State')
    assert len(avs) > 0
    assert len(avs) == 4
    assert u'Open' in avs
    assert u'Closed' in avs


#test_get_workspace()
#test_get_project()
#test_user_info_query()
#test_all_users_query()
#test_allowed_values_query()

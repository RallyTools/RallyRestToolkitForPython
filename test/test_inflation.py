#!/usr/bin/env python

import sys, os
import time
import types
import py

from pyral import Rally, RallyRESTAPIError

##################################################################################################

from rally_targets import AGICEN, AGICEN_USER, AGICEN_PSWD, DEFAULT_WORKSPACE, DEFAULT_PROJECT
from rally_targets import ALTERNATE_WORKSPACE

##################################################################################################

def test_default_connection():
    """
        Using a known valid Rally server and access credentials, 
        connect without specifying workspace or project.
        Return status should be OK, 
        Rally._wpCacheStatus should be 'minimal'
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200
    assert rally._wpCacheStatus() == 'minimal'


def test_default_workspace_with_named_default_project():
    """
        Using valid Rally access credentials, connect
        without specifying the workspace, specify the name of project
        which is the default project name.
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    project = 'Sample Project'
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                  project=project)
    response = rally.get('Project', fetch=False)
    assert response != None
    assert response.status_code == 200
    assert rally._wpCacheStatus() == 'minimal'

def test_default_workspace_non_default_valid_project():
    """
        Using valid Rally access credentials, connect
        without specifying the workspace, specify the name of project (not the default)
        which is valid for the default workspace.
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    project = 'My Project'
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                  project=project)
    response = rally.get('Project', fetch=False)
    assert response != None
    assert response.status_code == 200
    assert rally._wpCacheStatus() == 'minimal'

def test_default_workspace_non_valid_project():
    """
        Using valid Rally access credentials, connect
        without specifying the workspace, specify the name of project (not the default)
        which is not valid for the default workspace.
        An exception should be raised.
    """
    project = 'Halfling Leaf Pipe'
    problem = "The current Workspace '%s' does not contain an accessible Project with the name of '%s'"
    expectedErrMsg = problem % (DEFAULT_WORKSPACE, project)
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                      project=project)
    actualErrVerbiage = excinfo.value.args[0] 
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == expectedErrMsg

def test_named_default_workspace_use_default_project():
    """
        Using valid Rally access credentials, connect
        specifying the workspace name (which is the default value), 
        without specifying the name of project.
        Inquire after connecting as to what the current project is.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                  workspace=DEFAULT_WORKSPACE)
    project = rally.getProject()
    assert project != None
    assert project.Name == DEFAULT_PROJECT


def test_named_default_workspace_named_default_project():
    """
        Using valid Rally access credentials, connect
        specifying the workspace name (which is the default value), 
        specifying the name of project (which is the default value).
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                  workspace=DEFAULT_WORKSPACE, project=DEFAULT_PROJECT)
    response = rally.get('Project')
    assert response != None
    assert response.status_code == 200
    assert rally._wpCacheStatus() == 'minimal'

def test_named_default_workspace_named_valid_project():
    """
        Using valid Rally access credentials, connect
        specifying the workspace name (which is the default value), 
        specifying the name of a valid project (not the default value).
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    project   = 'My Project'
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                  workspace=DEFAULT_WORKSPACE, project=project)
    response = rally.get('Project')
    assert response != None
    assert response.status_code == 200
    assert rally._wpCacheStatus() == 'minimal'

def test_named_default_workspace_named_invalid_project():
    """
        Using valid Rally access credentials, connect
        specifying the workspace name (which is the default value), 
        specifying the name of an invalid project.
        An exception should be raised.
    """
    project = 'Sailor Sami'
    problem = "The current Workspace '%s' does not contain an accessible Project with the name of '%s'"
    expectedErrMsg = problem % (DEFAULT_WORKSPACE, project)
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                      workspace=DEFAULT_WORKSPACE, project=project)
    actualErrVerbiage = excinfo.value.args[0] 
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == expectedErrMsg

def test_named_non_default_workspace_use_default_project():
    """
        Using valid Rally access credentials, connect specifying
        a valid non-default workspace but not specifying a project.
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'narrow'

        Expanded this to incorporate two scenarios
            1) default project in default workspace is a valid project name
                in the named non-default workspace
            2) default project in default workspace is not a valid project name
                in the named non-default workspace
              
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                  workspace=ALTERNATE_WORKSPACE, warn=False)
    ai_proj = rally.getProject()
    assert str(ai_proj.Name) == 'Sample Project'  
    assert rally._wpCacheStatus() == 'narrow'

    #alt_project   = "Modus Operandi"
    #rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
    #              workspace=ALTERNATE_WORKSPACE,  project=alt_project, warn=False)
    #ai_proj = rally.getProject()
    #assert str(ai_proj.Name) == alt_project # is valid only in ALTERNATE_WORKSPACE
    #assert rally._wpCacheStatus() == 'narrow'

def test_named_non_default_workspace_named_valid_project():
    """
        Using valid Rally access credentials, connect specifying
        a valid non-default workspace and a valid project.
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    workspace   = "Kip's Playground"
    alt_project = 'Modus Operandi'
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD, workspace=workspace, warn=False)
    response = rally.get('Project')
    assert response != None
    assert response.status_code == 200
    assert rally._wpCacheStatus() == 'narrow'

    rally.setProject(alt_project)
    proj = rally.getProject()
    assert proj.Name == alt_project
    

def test_named_non_default_workspace_named_invalid_project():
    """
        Using valid Rally access credentials, connect specifying
        a valid non-default workspace and an invalid project.
        An exception should be raised.
    """
    workspace = ALTERNATE_WORKSPACE
    project   = 'Barney Rubble'
    problem = "The current Workspace '%s' does not contain an accessible Project with the name of '%s'"
    expectedErrMsg = problem % (ALTERNATE_WORKSPACE, project)
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD,
                  workspace=workspace, project=project, timeout=10)
        response = rally.get('Project', fetch=False, limit=5)
    actualErrVerbiage = excinfo.value.args[0] 
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == expectedErrMsg 

########################################################################################

#test_default_connection()
#test_default_workspace_with_named_default_project()
#test_default_workspace_non_default_valid_project()
#test_default_workspace_non_valid_project()

#test_named_default_workspace_use_default_project()
#test_named_default_workspace_named_default_project()
#test_named_default_workspace_named_valid_project()
#test_named_default_workspace_named_invalid_project()

#test_named_non_default_workspace_use_default_project()
#test_named_non_default_workspace_named_valid_project()
#test_named_non_default_workspace_named_invalid_project()

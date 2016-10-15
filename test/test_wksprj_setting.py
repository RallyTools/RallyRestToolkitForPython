#!/usr/bin/env python

import sys, os
import types

import py

from pyral import Rally, RallyUrlBuilder


##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD
from rally_targets import   DEFAULT_WORKSPACE,   DEFAULT_PROJECT
from rally_targets import ALTERNATE_WORKSPACE, ALTERNATE_PROJECT

##################################################################################################

#ALTERNATE_PROJECT   = 'Dynamic'

##################################################################################################

def test_get_default_workspace():
    """
        Using a known valid Rally server and known valid access credentials,
        and specifying the default workspace and project, verify that
        calling the getWorkspace method returns info for the default
        workspace.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=DEFAULT_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE

def test_get_non_default_workspace():
    """
        Using a known valid Rally server and known valid access credentials,
        and specifying the default workspace and project, verify that
        after having called setWorkspace on a valid but non-default 
        workspace value, the getWorkspace call correctly returns the
        newly set workspace value.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    rally.setWorkspace(ALTERNATE_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE

def test_warn_on_setting_invalid_workspace():
    """
        Using a known valid Rally server and known valid access credentials,
        and specifying the default workspace and project, verify that
        after having called setWorkspace on an invalid workspace, that
        something like a warning occurs and that a subsequent call to
        getWorkspace returns the default workspace.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    py.test.raises(Exception, "rally.setWorkspace('Constant Misbehavior')")
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE

def test_warn_on_setting_invalid_project():
    """
        Using a known valid Rally server and known valid access credentials,
        and specifying the default workspace and project, verify that
        after having called setProject on an invalid project, that
        something like a warning occurs and that a subsequent call to
        getProject returns the default project.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT
    py.test.raises(Exception, "rally.setProject('Thorny Buxcuit Weevilz')")
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

def test_disallow_project_value_invalid_for_workspace():
    """
        Using a known valid Rally server and known valid access credentials,
        and specifying the default workspace and project that does not exist 
        in that workspace, issue an Exception that prevents further processing.
    """
    problem_text = "No valid Project with the name 'Argonaut' found in the Workspace 'AC WSAPI Toolkit Python'"
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, 
                      workspace=DEFAULT_WORKSPACE, project=ALTERNATE_PROJECT, server_ping=False)
    actualErrVerbiage = excinfo.value.args[0]
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text


def test_get_project():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=DEFAULT_WORKSPACE, project='Sample Project')
    response = rally.get('Project', fetch=False, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    #assert response.warnings == []
    assert response.resultCount > 0
    proj = rally.getProject()
    assert str(proj.Name) == 'Sample Project'

def test_get_named_project():
    """
        Using a known valid Rally server and known valid access credentials,
        call the Rally.getProject using a valid (but non-default and non-current)
        project name as a parameter to the call.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=DEFAULT_WORKSPACE, project='Sample Project')
    response = rally.get('Project', fetch=False, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    #assert response.warnings == []
    assert response.resultCount > 0
    proj = rally.getProject('My Project')
    assert str(proj.Name) == 'My Project'

#test_get_workspace()
#test_get_project()

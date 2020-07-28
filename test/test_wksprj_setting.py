#!/usr/bin/env python

import sys, os
import types

import py

from pyral import Rally, RallyUrlBuilder


##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD
from rally_targets import   DEFAULT_WORKSPACE,   DEFAULT_PROJECT
from rally_targets import ALTERNATE_WORKSPACE, ALTERNATE_PROJECT
from rally_targets import API_KEY
from rally_targets import ACCOUNT_WITH_NO_DEFAULTS_CREDENTIALS

##################################################################################################

def test_get_default_workspace():
    """
        Using a known valid Rally server and known valid access credentials,
        and specifying the default workspace and project, verify that
        calling the getWorkspace method returns info for the default
        workspace.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, workspace=DEFAULT_WORKSPACE)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    problem_text = "The current Workspace '%s' does not contain an accessible Project with the name of '%s'" % (DEFAULT_WORKSPACE, ALTERNATE_PROJECT)
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD,
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, workspace=DEFAULT_WORKSPACE, project='Sample Project')
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, workspace=DEFAULT_WORKSPACE, project='Sample Project')
    response = rally.get('Project', fetch=False, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    #assert response.warnings == []
    assert response.resultCount > 0
    proj = rally.getProject('My Project')
    assert str(proj.Name) == 'My Project'

def test_no_defaults_good_workspace_none_project():
    no_defaults_user, no_defaults_password = ACCOUNT_WITH_NO_DEFAULTS_CREDENTIALS
    nd_workspace = "NMTest"
    none_project = None
    problem = "The current Workspace '%s' does not contain a Project with the name of '%s'"
    problem_text = problem % (nd_workspace, none_project)

    with py.test.raises(Exception) as excinfo:
        rally = Rally(RALLY, no_defaults_user, no_defaults_password,
                      workspace=nd_workspace, project=none_project, server_ping=False)
    actualErrVerbiage = excinfo.value.args[0]
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text

def test_no_defaults_good_workspace_bad_project():
    no_defaults_user, no_defaults_password = ACCOUNT_WITH_NO_DEFAULTS_CREDENTIALS
    nd_workspace, bad_project = ('NMTest', 'Cuzzin Blutto')
    problem = "The current Workspace '%s' does not contain an accessible Project with the name of '%s'"
    problem_text = problem % (nd_workspace, bad_project)

    with py.test.raises(Exception) as excinfo:
        rally = Rally(RALLY, no_defaults_user, no_defaults_password,
                      workspace=nd_workspace, project=bad_project, server_ping=False)
    actualErrVerbiage = excinfo.value.args[0]
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text

def test_ignore_defaults_use_good_workspace_none_project():
    good_workspace = "Integrations Test"
    good_project   = "Integrations Project"
    none_project   = None

    rally = Rally(server=RALLY, username=RALLY_USER, password=RALLY_PSWD, apikey=API_KEY,
                  workspace=good_workspace, project=good_project, server_ping=False)
    workspace = rally.getWorkspace()
    project   = rally.getProject()
    assert(workspace.Name) == good_workspace
    assert(project.Name)   == good_project

    problem = "The current Workspace '%s' does not contain a Project with the name of '%s'"
    problem_text = problem % (good_workspace, none_project)
    with py.test.raises(Exception) as excinfo:
       rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, apikey=API_KEY,
                     workspace=good_workspace,
                     project=none_project, server_ping=False)
    actualErrVerbiage = excinfo.value.args[0]
    #print("actualErrVerbiage")
    #print(actualErrVerbiage)
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text

def test_ignore_defaults_use_good_workspace_bad_project():
    good_workspace = "Integrations Test"
    good_project   = "Integrations Project"
    bad_project    = "while (e_coyote)"

    problem = "The current Workspace '%s' does not contain an accessible Project with the name of '%s'"
    problem_text = problem % (good_workspace, bad_project)
    with py.test.raises(Exception) as excinfo:
       rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, apikey=API_KEY,
                     workspace=good_workspace,
                     project=bad_project, server_ping=False)
    actualErrVerbiage = excinfo.value.args[0]
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text

#test_get_workspace()
#test_get_project()

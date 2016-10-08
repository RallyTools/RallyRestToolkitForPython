#!/usr/bin/env python

import sys, os
import types
import py

from pyral import Rally, RallyUrlBuilder

##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD
from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT, NON_DEFAULT_PROJECT
from rally_targets import ALTERNATE_WORKSPACE, ALTERNATE_PROJECT

##################################################################################################

def makeResourceUrl(rally, entity, **kwargs):
    resource = RallyUrlBuilder(entity)
    resource.qualify(True, None, None, 10, 1)
    context, augments = rally.contextHelper.identifyContext(**kwargs)
##
##    print(" context: %s" % repr(context))
##    print("augments: %s" % repr(augments))
##
    workspace_ref = rally.contextHelper.currentWorkspaceRef()
    project_ref   = rally.contextHelper.currentProjectRef()
##
##    print("workspace_ref: %s" % workspace_ref)
##    print("  project_ref: %s" %   project_ref)
##
    if workspace_ref:
        if 'workspace' not in kwargs or ('workspace' in kwargs and kwargs['workspace'] is not None):
            resource.augmentWorkspace(augments, workspace_ref)
            if project_ref:
                if 'project' not in kwargs or ('project' in kwargs and kwargs['project'] is not None):
                    resource.augmentProject(augments, project_ref)
                    resource.augmentScoping(augments)

    url = "%s/%s" % (rally.service_url, resource.build())
    return url

##################################################################################################

# 1
def test_default_context():  
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and confirm that the default workspace
        and project are set to DEFAULT_WORKSPACE and DEFAULT_PROJECT and
        that the current workspace and project are indeed the DEFAULT_WORKSPACE
        and DEFAULT_PROJECT values.
        Furthermore the construction of a GET related URL will contain
        the correct workspace and project specifications in the QUERY_STRING.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, server_ping=False)
    context1 = rally.contextHelper.currentContext()
    workspace = rally.getWorkspace()
    project   = rally.getProject()
    context2 = rally.contextHelper.currentContext()
    assert context1 == context2
    assert context1.workspace == DEFAULT_WORKSPACE
    assert workspace.Name     == DEFAULT_WORKSPACE
    assert context1.project   == DEFAULT_PROJECT
    assert project.Name       == DEFAULT_PROJECT
    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

# 2
def test_default_isolated_workspace():  
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and confirm that the default workspace
        and project are set to DEFAULT_WORKSPACE and DEFAULT_PROJECT and
        that the current workspace and project are indeed the DEFAULT_WORKSPACE
        and DEFAULT_PROJECT values.
        Furthermore the construction of a GET related URL will contain
        the correct workspace and project specifications in the QUERY_STRING.
        And any attempt to change the workspace via rally.setWorkspace(some_name)
        will result in a Exception being raised
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, server_ping=False, isolated_workspace=True)
    context1 = rally.contextHelper.currentContext()
    workspace = rally.getWorkspace()
    project   = rally.getProject()
    context2 = rally.contextHelper.currentContext()
    assert context1 == context2
    assert context1.workspace == DEFAULT_WORKSPACE
    assert workspace.Name     == DEFAULT_WORKSPACE
    assert context1.project   == DEFAULT_PROJECT
    assert project.Name       == DEFAULT_PROJECT
    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url

    problem_text = 'No reset of of the Workspace is permitted when the isolated_workspace option is specified'
    with py.test.raises(Exception) as excinfo:
        rally.setWorkspace(ALTERNATE_WORKSPACE)
    actualErrVerbiage = excinfo.value.args[0] 
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text

# 3
def test_explictly_set_workspace_as_default_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=DEFAULT_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT
    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

    rally.setWorkspace(ALTERNATE_WORKSPACE)
    assert rally.getWorkspace().Name == ALTERNATE_WORKSPACE

# 4
def test_explictly_set_workspace_as_isolated_workspace():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=DEFAULT_WORKSPACE, isolated_workspace=True)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT
    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)

    problem_text = 'No reset of of the Workspace is permitted when the isolated_workspace option is specified'
    with py.test.raises(Exception) as excinfo:
        rally.setWorkspace(ALTERNATE_WORKSPACE)
    actualErrVerbiage = excinfo.value.args[0] 
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text

# 5
def test_initial_workspace_not_default():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, 
                  workspace=ALTERNATE_WORKSPACE, 
                  warn=False)
    # Because no project=name arg was supplied, the project will be the User's default project
    # which will not necessarily be valid for the workspace argument that was supplied
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    rally.setProject(ALTERNATE_PROJECT)
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

    rally.setWorkspace(DEFAULT_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE

    rally.setProject(DEFAULT_PROJECT)
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

# 6
def test_initial_non_default_workspace_as_isolated():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, 
                  workspace=ALTERNATE_WORKSPACE, 
                  warn=False, isolated_workspace=True)
    # Because no project=name arg was supplied, the project will be the User's default project
    # which will not necessarily be valid for the workspace argument that was supplied
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    rally.setProject(ALTERNATE_PROJECT)
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

    problem_text = 'No reset of of the Workspace is permitted when the isolated_workspace option is specified'
    with py.test.raises(Exception) as excinfo:
        rally.setWorkspace(DEFAULT_WORKSPACE)
    actualErrVerbiage = excinfo.value.args[0] 
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    assert actualErrVerbiage == problem_text

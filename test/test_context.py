#!/usr/bin/env python

import sys, os
import types

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
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
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

# 3
def test_initial_workspace_not_default():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, 
                  workspace=ALTERNATE_WORKSPACE, 
                  warn=False)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT
    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

# 4
def test_explicitly_set_workspace_and_project_as_default_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, 
                  workspace=DEFAULT_WORKSPACE,
                  project=DEFAULT_PROJECT)
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

# 5
def test_set_default_workspace_non_default_project_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, 
                  workspace=DEFAULT_WORKSPACE,
                  project=NON_DEFAULT_PROJECT)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == NON_DEFAULT_PROJECT
    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

# 6
def test_set_non_default_workspace_and_project_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, 
                  workspace=ALTERNATE_WORKSPACE,
                  project=ALTERNATE_PROJECT)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT
    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

# 7
def test_default_wksprj_with_set_workspace_with_default_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    rally.setWorkspace(DEFAULT_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE

    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

#8
def test_default_wksprj_with_set_non_default_workspace_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project   = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    url = makeResourceUrl(rally, 'Defect')
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    expected_project_clause   = 'project=project/%s'     % str(project.oid)
    assert expected_workspace_clause in url
    assert expected_project_clause   in url

    rally.setWorkspace(ALTERNATE_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project   = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect')
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    expected_project_clause   = 'project=project/%s'     % str(project.oid)
    assert expected_workspace_clause in url
    assert expected_project_clause   in url

#9
def test_default_workspace_with_set_non_default_workspace_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=DEFAULT_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    rally.setWorkspace(ALTERNATE_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project   = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    expected_project_clause   = 'project=project/%s'     % str(project.oid)
    assert expected_workspace_clause in url
    assert expected_project_clause   in url

#10
def test_default_workspace_with_set_non_default_workspace_and_project_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=DEFAULT_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    rally.setWorkspace(ALTERNATE_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE

    rally.setProject(ALTERNATE_PROJECT)
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect')
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    expected_project_clause = 'project=project/%s' % str(project.oid)
    assert expected_project_clause   in url

#11
def test_default_workspace_project_specify_project_equal_None_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    url = makeResourceUrl(rally, 'Defect', project=None)
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    assert '&project=' not in url

#12
def test_non_default_workspace_project_specify_project_equal_None_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                  workspace=ALTERNATE_WORKSPACE,
                  project=ALTERNATE_PROJECT)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect', project=None)
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    assert '&project=' not in url

#13
def test_default_wksprj_with_set_non_default_workspace_specify_project_equal_None_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()

    rally.setWorkspace(ALTERNATE_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE

    url = makeResourceUrl(rally, 'Defect', project=None)
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    assert '&project=' not in url

#14
def test_default_wksprj_with_set_non_default_workspace_and_project_specify_project_equal_None_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()

    rally.setWorkspace(ALTERNATE_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE

    rally.setProject(ALTERNATE_PROJECT)
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect', project=None)
    #print(url)
    expected_workspace_clause = 'workspace=workspace/%s' % str(workspace.oid)
    assert expected_workspace_clause in url
    assert '&project=' not in url

#15
def test_default_wksprj_specify_workspace_and_project_equal_None_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    url = makeResourceUrl(rally, 'Defect', workspace=None, project=None)
    #print(url)
    assert '&workspace=' not in url
    assert '&project='   not in url

#16
def test_non_default_wksprj_specify_workspace_and_project_equal_None_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                  workspace=ALTERNATE_WORKSPACE,
                  project=ALTERNATE_PROJECT)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect', workspace=None, project=None)
    #print(url)
    assert '&workspace=' not in url
    assert '&project='   not in url

#17
def test_default_wksprj_set_non_default_wksprj_specify_workspace_and_project_equal_None_context():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    assert workspace.Name == DEFAULT_WORKSPACE
    project = rally.getProject()
    assert project.Name == DEFAULT_PROJECT

    rally.setWorkspace(ALTERNATE_WORKSPACE)
    workspace = rally.getWorkspace()
    assert workspace.Name == ALTERNATE_WORKSPACE

    rally.setProject(ALTERNATE_PROJECT)
    project = rally.getProject()
    assert project.Name == ALTERNATE_PROJECT

    url = makeResourceUrl(rally, 'Defect', workspace=None, project=None)
    #print(url)
    assert '&workspace=' not in url
    assert '&project='   not in url


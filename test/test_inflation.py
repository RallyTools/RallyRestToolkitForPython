import sys, os
import time
import types
import py

from pyral import Rally, RallyRESTAPIError

##################################################################################################

TRIAL = "preview.rallydev.com"

TRIAL_USER = "usernumbernine@acme.com"
TRIAL_PSWD = "************"

##################################################################################################

def test_default_connection():
    """
        Using a known valid Rally server and access credentials, 
        connect without specifying workspace or project.
        Return status should be OK, 
        Rally._wpCacheStatus should be 'minimal'
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
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
    project = 'Shopping Team'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
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
    project = 'Online Store'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
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
    expectedErrMsg = u"Unable to use your project specification of '%s', that value is not associated with current workspace setting of: '%s'" % (project, 'User Story Pattern')
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                      project=project)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'Exception'
    assert actualErrVerbiage == expectedErrMsg

def test_named_default_workspace_use_default_project():
    """
        Using valid Rally access credentials, connect
        specifying the workspace name (which is the default value), 
        without specifying the name of project.
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    workspace = 'User Story Pattern'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                  workspace=workspace)
    response = rally.get('Project')
    assert response != None
    assert response.status_code == 200
    project = response.next()
    assert project.Name == 'Shopping Team'
    assert rally._wpCacheStatus() == 'minimal'


def test_named_default_workspace_named_default_project():
    """
        Using valid Rally access credentials, connect
        specifying the workspace name (which is the default value), 
        specifying the name of project (which is the default value).
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    workspace = 'User Story Pattern'
    project   = 'Shopping Team'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                  workspace=workspace, project=project)
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
    workspace = 'User Story Pattern'
    project   = 'Online Store'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                  workspace=workspace, project=project)
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
    workspace = 'User Story Pattern'
    project = 'Sailor Sami'
    expectedErrMsg = u"Unable to use your project specification of '%s', that value is not associated with current workspace setting of: '%s'" % (project, workspace)
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                      workspace=workspace, project=project)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'Exception'
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
    #default_workspace = 'User Story Pattern'
    workspace = 'Integrations'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=workspace)
    ai_proj = rally.getProject()
    assert str(ai_proj.Name) == 'Shopping Team'   # is valid on both default and 'Integrations'
    assert rally._wpCacheStatus() == 'narrow'

    workspace = 'Healthcare Story Pattern 1'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=workspace)
    ai_proj = rally.getProject()
    assert str(ai_proj.Name) == 'Big Healthcare'   # is valid only in 'Healthcare Story Pattern 1'
    assert rally._wpCacheStatus() == 'narrow'

def test_named_non_default_workspace_named_valid_project():
    """
        Using valid Rally access credentials, connect specifying
        a valid non-default workspace and a valid project.
        Return status should be OK, the Rally instance's RallyContextHelper
        _inflated value should be 'minimal'
    """
    workspace = 'Integrations'
    project   = 'Consumer Site'
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                  workspace=workspace, project=project)
    response = rally.get('Project')
    assert response != None
    assert response.status_code == 200
    assert rally._wpCacheStatus() == 'narrow'

def test_named_non_default_workspace_named_invalid_project():
    """
        Using valid Rally access credentials, connect specifying
        a valid non-default workspace and an invalid project.
        An exception should be raised.
    """
    workspace = 'Integrations'
    project   = 'Barney Rubble'
    expectedErrMsg = u"Unable to use your project specification of '%s', that value is not associated with current workspace setting of: '%s'" % (project, workspace)
    with py.test.raises(Exception) as excinfo:
        rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD,
                  workspace=workspace, project=project, timeout=10)
        response = rally.get('Project', fetch=False, limit=5)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'Exception'
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

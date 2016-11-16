#!/usr/bin/env python

import sys, os
import types

import py

from pyral import Rally, RallyUrlBuilder

##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD
from rally_targets import   DEFAULT_WORKSPACE,   DEFAULT_PROJECT
from rally_targets import ALTERNATE_WORKSPACE, ALTERNATE_PROJECT
from rally_targets import BOONDOCKS_WORKSPACE, BOONDOCKS_PROJECT
from rally_targets import API_KEY
from rally_targets import ACCOUNT_WITH_NO_DEFAULTS_CREDENTIALS

##################################################################################################

"""
4 ways we'll have to accommodate multi-element path Project, ie.,  BaseProject // NextLevelProject // TargetProject
  (aka m-e-p Project)

    o - Rally instance constructor with a m-e-p Project argument
    o - specification of a m-e-p Project in a Rally basic HTTP operation call
           get,put,post,delete as the project=m-e-p Project
    o - setProject(m-e-p Project)
    o - as a data payload item for Project  as name instead of _ref

        Example of Jenkins Build Connector  spec for
            Jenkins // Corral // Salamandra
"""

DUPLICATED_PROJECTS = ['Jenkins // Salamandra', 'Jenkins // Corral // Salamandra']
DUPLICATED_PROJECT  = 'Salamandra'
SHORT_DUPE = DUPLICATED_PROJECTS[0]
DEEP_DUPE  = DUPLICATED_PROJECTS[1]

def test_get_duplicated_project():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query to retrieve Project items that match a specific project name that occurs
        in more than one location in the tree of Projects under the target Workspace.
    """
    yeti, cred = "yeti@rallydev.com", "Vistabahn"
    rally = Rally(server=TRIAL, user=yeti, password=cred, workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)
    response = rally.get('Project', fetch=False, query='Name = "%s"' % DUPLICATED_PROJECT, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    #assert response.warnings == []
    assert response.resultCount > 1
    assert response.resultCount == 2
    for proj in response:
        assert str(proj.Name) == DUPLICATED_PROJECT
        print(proj.details())

def test_get_distant_duplicated_project():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query to retrieve a Project item that matches a full project path within the target workspace.
        Expect the result to return one and only one Project that is the correct Project.
    """
    yeti, cred = "yeti@rallydev.com", "Vistabahn"
    rally = Rally(server=TRIAL, user=yeti, password=cred, workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)
    response = rally.get('Project', fetch=False, query='Name = "%s"' % DEEP_DUPE, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    #assert response.warnings == []
    assert response.resultCount == 1
    proj = response.next()
    assert str(proj.Name) == DUPLICATED_PROJECT

    sp = rally.setProject(DEEP_DUPE)
    assert sp.Name == DEEP_DUPE

#!/usr/bin/env python

import sys, os
import types

import py

from pyral import Rally, RallyUrlBuilder

##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD
from rally_targets import YETI_USER, YETI_PSWD
from rally_targets import BOONDOCKS_WORKSPACE, BOONDOCKS_PROJECT
from rally_targets import API_KEY

##################################################################################################

"""
Several ways we'll have to accommodate multi-element path Project (aka m-e-p Project) of the form:
    BaseProject // NextLevelProject // TargetProject

    o - Rally instance constructor with a m-e-p Project argument
        OK

    o - setProject(m-e-p Project)
        OK

    o - getProject()   when the current project is a m-e-p Project
        OK

    o - getProject(m-e-p Project)
        OK

    o - as default Project after a setProject(m-e-p Project)
        OK

    o - specification of a m-e-p Project in a Rally basic HTTP operation call
           get,put,post,delete as the project=m-e-p Project
        OK

    o - as a data payload item for Project as name instead of _ref
        NOT YET WRITTEN

        Example of Jenkins Build Connector spec for
            Jenkins // Corral // Salamandra
"""

DUPLICATED_PROJECTS = ['Jenkins // Salamandra', 'Jenkins // Corral // Salamandra']
DUPLICATED_PROJECT  = 'Salamandra'
SHORT_DUPE = DUPLICATED_PROJECTS[0]
DEEP_DUPE  = DUPLICATED_PROJECTS[1]
BASE_PROJECT = SHORT_DUPE.split(' // ')[0]

def test_mep_project_as_payload_project_value():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance associated with default workspace and project.
        The credentials should permit the user to create items in the DEEP_DUPE
        Project.
        Issue a request through the instance to create an item whose data payload
        includes a field for Project whose value will be a m-e-p Project string.
        The resulting created item must have a Project value that is a ref to the
        m-e-p Project.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD)


def test_obtain_instance_using_mep_project():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance associated with specifying a valid but 
        multi-element-path Project within a valid Workspace.
        A subsequent call on the instance to obtain the current Project should
        return a pyral entity for Project that has a ref for the correct m-e-p Project.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD, 
                  workspace=BOONDOCKS_WORKSPACE, project=DEEP_DUPE)
    cur_project = rally.getProject()
    assert cur_project.Name == DEEP_DUPE


def test_get_duplicated_project():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query to retrieve Project items that match a specific project name that occurs
        in more than one location in the tree of Projects under the target Workspace.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD, 
                  workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)
    response = rally.get('Project', fetch=False, query='Name = "%s"' % DUPLICATED_PROJECT, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.resultCount > 1
    assert response.resultCount == 2
    for proj in response:
        assert str(proj.Name) == DUPLICATED_PROJECT


def test_get_distant_duplicated_project():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and use it to obtain a Project instance for 
        a Project whose name contains multiple path elements with the elements 
        separated by the ' // ' token string.
        Expect the result to return one and only one Project that is the correct Project.
        The result should have the correct Parent Project.
        When the Rally instance is called to setProject with the value of that 
        multi element path for the Project it should do so and should return the
        correct value when asked for the current Project.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD, 
                  workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)

    dupey_project = rally.getProject(DEEP_DUPE)
    assert dupey_project is not None
    assert dupey_project.__class__.__name__ == 'Project'
    assert dupey_project.Name == DEEP_DUPE

    criteria = 'Name = "%s"' % 'Corral'
    expected_parent = rally.get('Project', fetch="Name,ObjectID,Parent,Children", 
                                query=criteria, projectScopeDown=False, instance=True)
    assert expected_parent is not None
    assert expected_parent.__class__.__name__ == 'Project'
    assert expected_parent.Name == 'Corral'
    assert dupey_project.Parent.ref == expected_parent.ref

    result = rally.setProject(DEEP_DUPE)
    assert result is None
    cur_project = rally.getProject()
    assert cur_project.Name == DEEP_DUPE


def test_use_mep_project_as_default_scoped_project():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance associated with specifying a valid but 
        multi-element-path Project within a valid Workspace.
        A subsequent call on the instance to obtain the current Project should
        return a pyral entity for Project that has a ref for the correct m-e-p Project.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD, 
                  workspace=BOONDOCKS_WORKSPACE, project=DEEP_DUPE)
    target_story = 'US3'
    result = rally.get('Story', fetch="FormattedID,Name,Description,State,Project", projectScopeUp=False)
    assert result is not None
    assert result.resultCount > 0
    stories = [story for story in result]
    assert len(stories) > 0
    hits = [story for story in stories if story.FormattedID == target_story]
    assert len(hits) == 1
    hit = hits[0]
    assert hit.FormattedID == target_story
    assert hit.Project.Name == DUPLICATED_PROJECT


def test_use_mep_project_as_project_keyword_scoped():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance associated with specifying a valid unique Project name
        that exists within the Workspace.
        A subsequent request the instance specifying a valid m-e-p Project in the Workspace
        should return an item scoped to that m-e-p Project.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD, 
                  workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)
    target_story = 'US3'
    result = rally.get('Story', fetch="FormattedID,Name,Description,State,Project", 
                                query='FormattedID = %s' % target_story,
                                project=DEEP_DUPE, projectScopeUp=False)
    assert result is not None
    assert result.resultCount > 0
    stories = [story for story in result]
    assert len(stories) > 0
    hits = [story for story in stories if story.FormattedID == target_story]
    assert len(hits) == 1
    hit = hits[0]
    assert hit.FormattedID == target_story


def test_set_mep_project_used_as_default_in_request_operation():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance associated with a unique Project name within a 
        valid Workspace.
        Subsequently, set the instance's Project to a Project whose name is a duplicate.
        The duplicate Project is specified as a path chain of:
           baseProject // nextLevelProject // leafProject
        At least one of the other non-target duplicates should exist in a shorter path.
        Issue a request using the target duplicate Project m-e-p.
        The result should be an Artifact whose projet matches the target duplicate Project
        leaf name and ref exactly.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD, 
                  workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)
    rally.setProject(DEEP_DUPE)
    target_story = 'US3'
    result = rally.get('Story', fetch="FormattedID,Name,Description,State,Project", 
                                query='FormattedID = %s' % target_story,
                                projectScopeUp=False)
    assert result is not None
    assert result.resultCount > 0
    stories = [story for story in result]
    assert len(stories) > 0
    hits = [story for story in stories if story.FormattedID == target_story]
    assert len(hits) == 1
    hit = hits[0]
    assert hit.FormattedID == target_story

def test_mep_project_in_request_payload():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance associated with a unique Project name within a
        valid Workspace.
        Assemble a payload dict to be used in creating a BuildDefinition item
        that uses a m-e-p Project value for the Project attribute.
        Issue the request to create the BuildDefinition item.
        The result should be the creation of the BuildDefinition item
        for which the Project attribute has a ref to the targeted m-e-p Project.
    """
    rally = Rally(server=TRIAL, user=YETI_USER, password=YETI_PSWD,
                  workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)
    workspace = rally.getWorkspace()
    dd_project = rally.getProject(DEEP_DUPE)
    info = {
        'Name'         : 'Throckmorton Nunnigan',
        'Description'  : 'A completely artificial sweetener',
        'Workspace'    : workspace._ref,
        'Project'      : dd_project._ref
    }

    build_defn = rally.create('BuildDefinition', info)
    assert build_defn.Project._ref == dd_project._ref

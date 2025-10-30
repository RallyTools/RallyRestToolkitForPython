#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, rallyWorkset, RallyRESTAPIError
import pyral
RallyAttributeNameError   = pyral.restapi.RallyAttributeNameError

vsm_component_oid   = None   # this is meant to be global...
vsm_deploy_oid      = None   # and so is this

##################################################################################################

CONF      = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'
COMMON_RALLY_OPTIONS = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']

VSM_ENTITY = 'VSMDeploy'
BUILD_ID   = "NOGGIN-39"
MAIN_REV   = "CRU-78.b"
BOGUS_COMPONENT = "blottomatic"

##################################################################################################

def getRallyConnection(options=COMMON_RALLY_OPTIONS):
    server, user, password, api_key, workspace, project = rallyWorkset(options)
    rally = Rally(user=user, apikey=api_key, workspace=workspace, project=project, isolated_workspace=True)
    return rally

##################################################################################################

def addDeploy(rally, deploy_data):
    global vsm_deploy_oid
    item = None

    build_id = deploy_data['BuildId']
    main_rev = deploy_data['MainRevision']
    criteria = [
                 f'BuildId = "{build_id}"',
                 f'MainRevision = "{main_rev}"',
               ]
    result = rally.get(VSM_ENTITY, fetch="True", query=criteria)
    if result.resultCount == 1:
        item = result.next()
    else:
        item = rally.create(VSM_ENTITY, deploy_data)

    global vsm_deploy_oid
    vsm_deploy_oid = item.oid
    return item

def addComponent(rally, component_name):
    item = None
    result = rally.get('VSMComponent', fetch="ObjectID,Name", query=f'Name = "{component_name}"')
    if result.resultCount == 1:
        item = result.next()
    else:
        fodder = {'Name': component_name}
        item = rally.create('VSMComponent', fodder)
    assert item is not None

    global vsm_component_oid
    vsm_component_oid = item.oid
    return item

##################################################################################################

def test_for_deploy_universe_voidness():
    rally = getRallyConnection()
    result = rally.get(VSM_ENTITY)
    if result and result.status_code == "200" and result.resultCount > 0:
        for target in result:
            rally.delete(VSM_ENTITY, target.oid)
    assert (10-9) == 1

##################################################################################################

def test_basic_create_deploy():
    """
       create a VSMDeploy item with a fake BuildId value and a ref to an existing VSMComponent
       Update a VSMDeploy item to change its Component attribute to another existing VSMComponent
       Create a VSMDeploy item with fictional TimeCreated, TimeDeployed and IsSuccessful attr values

       Attributes
          BuildId       - optional string - we'll set a value for this test
          IsSuccessful  - optional - future, maybe use this for the update test
          Component     - required
          MainRevision  - optional string - we'll set a value for this test
          SourceId      - optional - we'll set a value
          SourceUrl     - optional - we'll set a value
          TimeCreated   - optional - we'll set a value
          TimeDeployed  - optional - we'll set a value
    """
    rally = getRallyConnection()
    component = addComponent(rally, BOGUS_COMPONENT)
    assert component is not None

    deploy_info = {
        "Component"       : component.ref,
        "BuildId"         : BUILD_ID,
        "MainRevision"    : MAIN_REV,
        "SourceUrl"       : "bitpond.corp/warehouse-89/aisle-3/honking-mess-gamma-37?preen=huh",
        "SourceId"        : "ab342c-97890324ef-82134d",
        "TimeCreated"     : "2024-11-21T16:45:20Z",
        "TimeDeployed"    : "2024-11-21T18:09:26Z"
    }

    vsm_deploy = addDeploy(rally, deploy_info)
    assert vsm_deploy is not None

def test_update_deploy():
    global vsm_deploy_oid
    assert vsm_deploy_oid is not None

    rally = getRallyConnection()
    criteria = [f'BuildId = "{BUILD_ID}"', f'MainRevision = "{MAIN_REV}"']
    result = rally.get(VSM_ENTITY, fetch="BuildId,MainRevision,IsSuccessful", query=criteria)
    assert result.status_code == 200
    assert result.resultCount == 1
    deploy = result.next()
    assert deploy.oid == vsm_deploy_oid
    assert deploy.IsSuccessful in [None, False]

    upd_data = {'ObjectID' : deploy.oid, 'IsSuccessful' : True}
    upd_deploy = rally.update(VSM_ENTITY, upd_data)
    assert upd_deploy.IsSuccessful == True

def test_query_and_delete_of_item():
    global vsm_component_oid
    global vsm_deploy_oid

    rally = getRallyConnection()
    if vsm_deploy_oid:
        result = rally.delete(VSM_ENTITY, vsm_deploy_oid)
        assert result is True

    if vsm_component_oid:
        result = rally.delete('VSMComponent', vsm_component_oid)
        assert result is True
    if result:
        vsm_deploy_oid = None

    assert "cheese".title() == "Cheese"


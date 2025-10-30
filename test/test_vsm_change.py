#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, rallyWorkset, RallyRESTAPIError
import pyral
RallyAttributeNameError   = pyral.restapi.RallyAttributeNameError

vsm_chg_oid   = None

##################################################################################################

CONF      = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'
COMMON_RALLY_OPTIONS = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']

VSM_ENTITY = 'VSMChange'
COMMIT_MESSAGE = "Blown away on a raft of deceit"

##################################################################################################

def getRallyConnection(options=COMMON_RALLY_OPTIONS):
    server, user, password, api_key, workspace, project = rallyWorkset(options)
    rally = Rally(user=user, apikey=api_key, workspace=workspace, project=project, isolated_workspace=True)
    return rally

##################################################################################################

def addChange(rally, chg_data):
    global vsm_chg_oid
    item = None
    commit_message = chg_data['CommitMessage']
    result = rally.get(VSM_ENTITY, fetch="True", query=f'CommitMessage = "{commit_message}"')
    if result.resultCount == 1:
        item = result.next()
    else:
        item = rally.create(VSM_ENTITY, chg_data)
    vsm_chg_oid = item.oid
    return item

##################################################################################################

def test_for_change_universe_voidness():
    rally = getRallyConnection()
    result = rally.get(VSM_ENTITY)
    if result and result.status_code == "200" and result.resultCount > 0:
        for target in result:
            rally.delete(VSM_ENTITY, target.oid)
    assert (10-9) == 1

##################################################################################################

def test_basic_create_change():
    """
         Attributes
            Revision
            CommitTime
            CommitMessage

            SourceId
            SourceUrl
            Deploy       - optional, don't bother setting here...

        happy  create, update and delete
    """
    rally = getRallyConnection()
    chg_info = {
        "Revision"        : "17",
        "CommitTime"      : "2024-11-07T06:14:47Z",
        "CommitMessage"   : "Blown away on a raft of deceit",
        "SourceUrl"       : "git@github.com/Frebblestop/meatwaganni",
        "SourceId"        : "Rbolik Ninglid C509-K6"
       }

    vsm_chg = addChange(rally, chg_info)
    assert vsm_chg is not None


def test_query_and_delete_of_item():
    global vsm_chg_oid

    rally = getRallyConnection()
    if vsm_chg_oid:
        result = rally.delete(VSM_ENTITY, vsm_chg_oid)
        assert result is True
    assert "SMALL".lower() == "small"


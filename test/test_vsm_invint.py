#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, rallyWorkset, RallyRESTAPIError
import pyral
RallyAttributeNameError   = pyral.restapi.RallyAttributeNameError
InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError

inv_int_map_oid = None

##################################################################################################

#from internal_rally_targets import APIKEY, WORKSPACE, PROJECT
#from rally_targets import APIKEY, DEFAULT_WORKSPACE, DEFAULT_PROJECT
#from rally_targets import PROD_USER, PROD_PSWD

CONF      = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'
COMMON_RALLY_OPTIONS = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']

VSM_ENTITY = 'VSMInvestmentCategorytoInvestmentIntentMap'

##################################################################################################

def getRallyConnection(options=COMMON_RALLY_OPTIONS):
    server, user, password, api_key, workspace, project = rallyWorkset(options)
    rally = Rally(user=user, apikey=api_key, workspace=workspace, project=project, isolated_workspace=True)
    return rally

##################################################################################################

def test_basic_create_invint():
    """
        Create a new VSMInvestmentCategorytoInvestmentIntentMap item
        with InvestmentCategory and InvestmentIntentName attrs
    """
    rally = getRallyConnection()
    wksp = rally.getWorkspace()
    proj = rally.getProject()

    valid_categories = [ '', 'Cost Savings', 'Short Term Growth', 'Strategic Growth', 'Maintenance' ]
    valid_intents    = [ 'Innovate', 'Scale', 'Retain' ]
    category = 'Maintenance'
    intent   = 'Retain'
    ii_info = {
                #"Project"      : proj.ref,
                "InvestmentCategory"   : category,
                "InvestmentIntentName" : intent,
              }

    invint_item = rally.create(VSM_ENTITY, ii_info)
    assert invint_item is not None
    assert invint_item.__class__.__name__ == 'VSMInvestmentCategorytoInvestmentIntentMap'
    global inv_int_map_oid
    inv_int_map_oid = invint_item.oid

def test_query_and_delete_of_item():
    global inv_int_map_oid
    if not inv_int_map_oid:
        assert inv_int_map_oid is None
    else:
        rally = getRallyConnection()
        iimap_oid = inv_int_map_oid
        result = rally.delete(VSM_ENTITY, iimap_oid)
        assert result is True

def test_detect_bad_attr_values():
    rally = getRallyConnection()
    category = 'Gougetakos'
    intent   = 'Profitus'
    ii_info = \
        {
            "InvestmentCategory"   : category,
            "InvestmentIntentName" : intent,
        }

    expectedErrMsg = ' is invalid.  Valid values are: '
    with pytest.raises(RallyRESTAPIError) as excinfo:
        invint_item = rally.create(VSM_ENTITY, ii_info)
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    actualErrVerbiage = excinfo.value.args[0]
    assert expectedErrMsg in actualErrVerbiage

#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, rallyWorkset, RallyRESTAPIError
import pyral
RallyAttributeNameError   = pyral.restapi.RallyAttributeNameError
InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError

vsm_inc_oid = None

##################################################################################################

#from internal_rally_targets import APIKEY, WORKSPACE, PROJECT
#from rally_targets import APIKEY, DEFAULT_WORKSPACE, DEFAULT_PROJECT
#from rally_targets import PROD_USER, PROD_PSWD

CONF      = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'
COMMON_RALLY_OPTIONS = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']

VSM_ENTITY = 'VSMIncident'

##################################################################################################

def getRallyConnection(options=COMMON_RALLY_OPTIONS):
    server, user, password, api_key, workspace, project = rallyWorkset(options)
    rally = Rally(user=user, apikey=api_key, workspace=workspace, project=project, isolated_workspace=True)
    return rally

##################################################################################################

def addProduct(rally, product_name):
    entity_name = 'VSMProduct'
    item = None

    result = rally.get(entity_name, fetch="Name,ObjectID", query=f'Name = "{product_name}"')
    if result.resultCount ==1:
        item = result.next()
    else:
        fodder = {'Name' : product_name}   # 'SubclassType' : 'P'
        item = rally.create(entity_name, fodder)
    return item

##################################################################################################

def test_basic_create_incident():
    """
         Prereq for this test is that there has to be a VSMProduct to link to

    happy
       create a VSMIncident item with valid value for Product
          Product - actual VSMProduct ref
          Component - not required
          Name - required
          Description - optional
          Channel - Kabuki
          OpenedDate - today
          ClosedDate
          Priority - not required
          Status - string like Open or Closed or Research
       update an existing VSMIncident to set Description and Component and Status

    """
    rally = getRallyConnection()
    vsm_product = addProduct(rally, 'Vukonardim')

    inc_info = {
        "Product"     : vsm_product.ref,
        "Name"        : "Ruffinas exhibit bulging relief valve near drizzle pod",
        "Description" : "on site supervisor notes lagging indicators for drain cycle",
        "OpenedDate"  : "2024-11-01T08:00:05.000Z",
       }

    inc_item = rally.create(VSM_ENTITY, inc_info)

    assert inc_item is not None
    assert inc_item.__class__.__name__ == VSM_ENTITY
    global vsm_inc_oid
    vsm_inc_oid = inc_item.oid

    inc_data = { 'ObjectID' : inc_item.oid,
                 'Priority' : 'Normal',
                 'Status'   : 'Open'
               }
    upd_item = rally.update(VSM_ENTITY, inc_data)
    assert upd_item.ObjectID == inc_item.ObjectID
    assert upd_item.Status   == 'Open'
    assert upd_item.Priority == 'Normal'


def test_query_and_delete_of_item():
    global vsm_inc_oid
    if not vsm_inc_oid:
        assert vsm_inc_oid is None
    else:
        rally = getRallyConnection()
        pam_oid = vsm_inc_oid
        result = rally.delete(VSM_ENTITY, pam_oid)
        assert result is True

def test_detect_bad_attr_values():
    rally = getRallyConnection()
    doofus_product = 'InfinityDrain'
    inc_info = \
        {
            "Product"  :  doofus_product,
            "Name"     : "",
            "Description" : "not fit for release to dead rats"
        }

    expectedErrMsg = f'Cannot parse object reference from "{doofus_product}"'
    with pytest.raises(RallyRESTAPIError) as excinfo:
        pam_item = rally.create(VSM_ENTITY, inc_info)
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    actualErrVerbiage = excinfo.value.args[0]
    assert expectedErrMsg in actualErrVerbiage

#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, rallyWorkset, RallyRESTAPIError
import pyral
RallyAttributeNameError   = pyral.restapi.RallyAttributeNameError

vsm_prod_oid   = None
vsm_pam_oid    = None
vsm_mzr_oid    = None

##################################################################################################

CONF      = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'
COMMON_RALLY_OPTIONS = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']

VSM_ENTITY = 'VSMMeasure'

##################################################################################################

def getRallyConnection(options=COMMON_RALLY_OPTIONS):
    server, user, password, api_key, workspace, project = rallyWorkset(options)
    rally = Rally(user=user, apikey=api_key, workspace=workspace, project=project, isolated_workspace=True)
    return rally

##################################################################################################

def addProduct(rally, product_name):
    global vsm_prod_oid
    item = None

    result = rally.get('VSMProduct', fetch="Name,ObjectID", query=f'Name = "{product_name}"')
    if result.resultCount ==1:
        item = result.next()
    else:
        fodder = {'Name' : product_name}   # 'SubclassType' : 'P'
        item = rally.create('VSMProduct', fodder)
    vsm_prod_oid = item.oid
    return item

def addProductAnalyticsMetric(rally, name):
    """
         Prereq for this is that there has to be a VSMProduct
    """
    global vsm_pam_oid
    rally = getRallyConnection()
    vsm_prod = addProduct(rally, 'Bamooxil')

    pam_info = {
        "Product"   : vsm_prod.ref,
        "Active"    : False,
        "Category"  : "Product Stickiness",
        "Name"      : name,
        "SourceKey" : "Cadbury-DarkCloud-alpha",
        "Description" : "Smudge pots and howling at the moon"
       }

    pam_item = rally.create('VSMProductAnalyticsMetric', pam_info)

    assert pam_item is not None
    vsm_pam_oid = pam_item.oid

    return pam_item

##################################################################################################

def test_for_measure_universe_voidness():
    rally = getRallyConnection()
    result = rally.get(VSM_ENTITY)
    if result and result.status_code == "200" and result.resultCount > 0:
        for target in result:
            rally.delete(VSM_ENTITY, target.oid)
    assert (10-9) == 1

##################################################################################################

def test_basic_create_measure():
    """
         Prereq for this test is that there has to be a VSMProductAnalyticsMetric

         Attributes
            Metric   - reference to an existing VSMProductAnalyticsMetric
            Arg1
            Operator
            Arg2
            TargetDate
        happy  create, update and delete
    """
    rally = getRallyConnection()
    vsm_pam = addProductAnalyticsMetric(rally, 'Oh Henry bar')

    mzr_info = {
        "Metric"      : vsm_pam.ref,
        "Value"       : 4907,
        "ValueTime"   : "2024-11-08T11:52:47Z",
        "SourceId"    : "Obanizuka Ronkoma A5Y89-98"
       }

    tgt_item = rally.create(VSM_ENTITY, mzr_info)

    assert tgt_item is not None
    assert tgt_item.__class__.__name__ == VSM_ENTITY
    global vsm_target_oid
    vsm_target_oid = tgt_item.oid

def test_bonk_for_issufficient_measure_attrs():
    rally = getRallyConnection()

    vsm_pam = addProductAnalyticsMetric(rally, 'Oh Henry bar')

    mzr_info = {
        "Metric"      : vsm_pam.ref,
        "ValueTime"   : "2025-01-28T01:25:39Z",
       }

    expectedErrMessage = ""
    with pytest.raises(RallyRESTAPIError) as excinfo:
        foo = rally.create(VSM_ENTITY, mzr_info)
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    actualErrVerbiage = excinfo.value.args[0]
    assert expectedErrMessage in actualErrVerbiage


def test_query_and_delete_of_item():
    global vsm_prod_oid
    global vsm_pam_oid
    global vsm_mzr_oid

    rally = getRallyConnection()
    if vsm_mzr_oid:
        result = rally.delete(VSM_ENTITY, vsm_mzr_oid)
        assert result is True
    if vsm_pam_oid:
        result = rally.delete('VSMProductAnalyticsMetric', vsm_pam_oid)
        assert result is True
    if vsm_prod_oid:
        result = rally.delete('VSMProduct', vsm_prod_oid)
        assert result is True
    assert "big".upper() == "BIG"


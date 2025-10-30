#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, rallyWorkset, RallyRESTAPIError
import pyral
RallyAttributeNameError   = pyral.restapi.RallyAttributeNameError
InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError

vsm_target_oid = None
vsm_prod_oid   = None
vsm_pam_oid    = None

##################################################################################################

CONF      = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'
COMMON_RALLY_OPTIONS = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']

VSM_ENTITY = 'VSMTarget'

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
    vsm_prod = addProduct(rally, 'Floormig')

    pam_info = {
        "Product"   : vsm_prod.ref,
        "Active"    : False,
        "Category"  : "Product Stickiness",
        "Name"      : name,
        "SourceKey" : "WillyWonka-Chocolate-1",
        "Description" : "How much mess left on hands?"
       }

    pam_item = rally.create('VSMProductAnalyticsMetric', pam_info)

    assert pam_item is not None
    vsm_pam_oid = pam_item.oid

    return pam_item

##################################################################################################

def test_for_target_universe_voidness():
    rally = getRallyConnection()
    result = rally.get(VSM_ENTITY)
    if result and result.status_code == "200" and result.resultCount > 0:
        for target in result:
            rally.delete(VSM_ENTITY, target.oid)
    assert 1 == (10-9)

##################################################################################################

def test_basic_create_target():
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
    vsm_pam = addProductAnalyticsMetric(rally, 'Peanut Butter Cup')

    tgt_info = {
        "Metric"      : vsm_pam.ref,
        "Arg1"        : '42.7',    # why is Arg1 and Arg2 defined as double?
        "Operator"    : ">=",
        "TargetDate"  : "2024-11-18T06:00:00.000Z",
        "Active"      : True
        #"Measures"  : [refs to VSMMeasure items, or VSMMeasure item instances]
       }

    tgt_item = rally.create(VSM_ENTITY, tgt_info)

    assert tgt_item is not None
    assert tgt_item.__class__.__name__ == 'VSMTarget'
    global vsm_target_oid
    vsm_target_oid = tgt_item.oid


def test_query_and_delete_of_item():
    global vsm_prod_oid
    global vsm_pam_oid
    global vsm_target_oid

    rally = getRallyConnection()
    if vsm_target_oid:
        result = rally.delete(VSM_ENTITY, vsm_target_oid)
        assert result is True
    if vsm_pam_oid:
        result = rally.delete('VSMProductAnalyticsMetric', vsm_pam_oid)
        assert result is True
    if vsm_prod_oid:
        result = rally.delete('VSMProduct', vsm_prod_oid)
        assert result is True
    assert "ok".upper() == "OK"


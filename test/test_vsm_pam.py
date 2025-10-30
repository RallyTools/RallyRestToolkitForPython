#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, rallyWorkset, RallyRESTAPIError
import pyral
RallyAttributeNameError   = pyral.restapi.RallyAttributeNameError
InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError

vsm_pam_oid = None

##################################################################################################

CONF      = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'
COMMON_RALLY_OPTIONS = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']

VSM_ENTITY = 'VSMProductAnalyticsMetric'

##################################################################################################

def getRallyConnection(options=COMMON_RALLY_OPTIONS):
    server, user, password, api_key, workspace, project = rallyWorkset(options)
    rally = Rally(user=user, apikey=api_key, workspace=workspace, project=project, isolated_workspace=True)
    return rally

##################################################################################################

def addProduct(rally, product_name):
    item = None

    result = rally.get('VSMProduct', fetch="Name,ObjectID", query=f'Name = "{product_name}"')
    if result.resultCount ==1:
        item = result.next()
    else:
        fodder = {'Name' : product_name}   # 'SubclassType' : 'P'
        item = rally.create('VSMProduct', fodder)
    return item

##################################################################################################

def test_basic_create_pam():
    """
         Prereq for this test is that there has to be a VSMProduct

        happy  create, update and delete
        Product  - VSMProduct ref
        Active - boolean
        Category - string which should be this list: (see if this is really enforced, ...it is!!)
            "Product Active Users"
            "Product Usage Rate"
            "Product Stickiness"
            "Product User Churn Rate"
            "Product Repeat Users"
            "Product User Sentiment"
            "Product Custom"
        SourceKey
        Description

        Name
        Measures  - Collection of refs to VSMMeasure items  -  not required for creation
    """
    rally = getRallyConnection()
    vsm_prod = addProduct(rally, 'PeskyMopz')

    pam_info = {
        "Product"   : vsm_prod.ref,
        "Active"    : False,
        "Category"  : "Product Stickiness",
        "Name"      : "Repeat Offenders",
        "SourceKey" : "GondwonalanderX-7543-F33BU77",
        "Description" : "Number of souls using this 3 days a week or more"
        #"Measures"  : [refs to VSMMeasure items, or VSMMeasure item instances]
       }

    pam_item = rally.create(VSM_ENTITY, pam_info)

    assert pam_item is not None
    assert pam_item.__class__.__name__ == 'VSMProductAnalyticsMetric'
    global vsm_pam_oid
    vsm_pam_oid = pam_item.oid

def test_query_and_delete_of_item():
    global vsm_pam_oid
    if not vsm_pam_oid:
        assert vsm_pam_oid is None
    else:
        rally = getRallyConnection()
        pam_oid = vsm_pam_oid
        result = rally.delete(VSM_ENTITY, pam_oid)
        assert result is True

def test_detect_bad_attr_values():
    rally = getRallyConnection()
    doofus_category = 'Half-Gainer'
    intent   = 'Profitus'
    pam_info = \
        {
            #"Product"  :  wouldhavetohavereftovalidproduct,
            "Active"   : True,
            "Category" : doofus_category,
            "Name"  : "Total Flippancy Gradient Slider"
        }

    expectedErrMsg = f'{doofus_category} is an invalid value'
    with pytest.raises(RallyRESTAPIError) as excinfo:
        pam_item = rally.create(VSM_ENTITY, pam_info)
    assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    actualErrVerbiage = excinfo.value.args[0]
    assert expectedErrMsg in actualErrVerbiage

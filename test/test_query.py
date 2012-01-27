#!/opt/local/bin/python2.6

import sys, os
import types
import py

from pyral import Rally

##################################################################################################

PREVIEW = "preview.rallydev.com"
DEMO    = "demo.rallydev.com"
PROD    = "rally1.rallydev.com"

PREVIEW_USER = "usernumbernine@acme.com"
PREVIEW_PSWD = "************"

##################################################################################################

def test_basic_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('project', fetch=False, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount > 0

def test_simple_named_fields_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity. The fetch specifies a small number of known valid
        attributes on the Rally entity.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('Project', fetch="Owner,State", limit=10)
    assert response.status_code == 200
    assert len(response.errors) == 0
    assert len(response._page) > 0

def test_all_fields_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity.  The fetch value is True so each entity returned in
        the response (data) will have its _hydrated attribute value set to True.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('Project', fetch=True, limit=10)
    assert response.status_code == 200
    assert len(response.errors) ==   0
    assert len(response._page)  ==  10
    for project in response:
        assert project.oid > 0
        assert len(project.Name) > 0
        assert project._hydrated == True

def test_bogus_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query specifying a entity for which there is no valid Rally entity.
        The status_code in the response must not indicate a valid request/response
        and the errors attribute must have some descriptive info about the error.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('payjammas', fetch=False, limit=10)
    assert response.status_code != 200
    assert len(response.errors) > 0

def test_good_and_bad_fields_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity. The fetch spec should contain both valid attributes and
        invalid attributes.  The request should succeed but the instances returned
        in the response data should not have the invalid attribute names, but
        should have attribute names/values for the correctly specified entity attributes.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('Project', fetch="Owner,State,Fabulote,GammaRays", limit=10)
    project = response.next()
    name  = None
    state = None
    fabulote  = None
    gammaRays = None
    try:
        name = project.Owner.Name
    except:
        name = 'undefined'
    try:
        state = project.State
    except:
        state = 'undefined'
    try:    
        fabulote = project.Fabulote
    except:
        fabulote = 'undefined'
    try:
        gammaRays = project.GammaRays
    except:
        gammaRays = 'undefined'

    assert name  != None
    assert state != None
    assert fabulote  == 'undefined'
    assert gammaRays == 'undefined'

def test_multiple_entities_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a comma
        separated list of known valid Rally entity names.  As of the initial
        swag at the Python toolkit for the Rally REST API, this is an invalid request;
        only a single Rally entity can be specified.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('Project,Workspace', fetch=False, limit=10)
    assert len(response.errors) > 0
    # note how 'Project,Workspace' has been lower-cased to 'project,workspace'
    expectedErrMsg = u"Not able to parse artifact type: project,workspace"
    actualErrMsg   = response.errors[0]
    assert actualErrMsg == expectedErrMsg

def test_multiple_page_response_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) against a Rally entity
        (Defect) known to have more than 5 items.  Set the pagesize to 5 to
        force pyral to retrieve multiple pages to satisfy the query.
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('Defect', fetch=False, pagesize=5, limit=15)
    count = 0
    for ix, bugger in enumerate(response):
        count += 1
    assert response.resultCount > 5
    assert count <= response.resultCount
    assert count == 15

def test_defects_revision_history():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) against a Rally entity
        (Defect) known to have an attribute (RevisionHistory) that has an
        attribute (Revisions) that is a sequence type (list).
        This test demonstrates the lazy-evaluation of non first-level attributes.
        Ultimately, the attributes deeper than the first level must be obtained
        and have their attributes filled out completely (_hydrated == True).
    """
    rally = Rally(server=PREVIEW, user=PREVIEW_USER, password=PREVIEW_PSWD)
    response = rally.get('Defect', fetch=True, limit=10)
    
    defect1 = response.next()
    defect2 = response.next()
    assert defect1.oid != defect2.oid

    d1_revs = defect1.RevisionHistory.Revisions
    d2_revs = defect2.RevisionHistory.Revisions

    assert type(d1_revs) == types.ListType
    assert type(d2_revs) == types.ListType

    d1_rev1 = d1_revs.pop(0)
    d2_rev1 = d2_revs.pop(0)

    assert d1_rev1.RevisionNumber == 0
    assert d2_rev1.RevisionNumber == 0

    assert d1_rev1.Description != "" and len(d1_rev1.Description) > 0
    assert d2_rev1.Description != "" and len(d2_rev1.Description) > 0

    assert d1_rev1._hydrated == True
    assert d2_rev1._hydrated == True

#test_basic_query()
#test_simple_named_fields_query()
#test_all_fields_query()
#test_bogus_query()
#test_good_and_bad_fields_query()
#test_multiple_entities_query()
#test_multiple_page_response_query()
#test_defects_revision_history()

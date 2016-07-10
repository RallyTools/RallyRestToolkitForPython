#!/usr/bin/env python

import sys, os
import types
if sys.version_info < (3, 0):
    import urllib # for errors
    from urllib import quote, unquote
else: # 3.0+
    from urllib.parse import quote, unquote
    import urllib.request
    import urllib.error # for errors
import py

from pyral import Rally
import pyral

InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError
from pyral.query_builder import RallyUrlBuilder, RallyQueryFormatter

##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD
from rally_targets import DEFAULT_WORKSPACE, NON_DEFAULT_PROJECT

##################################################################################################

def test_basic_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    response = rally.get('Project', fetch=False, limit=10)
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
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
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
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    response = rally.get('Project', fetch=True, limit=10)
    assert response.status_code == 200
    assert len(response.errors) ==   0
    #assert len(response._page)  ==   12
    assert response.resultCount > 12
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
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    bogus_entity = "Payjammas"
    expectedErrMsg = "not a valid Rally entity: %s" % bogus_entity
    with py.test.raises(InvalidRallyTypeNameError) as excinfo:
        response = rally.get('Payjammas', fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'InvalidRallyTypeNameError'
    assert actualErrVerbiage == bogus_entity

def test_good_and_bad_fields_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity. The fetch spec should contain both valid attributes and
        invalid attributes.  The request should succeed but the instances returned
        in the response data should not have the invalid attribute names, but
        should have attribute names/values for the correctly specified entity attributes.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    response = rally.get('Project', fetch="Owner,State,Fabulote,GammaRays", limit=10)
    project = next(response)
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
        separated list of known valid Rally entity names.  
        As of Rally WSAPI 1.x, this is an invalid request; 
        only a single Rally entity can be specified.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    multiple_entities = "Project,Workspace"
    with py.test.raises(InvalidRallyTypeNameError) as excinfo:
        response = rally.get(multiple_entities, fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    assert excinfo.value.__class__.__name__ == 'InvalidRallyTypeNameError'
    assert actualErrVerbiage == multiple_entities

def test_multiple_page_response_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) against a Rally entity
        (Defect) known to have more than 5 items.  Set the pagesize to 5 to
        force pyral to retrieve multiple pages to satisfy the query.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
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
        attribute (Revisions) that is a Rally collections reference.
        This test demonstrates the lazy-evaluation of non first-level attributes.
        Ultimately, the attributes deeper than the first level must be obtained
        and have their attributes filled out completely (_hydrated == True).
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    response = rally.get('Defect', fetch=True,  limit=10)
    
    defect1 = next(response)
    defect2 = next(response)
    assert defect1.oid != defect2.oid

    d1_revs = defect1.RevisionHistory.Revisions
    d2_revs = defect2.RevisionHistory.Revisions

    assert type(d1_revs) == list
    assert type(d2_revs) == list

    d1_rev1 = d1_revs.pop()  # now the revs are in stack order, newest first, original the last
    d2_rev1 = d2_revs.pop()  # ditto

    assert d1_rev1.RevisionNumber == 0
    assert d2_rev1.RevisionNumber == 0

    assert d1_rev1.Description != "" and len(d1_rev1.Description) > 0
    assert d2_rev1.Description != "" and len(d2_rev1.Description) > 0

    assert d1_rev1._hydrated == True
    assert d2_rev1._hydrated == True

def test_single_condition_query_plain_expression():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query with a single qualifying criterion against a Rally entity
        (Defect) known to exist for which the qualifying criterion should return 
        one or more Defects. The qualifying criterion is a string that is _not_
        surrounded with paren chars.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    workspace = rally.getWorkspace()
    project   = rally.getProject()
    qualifier = 'State = "Submitted"'

    response = rally.get('Defect', fetch=True, query=qualifier, limit=10)
    assert response.resultCount > 0

def test_single_condition_query_parenned():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query with a single qualifying criterion against a Rally entity
        (Defect) known to exist for which the qualifying criterion should return 
        one or more Defects. The qualifying criterion is a string that _is_
        surrounded with paren chars.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifier = "(State = Submitted)"
    #qualifier = '(FormattedID = "US100")'
    response = rally.get('Defect', fetch=True, query=qualifier, limit=10)
    assert response.resultCount > 0

def test_two_condition_query_in_unparenned_string():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query with two qualifying conditions against a Rally entity
        (Defect) known to exist for which the qualifying criterion should return 
        one or more Defects. The qualifying criterion is a list that contains
        two condition strings, each condition string does _not_ have any 
        surrounding paren chars.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    double_qualifier = "State = Submitted AND FormattedID != US100"
    response = rally.get('Defect', fetch=True, query=double_qualifier, limit=10)
    assert response.resultCount > 0

def test_two_condition_query_parenned():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query with two qualifying conditions against a Rally entity
        (Defect) known to exist for which the qualifying criterion should return 
        one or more Defects. The qualifying criterion is a string that _is_
        surrounded with paren chars and each condition itself is surrounded by
        parens..
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifiers = "(State = Submitted) AND (FormattedID != US100)"
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0

def test_single_condition_query_as_list():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifier = ['State != Open']
    response = rally.get('Defect', fetch=True, query=qualifier, limit=10)
    assert response.resultCount > 0

def test_two_condition_query_in_list():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query with two qualifying conditions against a Rally entity
        (Defect) known to exist for which the qualifying criterion should return 
        one or more Defects. The qualifying criterion is a list that contains
        two condition strings, each condition string does _not_ have any 
        surrounding paren chars.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifiers = ["State = Submitted", "FormattedID != US100"]
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0

def test_three_condition_query_in_list():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a query with three qualifying conditions against a Rally entity
        (Defect) known to exist for which the qualifying criterion should return 
        one or more Defects. The qualifying criterion is a list that contains
        three condition strings, each condition string does _not_ have any 
        surrounding paren chars.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    #qualifiers = ["State = Submitted", "FormattedID != DE100", "Owner.UserName != horsefeathers"]
    qualifiers = ["State = Submitted", "FormattedID != DE100", "Severity != UltraMegaHurt"]
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0

def test_five_condition_query_in_list():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifiers = ["State = Submitted",
                  "FormattedID < DE6000",
                  "FormattedID != DE5986",
                  'Priority = "High Attention"',
                  "Severity != Cosmetic"
                 ]
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0
    
def test_single_condition_query_as_dict():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifier = {'State' : 'Submitted'}
    response = rally.get('Defect', fetch=True, query=qualifier, limit=10)
    assert response.resultCount > 0

def test_two_conditions_query_as_dict():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifiers = {'State' : 'Submitted',
                  'Ready' : 'False'
                 }
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0

def test_three_conditions_query_as_dict():
    """
        
    """
    # TODO: note that an attribute value containing a '/' char will fail
    #       have yet to determine how to get this to work with Rally WSAPI ...
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifiers = {"State"    : "Submitted",
                  "Priority" : "High Attention",
                  "Ready"    : "False"
                  #'Severity : "Major Problem"',
                  #'Severity : "Crash/DataLoss"',
                 }
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0

def test_limit_query():
    """
        Use a pagesize of 200 and a limit of 80 in the params in the URL
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifier = "State = Submitted"
    response = rally.get('Defect', fetch=True, query=qualifier, pagesize=200, limit=80)
    items = [item for item in response]
    assert len(items) == 80

def test_start_value_query():
    """
        Use a pagesize of 200 and a start index value of 300 in the params in the URL
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifier = "State = Submitted"
    response = rally.get('Defect', fetch=True, query=qualifier, pagesize=200, start=2000)
    items = [item for item in response]
    assert len(items) > 200 
    assert len(items) < 600

def test_start_and_limit_query():
    """
        Use a pagesize of 50 and a start index value of 20 and a limit of 60 in the params in the URL
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    qualifier = "State = Submitted"
    response = rally.get('Defect', fetch=True, query=qualifier, pagesize=50, start=20,limit=60)
    items = [item for item in response]
    assert len(items) == 60

def test_query_target_value_with_ampersand():
    """
        Query for a Project.Name = 'R&D'
    """
    criteria = ['Project.Name = R&D']
    result = RallyQueryFormatter.parenGroups(criteria)
    assert unquote(result) == 'Project.Name = R&D'.replace('&', '%26')

    criteria = ['Project.Name = "R&D"']
    result = RallyQueryFormatter.parenGroups(criteria)
    assert unquote(result) == 'Project.Name = "R&D"'.replace('&', '%26')

    criteria = ['Project.Name contains "R&D"']
    result = RallyQueryFormatter.parenGroups(criteria)
    assert unquote(result) == 'Project.Name contains "R&D"'.replace('&', '%26')

    criteria = 'Railhead.Company.Name != "Atchison Topeka & Santa Fe & Cunard Lines"'
    result = RallyQueryFormatter.parenGroups(criteria)
    assert unquote(result) == criteria.replace('&', '%26')


def test_query_target_value_with_and():
    """
        Query for a Project.Name = 'Operations and Support Group'
    """
    criteria = 'Project.Name = "Operations and Support Group"'
    result = RallyQueryFormatter.parenGroups(criteria)
    assert result == 'Project.Name = "Operations and Support Group"'.replace(' ', '%20')

    criteria = ['State != Open', 'Name !contains "Henry Hudson and Company"']
    result = RallyQueryFormatter.parenGroups(criteria)
    assert result.replace('%21%3D', '!=') == '(State != Open) AND (Name !contains "Henry Hudson and Company")'.replace(' ', '%20')

def test_query_with_special_chars_in_criteria():
    """
       DE3228 in DEFAULT_WORKSPACE / NON_DEFAULT_PROJECT has Name = Special chars:/!@#$%^&*()-=+[]{};:./<>?/ 
       query for it by looking for it by the name value
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    rally.setWorkspace(DEFAULT_WORKSPACE)
    rally.setProject(NON_DEFAULT_PROJECT)
    rally.enableLogging('spec_char_query')
    criteria = 'Name = "distinctive criteria of -32% degradation in rust protection"'
    response = rally.get('Defect', fetch=True, query=criteria, limit=10)
    assert response.__class__.__name__ == 'RallyRESTResponse'
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount == 1

    criteria = 'Name = "Looking for the #blowback hashtag"'
    response = rally.get('Defect', fetch=True, query=criteria, limit=10)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount == 1

    special_chars = "/!@#$%^*_-+=?{}[]:;,<>"
    # characters that break the RallyQueryFormatter and/or WSAPI: ( ) ~ & | backslash
    for character in special_chars:
        criteria = 'Name contains "%s"' % character
        response = rally.get('Defect', fetch=True, query=criteria, limit=10)
        assert response.__class__.__name__ == 'RallyRESTResponse'
        assert response.status_code == 200
        assert response.errors   == []
        assert response.warnings == []
        assert response.resultCount >= 1

    criteria = 'Name = "Special chars:/!@#$%^*-=+[]{};:.<>? in the name field"'
    response = rally.get('Defect', fetch=True, query=criteria, limit=10)
    assert response.__class__.__name__ == 'RallyRESTResponse'
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount >= 1

def test_query_with_matched_parens_in_condition_value():
    """
        'REST Toolkit Testing' / 'Sample Project' has a Release in it whose name contains a matched paren pair
        make sure a query containing a condition looking for the Release by this name succeeds.
    """
    target_workspace = 'REST Toolkit Testing'
    target_project   = 'Sample Project'

    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, workspace=target_workspace, project=target_project)
    rally.enableLogging('query_condition_value_has_matched_internal_parens')

    criteria = 'Name = "8.5 (Blah and Stuff)"'
    response = rally.get('Release', fetch=True, query=criteria, limit=10)

    assert response.__class__.__name__ == 'RallyRESTResponse'
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount >= 1
    release = next(response)
    assert release.Name == '8.5 (Blah and Stuff)'


#test_basic_query()
#test_simple_named_fields_query()
#test_all_fields_query()
#test_bogus_query()
#test_good_and_bad_fields_query()
#test_multiple_entities_query()
#test_multiple_page_response_query()
#test_defects_revision_history()
#test_single_condition_query_plain_expression()
#test_single_condition_query_parenned()
#test_two_condition_query_in_unparenned_string()
#test_two_condition_query_parenned()
#test_single_condition_query_in_list()
#test_two_condition_query_in_list()
#test_three_condition_query_in_list()
#test_five_condition_query_in_list()
#test_single_condition_query_as_dict()
#test_two_conditions_query_as_dict()
#test_three_conditions_query_as_dict()
#test_limit_query()
#test_start_value_query()
#test_start_and_limit_query()
#test_query_target_value_with_ampersand()
#test_query_target_value_with_and()
#test_query_with_special_chars_in_criteria

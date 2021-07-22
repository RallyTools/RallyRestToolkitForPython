#!/usr/bin/env python

import sys, os
import types
import urllib
import py

try:
    from urllib import unquote
except:
    from urllib.parse import unquote

import pyral
from pyral import Rally

InvalidRallyTypeNameError = pyral.entity.InvalidRallyTypeNameError
from pyral.query_builder import RallyUrlBuilder, RallyQueryFormatter

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD
from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT, NON_DEFAULT_PROJECT
from rally_targets import BOONDOCKS_WORKSPACE, BOONDOCKS_PROJECT
from rally_targets import PROJECT_SCOPING_TREE
TLP_DICT = PROJECT_SCOPING_TREE['TOP_LEVEL_PROJECT']
TLP_DICT_keys = [key for key in TLP_DICT.keys()]
COLD_PROJECT = TLP_DICT_keys[0]

##################################################################################################

def test_basic_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    response = rally.get('Project', fetch=True, limit=10)
    assert response.status_code == 200
    assert len(response.errors) ==   0
    assert response.resultCount > 1
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
        separated list of known valid Rally entity names.  
        As of Rally WSAPI 1.x, this is an invalid request; 
        only a single Rally entity can be specified.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    multiple_entities = "Project,Workspace"
    with py.test.raises(InvalidRallyTypeNameError) as excinfo:
        response = rally.get(multiple_entities, fetch=False, limit=10)
    actualErrVerbiage = excinfo.value.args[0]
    assert excinfo.value.__class__.__name__ == 'InvalidRallyTypeNameError'
    assert actualErrVerbiage == multiple_entities

def test_multiple_page_response_query():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) against a Rally entity
        (Defect) known to have more than 5 items.  Set the pagesize to 5 to
        force pyral to retrieve multiple pages to satisfy the query.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    response = rally.get('Defect', fetch=True,  limit=10)
    
    defect1 = response.next()
    defect2 = response.next()
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    qualifiers = "((State = Submitted) AND (FormattedID != US100))"
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0

def test_four_ored_conditions_in_parrened_string():
    """
        Take a user query with OR conditions in which the parenneg groups are 
        already supplied in Rally conformant "binary" condition style
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD,
                  workspace=BOONDOCKS_WORKSPACE, project=BOONDOCKS_PROJECT)
    qualifiers = '((((Name = "Brazen%20Milliwogs") OR (Name = "Jenkins")) OR (Name = "Refusnik")) OR (Name = "Salamandra"))'
    response = rally.get('Project', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0
    projects = [project for project in response]
    #print([project.Name for project in projects])
    assert response.resultCount == 2  # Only Jenkins and Salamandra exist or or accessible to the accessing account

def test_single_condition_query_as_list():
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    #qualifiers = ["State = Submitted", "FormattedID != DE100", "Owner.UserName != horsefeathers"]
    qualifiers = ["State = Submitted", "FormattedID != DE100", "Severity != UltraMegaHurt"]
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0

def test_five_condition_query_in_list():
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    qualifiers = ["State = Submitted",
                  "FormattedID < DE22",
                  "FormattedID != DE17",
                  'Priority = "High Attention"',
                  "Severity != Cosmetic"
                 ]
    response = rally.get('Defect', fetch=True, query=qualifiers, limit=10)
    assert response.resultCount > 0
    
def test_single_condition_query_as_dict():
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    qualifier = {'State' : 'Submitted'}
    response = rally.get('Defect', fetch=True, query=qualifier, limit=10)
    assert response.resultCount > 0

def test_two_conditions_query_as_dict():
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
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
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    qualifier = "State = Submitted"
    response = rally.get('Defect', fetch=True, query=qualifier, pagesize=100, limit=30)
    items = [item for item in response]
    assert len(items) == 30

def test_start_value_query():
    """
        Use a pagesize of 200 and a start index value of 10 in the params in the URL
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    qualifier = "State = Submitted"
    response = rally.get('Defect', fetch=True, query=qualifier, pagesize=200, start=10)
    items = [item for item in response]
    assert len(items) > 20 
    assert len(items) < 1000

def test_start_and_limit_query():
    """
        Use a pagesize of 50 and a start index value of 10 and a limit of 40 in the params in the URL
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    qualifier = "State = Submitted"
    response = rally.get('Defect', fetch=True, query=qualifier, pagesize=50, start=10,limit=40)
    items = [item for item in response]
    assert len(items) >  10
    assert len(items) <= 40

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
       DE3228 in DEFAULT_WORKSPACE / DEFAULT_PROJECT has Name = Special chars:/!@#$%^&*()-=+[]{};:./<>?/ 
       query for it by looking for it by the name value
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    rally.setWorkspace(DEFAULT_WORKSPACE)
    rally.setProject(DEFAULT_PROJECT)
    #rally.enableLogging('spec_char_query')
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

    special_chars = "/!@#$%^*_-+=?{}[]:;,.<>"
    # characters that break the RallyQueryFormatter and/or WSAPI: ( ) ~ & | backslash
    for character in special_chars:
        criteria = 'Name contains "%s"' % character
        response = rally.get('Defect', fetch=True, query=criteria, limit=10)
        assert response.__class__.__name__ == 'RallyRESTResponse'
        assert response.status_code == 200
        assert response.errors   == []
        assert response.warnings == []
        assert response.resultCount >= 1

    criteria = 'Name = "Special chars:/!@#$%^*-=+[]{};:,.<>? in the name field"'
    response = rally.get('Defect', fetch=True, query=criteria, limit=10)
    assert response.__class__.__name__ == 'RallyRESTResponse'
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount >= 1

def test_query_with_matched_parens_in_condition_value():
    """
        The default workspace and project has  a Release in it whose name contains a matched paren pair
        make sure a query containing a condition looking for the Release by this name succeeds.
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    #rally.enableLogging('query_condition_value_has_matched_internal_parens')

    criteria = 'Name = "8.5 (Blah and Stuff)"'
    response = rally.get('Release', fetch=True, query=criteria, limit=10)

    assert response.__class__.__name__ == 'RallyRESTResponse'
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount >= 1
    release = response.next()
    assert release.Name == '8.5 (Blah and Stuff)'

def test_query_using_project_scoping_options():
    """
        Target a Project that has subprojects with a population of Stories for a query,
        using the projectScopeDown=False and then again with projectScopeDown=True.
        The query specifying projectScopeDown=True should return more Stories than the initial query
    """
    SCOPE_ROOT_PROJECT = 'Arctic Elevation'
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    projects = rally.getProjects(workspace=DEFAULT_WORKSPACE)

    rally.setProject(SCOPE_ROOT_PROJECT)

    response = rally.get('Story', fetch="FormattedID,Name,State,Project", project=SCOPE_ROOT_PROJECT)
    stories = [item for item in response]
    proj_scope_stories = [story for story in stories if story.Project.Name == SCOPE_ROOT_PROJECT]
    assert len(proj_scope_stories) == len(stories)
    ps_pop = len(stories)

    response = rally.get('Story', fetch="FormattedID,Name,State,Project", project=SCOPE_ROOT_PROJECT,
                         projectScopeDown=True)
    downscope_stories = [item for item in response]
    underfoot = [story for story in downscope_stories if story.Project.Name != SCOPE_ROOT_PROJECT]
    assert underfoot
    assert len(downscope_stories) > len(underfoot)
    assert len(downscope_stories) > ps_pop

    response = rally.get('Story', fetch="FormattedID,Name,State,Project", project=SCOPE_ROOT_PROJECT,
                         projectScopeDown=False)
    upper_crust_stories = [item for item in response]
    assert len(upper_crust_stories) == ps_pop

    ISOLATED_SUB_PROJECT = 'Aurora Borealis'
    #print("\nISOLATED_SUB_PROJECT: %s" % ISOLATED_SUB_PROJECT)

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=ISOLATED_SUB_PROJECT, projectScopeDown=False,
                         order="FormattedID,Project.Name")
    assert response.resultCount == 2

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=ISOLATED_SUB_PROJECT, projectScopeDown=True)
    assert response.resultCount == 2

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=ISOLATED_SUB_PROJECT, projectScopeUp=True)
    all_stories = [item for item in response]
    iso_sp_stories = [item for item in all_stories if item.Project.Name == ISOLATED_SUB_PROJECT]
    other_stories  = [item for item in all_stories if item.Project.Name != ISOLATED_SUB_PROJECT]
    assert len(iso_sp_stories) == 2
    assert len(other_stories)  > 0


    BEEFIER_SUB_PROJECT = 'Sub Arctic Conditions'
    #print("BEEFIER_SUB_PROJECT: %s" % BEEFIER_SUB_PROJECT)
    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BEEFIER_SUB_PROJECT,
                         projectScopeDown=False)
    initial_q_stories = [item for item in response]
    orig_bfee_stories = [story for story in initial_q_stories if story.Project.Name == BEEFIER_SUB_PROJECT ]
    assert initial_q_stories
    assert orig_bfee_stories
    assert len(orig_bfee_stories) == len(initial_q_stories)

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BEEFIER_SUB_PROJECT,
                         projectScopeUp=True,
                         projectScopeDown=False)
    assert response.resultCount > len(initial_q_stories)

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BEEFIER_SUB_PROJECT,
                         projectScopeDown=True)
    assert response.resultCount == 5

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BEEFIER_SUB_PROJECT,
                         projectScopeUp=False,
                         projectScopeDown=True)
    assert response.resultCount == 5

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BEEFIER_SUB_PROJECT,
                         projectScopeUp=True,
                         projectScopeDown=True)
    all_stories = [item for item in response]
    bfee_sp_stories = [item for item in all_stories if item.Project.Name == BEEFIER_SUB_PROJECT]
    other_stories   = [item for item in all_stories if item.Project.Name != BEEFIER_SUB_PROJECT]
    assert len(bfee_sp_stories) == len(orig_bfee_stories)
    assert len(other_stories)  > 0

    # BOTTOM_PROJECT is a sub-project under BEEFIER_SUB_PROJECT
    BOTTOM_PROJECT = 'Bristol Bay Barons'
    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BOTTOM_PROJECT)
    assert response.resultCount == 2

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BOTTOM_PROJECT,
                         projectScopeDown=True)
    assert response.resultCount == 2

    response = rally.get('Story', fetch="FormattedID,Name,State,Project",
                         project=BOTTOM_PROJECT,
                         projectScopeUp=True, projectScopeDown=True)
    assert response.resultCount > len(bfee_sp_stories)


def test_query_in_subset_operator():
    """
        Query for State in the subset of {'Defined', 'In-Progress'}
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    #qualifier = '(ScheduleState In "Defined,In-Progress")'   # works cuz expression is parenned
    #qualifier = 'ScheduleState In "Defined,In-Progress"'     # works when subset is quoted
    qualifier = 'ScheduleState In Defined,In-Progress'        # works when no space after comma
    response = rally.get('Defect', fetch=True, query=qualifier, pagesize=100, limit=100)
    print(response.status_code)
    assert response.status_code == 200
    assert len(response.errors) == 0
    assert len(response.warnings) == 0

    items = [item for item in response]

    assert len(items) > 10
    defined   = [item for item in items if item.ScheduleState == 'Defined']
    inprog    = [item for item in items if item.ScheduleState == 'In-Progress']
    completed = [item for item in items if item.ScheduleState == 'Completed']
    accepted  = [item for item in items if item.ScheduleState == 'Accepted']
    assert len(defined) > 0
    assert len(inprog)  > 0
    assert len(completed) == 0
    assert len(accepted)  == 0

def test_query_not_in_subset_operator():
    """
        Query for Priority not in the subset of {'Defined', 'Completed'}
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, project=COLD_PROJECT)
    qualifier = 'ScheduleState !in Defined,Completed'
    #qualifier = '((ScheduleState != Defined) AND (ScheduleState != Completed))'
    response = rally.get('Story', fetch=True, query=qualifier, pagesize=100, limit=100, projectScopeDown=True)
    assert response.status_code == 200
    assert len(response.errors) == 0
    assert len(response.warnings) == 0

    items = [item for item in response]
    sched_states = [item.ScheduleState for item in items]
    ss = list(set(sorted(sched_states)))
    assert len(ss) == 2

    defined   = [item for item in items if item.ScheduleState == 'Defined']
    inprog    = [item for item in items if item.ScheduleState == 'In-Progress']
    completed = [item for item in items if item.ScheduleState == 'Completed']
    accepted  = [item for item in items if item.ScheduleState == 'Accepted']

    assert len(defined)   == 0
    assert len(completed) == 0
    assert len(inprog)    > 0
    assert len(accepted)  > 0

def test_query_having_subset_exclusion_cond_and_other_conds():
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, project=COLD_PROJECT)
    base_cond = 'PlanEstimate > 2'
    subset_exclusion = 'ScheduleState !in Defined,Completed'
    not_contains = 'Name !contains "oo"'
    criteria = [base_cond, subset_exclusion, not_contains]
    response = rally.get('Story', fetch=True, query=criteria, pagesize=100, limit=100, projectScopeDown=True)
    assert response.status_code   == 200
    assert len(response.errors)   == 0
    assert len(response.warnings) == 0

    items = [item for item in response]
    sched_states = [item.ScheduleState for item in items]
    ss = list(set(sorted(sched_states)))
    assert len(ss) == 2

    defined   = [item for item in items if item.ScheduleState == 'Defined']
    inprog    = [item for item in items if item.ScheduleState == 'In-Progress']
    completed = [item for item in items if item.ScheduleState == 'Completed']
    accepted  = [item for item in items if item.ScheduleState == 'Accepted']

    assert len(defined)   == 0
    assert len(completed) == 0
    assert len(inprog)    > 0
    assert len(accepted)  > 0

def test_query_not_in_subset_with_3_exclusion_values():
    """
        Query for Priority not in the subset of {'Defined', 'Completed', 'Accepted'}
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, project=COLD_PROJECT)
    qualifier = 'ScheduleState !in Defined,Completed,Accepted'
    response = rally.get('Story', fetch=True, query=qualifier, pagesize=100, limit=100, projectScopeDown=True)
    assert response.status_code == 200
    assert len(response.errors) == 0
    assert len(response.warnings) == 0

    items = [item for item in response]
    sched_states = [item.ScheduleState for item in items]
    ss = list(set(sorted(sched_states)))
    #assert len(ss) > 2

    defined   = [item for item in items if item.ScheduleState == 'Defined']
    inprog    = [item for item in items if item.ScheduleState == 'In-Progress']
    completed = [item for item in items if item.ScheduleState == 'Completed']
    accepted  = [item for item in items if item.ScheduleState == 'Accepted']

    assert len(defined)   == 0
    assert len(completed) == 0
    assert len(accepted)  == 0
    assert len(inprog)    > 0

def test_query_between_range_operator():
    """
        Query for CreatedDate between 2016-09-30T00:00:00Z and 2016-10-04T23:59:59.999Z'
        Should get 1 item
    """
    # Uses DEFAULT_WORKSPACE, DEFAULT_PROJECT
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    response = rally.get('Story', fetch=True, pagesize=100, limit=100)
    all_stories = [item for item in response]
    assert len(all_stories) > 8
    cds = [story.CreationDate for story in all_stories]
    range_start_date = '2016-09-30T00:00:00Z'
    range_end_date   = '2016-10-04T23:59:59Z'
    prior_to_start_date = [story for story in all_stories if story.CreationDate < range_start_date]
    after_end_date      = [story for story in all_stories if story.CreationDate > range_end_date]
    assert prior_to_start_date
    assert after_end_date
    tweener_stories     = [story for story in all_stories
                                  if story.CreationDate >= range_start_date
                                 and story.CreationDate <= range_end_date]
    assert len(tweener_stories) == 1

    criteria = f'CreationDate between {range_start_date} and {range_end_date}'
    response = rally.get('Story', fetch=True, query=criteria, pagesize=100, limit=100)
    target_stories = [story for story in response]
    assert len(target_stories) == 1

def test_query_not_between_range_operator():
    """
        Query for CreatedDate !between 2016-09-30T00:00:00Z and 2016-11-01T00:00:00Z'
        #assert result of query is has some elements less than date_1, and
        # has some greater than date_2 and none in the range specified
    """
    # Uses DEFAULT_WORKSPACE, DEFAULT_PROJECT
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    range_start_date = '2016-09-30T00:00:00Z'
    range_end_date   = '2016-11-01T00:00:00Z'
    criteria = f'CreationDate !between {range_start_date} and {range_end_date}'
    response = rally.get('Story', fetch=True, query=criteria, pagesize=100, limit=100)
    target_stories = [story for story in response]
    assert len(target_stories) > 2
    prior_date_stories = [story for story in target_stories if story.CreationDate < range_start_date]
    after_date_stories = [story for story in target_stories if story.CreationDate > range_end_date]
    assert prior_date_stories
    assert after_date_stories
    assert len(prior_date_stories) + len(after_date_stories) == len(target_stories)
    tweener_stories     = [story for story in target_stories
                           if  story.CreationDate >= range_start_date
                           and story.CreationDate <= range_end_date]
    assert len(tweener_stories) == 0

def test_query_range_with_other_conds():
    """
        Query for CreatedDate between 2016-09-29T14:30:00Z and 2016-10-01T08:00:00Z'
        along with a condition that some field is not null (or null)...
        assert that there are results only within the date-time range specified
    """
    # Uses DEFAULT_WORKSPACE, DEFAULT_PROJECT
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    response = rally.get('Story', fetch=True, pagesize=100, limit=100)
    all_stories = [item for item in response]
    assert len(all_stories) > 8
    #for story in all_stories:
    #    plan_est = str(int(story.PlanEstimate)) if story.PlanEstimate else " "
    #    print(f'{story.FormattedID:<5} {story.CreationDate} {story.Project.Name} {story.Iteration}  {plan_est:>4} {story.Name}')

    range_start_date = '2016-09-29T14:30:00Z'
    range_end_date   = '2016-10-01T08:00:00Z'
    range_cond = f'CreationDate between {range_start_date} and {range_end_date}'
    base_cond = 'Iteration = null'
    proj_cond = 'Project != null'
    noncon_cond = 'Name contains with'
    criteria = [base_cond, range_cond, proj_cond, noncon_cond]
    response = rally.get('Story', fetch=True, query=criteria, pagesize=100, limit=100)
    target_stories = [story for story in response]
    assert len(target_stories) >= 1
    #print('-' * 60)
    #for story in target_stories:
    #    plan_est = str(int(story.PlanEstimate)) if story.PlanEstimate else " "
    #    print(f'{story.FormattedID:<5} {story.CreationDate} {story.Project.Name} {story.Iteration}  {plan_est:>4} {story.Name}')


def test_query_target_value_with_ampersand():
    """
        Query for a Project.Name = 'R&D'

        Note: This test must be last as there is some weird interplay going on when this is higher up
              in the file.  3 Tests fail having nothing to do with ampersands in the query criteria
              when this test appears before them.
    """
    criteria = ['Project.Name = R&D']
    result = RallyQueryFormatter.parenGroups(criteria)
    #assert unquote(result) == 'Project.Name = R&D'.replace('&', '%26')
    assert unquote(result) == 'Project.Name = R&D'

    criteria = ['Project.Name = "R&D"']
    result = RallyQueryFormatter.parenGroups(criteria)
    #assert unquote(result) == 'Project.Name = "R&D"'.replace('&', '%26')
    assert unquote(result) == 'Project.Name = "R&D"'

    criteria = ['Project.Name contains "R&D"']
    result = RallyQueryFormatter.parenGroups(criteria)
    #assert unquote(result) == 'Project.Name contains "R&D"'.replace('&', '%26')
    assert unquote(result) == 'Project.Name contains "R&D"'

    criteria = 'Railhead.Company.Name != "Atchison Topeka & Santa Fe & Cunard Lines"'
    result = RallyQueryFormatter.parenGroups(criteria)
    #assert unquote(result) == criteria.replace('&', '%26')
    assert unquote(result) == criteria

    APIKEY = "_useYourRallyKey"
    RALLY_100_APIKEY = "_lsMzURZTRyBoD3bwnpn5kUZvDQkRIoEeGkq7QNkg"
    target_workspace = 'Rally'
    target_project   = 'R&D'
    rally = Rally(server='rally1.rallydev.com', apikey=RALLY_100_APIKEY, workspace=target_workspace, project=target_project)
    pifs = rally.get('Feature', fetch='Name,FormattedID')
    assert pifs.resultCount == 26  # as of 02/05/2021 this was correct, total of 26 Features for R&D
    # The following does not work...
    pifs = rally.get('Feature', fetch='Name,FormattedID', query=['Project.Name = "R&D"', 'Name contains "On-Prem"'])
    assert pifs.resultCount == 7   # as of 02/05/2021 this was correct, 7 Features had "On-Prem" in the Name

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
#test_query_target_value_with_and()
#test_query_with_special_chars_in_criteria
#test_query_target_value_with_ampersand()

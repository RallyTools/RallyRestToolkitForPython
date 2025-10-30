#!/usr/bin/env python

import sys, os
import types
import pytest

from pyral import Rally, RallyUrlBuilder, RallyRESTAPIError
from pyral.entity   import classFor
from pyral.restapi  import hydrateAnInstance

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD
from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT, NON_DEFAULT_PROJECT
from rally_targets import ALTERNATE_WORKSPACE, ALTERNATE_PROJECT
from internal_rally_targets import APIKEY

RALLY_SUB_100_USER = ''
RALLY_SUB_100_PSWD = ''
RALLY_SUB_100_API_KEY = APIKEY

REFABLE_ARTIFACT = 'hierarchicalrequirement/141184568124'

##################################################################################################


dummy_data = {
              'ExternalId' : 'abcde12345bb999ee7733aa77ccfedbeaf', #last commit's sha
              'ExternalFormattedId' :  11,
              'Url'        : 'https://github.com/RallyTools/RallyRestToolkitForJava/pull/11/',
              'Name'       : 'Prepare for Maven Central Deployment',
              'Description': 'What makes you happy about this Pull Request?  Katy Perry is staying in my tent tonight!',
              #'Workspace'  :  DEFAULT_WORKSPACE,
              #'Artifact'   :  'hierarchicalrequirement/81379898588' # ref to the Artifact mentioned in some commit message
              'Artifact'   :  REFABLE_ARTIFACT
              # CreationDate
              # SubscriptionID
              # Version
              # Subclass_Type
             }

#TESTN = 'kbiz.testn.f4tech.com'
#TESTN_USER = 'klehman@rallydev.com'
#TESTN_PSWD = 'Password'
#
# def test_create_local_pull_request_instance():
#     fake_oid = 12345698765
#
#     rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
#     context1 = rally.contextHelper.currentContext()
#     pr_class = classFor['PullRequest']
#     pr = pr_class(fake_oid, dummy_data['Name'], dummy_data['Url'], context1)
#     assert pr is not None
#     assert pr.oid  == fake_oid
#     assert pr.Name == dummy_data['Name']
#     hydrateAnInstance(context1, dummy_data, existingInstance=pr)
#     assert pr.ExternalId  == dummy_data['ExternalId']
#     assert pr.ExternalFormattedId  == dummy_data['ExternalFormattedId']
#     assert pr.Url  == dummy_data['Url']
#     assert pr.Description  == dummy_data['Description']
#     assert pr.Workspace == DEFAULT_WORKSPACE


def test_post_pull_request():
    expectedErrMsg = '422 Requested type name "pullrequest" is unknown.'
    #rally = Rally(server=TESTN, user=TESTN_USER, password=TESTN_PSWD)
    #rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    rally = Rally(server=RALLY, apikey=RALLY_SUB_100_API_KEY)
    #with pytest.raises(RallyRESTAPIError) as excinfo:
    pr = rally.create('PullRequest', dummy_data, project=None)
    assert pr is not None
    assert pr.oid
    #actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    #assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    #assert expectedErrMsg == actualErrVerbiage

def test_query_pull_requests():
    rally = Rally(server=RALLY, apikey=RALLY_SUB_100_API_KEY)
    attrs = "ExternalId,ExternalFormattedId,Artifact,Name,Url,Description"
    criteria = "CreationDate >= 2023-07-01T08:00:00Z"
    target_project = "Atom Smashers"
    response = rally.get('PullRequest', fetch=attrs, query=criteria, project=target_project, limit=100)
    assert response.status_code == 200
    assert len(response.errors) == 0
    assert len(response.warnings) == 0
    prs = [pr for pr in response]
    assert len(prs) > 0
    assert prs[0].Artifact
    assert prs[0].Artifact.__class__.__name__ == 'HierarchicalRequirement'
    #print (prs[0].Artifact.oid)
    #for wob in prs[0].details():
    #    print(wob)

# def test_creation_date_query():
#     rally = Rally(server=RALLY, apikey=RALLY_SUB_100_API_KEY)
#     ref_time_iso = '2017-08-30T14:00:00.000Z'
#     attrs = "ExternalId,ExternalFormattedId,Artifact,Name,Url,Description"
#     selectors = ['CreationDate >= %s' % ref_time_iso]
#     response1 = rally.get('PullRequest', fetch=attrs, query=selectors, project=None)
#     assert response1.status_code == 200
#     assert len(response1.errors) == 0
#     assert len(response1.warnings) == 0
#     prs1 = [pr for pr in response1]
#
#     response2 = rally.get('PullRequest', fetch=attrs, project=None)
#     assert response1.status_code == 200
#     assert len(response1.errors) == 0
#     assert len(response1.warnings) == 0
#     prs2 = [pr for pr in response2]
#
#     assert len(prs1) < len(prs2)


def test_delete_pull_request():
    #rally = Rally(server=TESTN, user=TESTN_USER, password=TESTN_PSWD)
    rally = Rally(server=RALLY, apikey=RALLY_SUB_100_API_KEY)
    attrs = "ExternalId,ExternalFormattedId,Artifact,Name,Url,Description"
    response = rally.get('PullRequest', fetch=attrs, project=None)
    assert response.status_code == 200
    assert len(response.errors) == 0
    assert len(response.warnings) == 0
    prs = [pr for pr in response]
    assert len(prs) > 0
    victim = prs[0]
    result = rally.delete('PullRequest', victim.oid, project=None)
    assert result == True

    response = rally.get('PullRequest', fetch=attrs, query='ObjectID = %s' % victim.oid)
    ghosts = [pr for pr in response]
    assert not ghosts



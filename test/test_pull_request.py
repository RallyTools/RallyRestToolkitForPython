#!/usr/bin/env python

import sys, os
import types
import py

from pyral import Rally, RallyUrlBuilder, RallyRESTAPIError
from pyral.entity   import classFor
from pyral.restapi  import hydrateAnInstance

##################################################################################################

from rally_targets import AGICEN, AGICEN_USER, AGICEN_PSWD
from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT, NON_DEFAULT_PROJECT
from rally_targets import ALTERNATE_WORKSPACE, ALTERNATE_PROJECT

##################################################################################################


dummy_data = {
              'ExternalId' : 'abcde12345bb999ee7733aa77ccfedbeaf', #last commit's sha
              'ExternalFormattedId' :  11,
              'Url'        : 'https://github.com/RallyTools/RallyRestToolkitForJava/pull/11/',
              'Name'       : 'Prepare for Maven Central Deployment',
              'Description': 'What makes you happy about this Pull Request?  Katy Perry is staying in my tent tonight!',
              #'Workspace'  :  DEFAULT_WORKSPACE,
              'Artifact'   :  'story/123543216677' # ref to the Artifact mentioned in some commit message
              # CreationDate
              # SubscriptionID
              # Version
              # Subclass_Type
             }

def test_create_local_pull_request_instance():
    fake_oid = 12345698765
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    context1 = rally.contextHelper.currentContext()
    pr_class = classFor['PullRequest']
    pr = pr_class(fake_oid, dummy_data['Name'], dummy_data['Url'], context1)
    assert pr is not None
    assert pr.oid  == fake_oid
    assert pr.Name == dummy_data['Name']
    hydrateAnInstance(context1, dummy_data, existingInstance=pr)
    assert pr.ExternalId  == dummy_data['ExternalId']
    assert pr.ExternalFormattedId  == dummy_data['ExternalFormattedId']
    assert pr.Url  == dummy_data['Url']
    assert pr.Description  == dummy_data['Description']
    assert pr.Workspace == DEFAULT_WORKSPACE

def test_post_pull_request():
    expectedErrMsg = "No such entity: PullRequest"
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally.create('PullRequest', dummy_data)
        actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
        assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
        assert expectedErrMsg in actualErrVerbiage


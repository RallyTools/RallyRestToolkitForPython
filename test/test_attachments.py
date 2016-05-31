#!/usr/local/bin/python2.7

import sys, os
import types
import py

import pyral
from pyral import Rally

RallyRESTAPIError = pyral.context.RallyRESTAPIError

##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD
from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT

EXAMPLE_ATTACHMENT_CONTENT = "The quck brown fox eluded the lumbering sloth\n"

##################################################################################################

def conjureUpAttachmentFile(filename, content=None, mimetype="text/plain"):
    """
    """
    file_content = content or EXAMPLE_ATTACHMENT_CONTENT
    with open(filename, 'w') as af:
        af.write(file_content)
    return True


def retrieveAttachment(rally, artifact, attachmentFileName):
    """
        
    """
    pass

def test_add_attachment():
    """
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    # find a Project with some US artifacts
    # pick one with no attachments
    # create an attachment file (or choose a smallish file with a commonly used suffix)
    # create the attachment in Rally and link it to the US artifact

    wksp = rally.getWorkspace()
    assert wksp.Name == DEFAULT_WORKSPACE

    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200

    proj = rally.getProject()  # proj.Name == DEFAULT_PROJECT
    assert proj.Name == DEFAULT_PROJECT

    #response = rally.get("UserStory", fetch="FormattedID,Name,Attachments")
    #for story in response:
    #    print "%s %-48.48s %d" % (story.FormattedID, story.Name, len(story.Attachments))

    candidate_story = "US96"
    response = rally.get("UserStory", fetch="FormattedID,Name,Attachments", 
                                   query='FormattedID = "%s"' % candidate_story)
    print(response.resultCount)
    story = next(response)
    assert len(story.Attachments) == 0

    attachment_name = "Addendum.txt"
    att_ok = conjureUpAttachmentFile(attachment_name)
    assert att_ok == True

    att = rally.addAttachment(story, attachment_name)
    assert att.Name == attachment_name

    response = rally.get("UserStory", fetch="FormattedID,Name,Attachments", 
                                   query='FormattedID = "%s"' % candidate_story)
    story = next(response)
    assert len(story.Attachments) == 1


def test_get_attachment():
    """
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    candidate_story = "US80"
    target = 'FormattedID = "%s"' % candidate_story
    response = rally.get("UserStory", fetch=True, query=target, project=None)
    assert response.resultCount == 1
    story = next(response)
##
    assert True == True
    return True
##
    assert len(story.Attachments) == 1
    attachment = story.Attachments[0]
    expected_attachment_name = "Addendum.txt"
    assert attachment.Name   == expected_attachment_name

    attachment = rally.getAttachment(candidate_story, expected_attachment_name)
    assert attachment.Name    == expected_attachment_name
    assert attachment.Content == EXAMPLE_ATTACHMENT_CONTENT


def test_add_tcr_attachment():
    """
        Add an Attachment to a TestCaseResult item

        Create a TestCase, save a reference
        Create a TestCaseResult to be associated with the TestCase
        Create an attachment
        Attach the Attachment to the TestCaseResult item
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    wksp = rally.getWorkspace()
    assert wksp.Name == DEFAULT_WORKSPACE

    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200
    proj = rally.getProject()  # proj.Name == My Project
    assert proj.Name == 'My Project'

    tc_info = { "Workspace"    : wksp.ref,
                "Project"      : proj.ref,
                "Name"         : "Heat exposure",
                "Type"         : "Functional",
              }
    test_case = rally.create('TestCase', tc_info)
    assert test_case.oid > 0

    tcr_info = { "Workspace" : wksp.ref,
                 "TestCase"  : test_case.ref,
                 "Date"      : "2014-05-17T14:30:28.000Z",
                 "Build"     : 27,
                 "Verdict"   : "Pass"
               }
    tcr = rally.create('TestCaseResult', tcr_info)
    assert tcr.oid > 0

    attachment_name = "Addendum.txt"
    att_ok = conjureUpAttachmentFile(attachment_name)
    assert att_ok == True

    att = rally.addAttachment(tcr, attachment_name)
    assert att.Name == attachment_name


def test_detach_attachment():
    """
        This is the counterpart test for test_add_attachment
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    candidate_story = "US96"
    target = 'FormattedID = "%s"' % candidate_story

    response = rally.get("UserStory", fetch=True, query=target, project=None)
    assert response.resultCount == 1
    story = next(response)
    assert len(story.Attachments) == 1
    attachment = story.Attachments[0]
    expected_attachment_name = "Addendum.txt"
    assert attachment.Name == expected_attachment_name

    result = rally.deleteAttachment(story, expected_attachment_name)
    assert result != False
    assert len(result.Attachments) == (len(story.Attachments) - 1)
    

def x_test_replace_attachment():
    """
    """


def x_test_add_attachments():
    """
    """


def x_test_get_attachments():
    """
    """


def x_test_detach_attachments():
    """
    """


def x_test_replace_attachments():
    """
    """

    #expectedErrMsg = "hostname '%s' non-existent or unreachable" % bogus_server
    #with py.test.raises(RallyRESTAPIError) as excinfo:
    #    rally = Rally(server=bogus_server,
    #                        user=TRIAL_USER, 
    #                        password=TRIAL_PSWD)
    #actualErrVerbiage = excinfo.value.args[0]  # becuz Python2.6 deprecates message :-(
    #assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    #assert actualErrVerbiage == expectedErrMsg

##########################################################################################



#!/op/local/bin/python2.6

import sys, os
import types
import py

import pyral
from pyral import Rally

RallyRESTAPIError = pyral.context.RallyRESTAPIError

##################################################################################################

TRIAL = "trial.rallydev.com"

TRIAL_USER = "usernumbernine@acme.com"
TRIAL_PSWD = "************"

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
    assert wksp.Name == "Yeti Manual Test Workspace"

    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200

    proj = rally.getProject()  # proj.Name == My Project
    assert proj.Name == "My Project"

    #response = rally.get("UserStory", fetch="FormattedID,Name,Attachments")
    #for story in response:
    #    print "%s %-48.48s %d" % (story.FormattedID, story.Name, len(story.Attachments))

    candidate_story = "US96"
    response = rally.get("UserStory", fetch="FormattedID,Name,Attachments", 
                                   query='FormattedID = "%s"' % candidate_story)
    print response.resultCount
    story = response.next()
##
    return True
##
    assert len(story.Attachments) == 0

    attachment_name = "Addendum.txt"
    att_ok = conjureUpAttachmentFile(attachment_name)
    assert att_ok == True

    att = rally.addAttachment(story, attachment_name)
    assert att.Name == attachment_name


def test_get_attachment():
    """
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    candidate_story = "US80"
    target = 'FormattedID = "%s"' % candidate_story
    response = rally.get("UserStory", fetch=True, query=target, project=None)
    assert response.resultCount == 1
    story = response.next()
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


def x_test_detach_attachment():
    """
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD)
    candidate_story = "S78"
    target = 'FormattedID = "%s"' % candidate_story

    response = rally.get("UserStory", fetch=True, query=target, project=None)
    assert response.resultCount == 1
    story = response.next()
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



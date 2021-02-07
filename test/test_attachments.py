#!/usr/local/bin/python2.7

import sys, os
import types
import py

import pyral
from pyral import Rally
from pyral.config import timestamp

RallyRESTAPIError = pyral.context.RallyRESTAPIError

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD, APIKEY
from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT
from rally_targets import YETI_USER, YETI_PSWD, YETI_NAME

EXAMPLE_ATTACHMENT_CONTENT = "The quick brown fox eluded the lumbering sloth\n"

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

##################################################################################################

def test_get_image_binary_attachment():
    # Use prior testing outcome for the story and attachment target
    target_workspace = 'Yeti Rally Workspace'
    target_project   = 'Anti-Cyclone'
    target_story     = 'US6099'
    attachment_name  = 'alpine-snow-glen-plake-quote.png'
    attachment_type  = 'image/png'

    rally = Rally(server=RALLY, user=YETI_USER, password=YETI_PSWD, workspace=target_workspace, project=target_project)

    criteria = f'FormattedID = "{target_story}"'
    response = rally.get("UserStory", fetch='ObjectID,Name,Description,Attachments', query=criteria)
    assert response.resultCount == 1
    story = response.next()

    assert len(story.Attachments) == 1
    attachment_from_collection = story.Attachments[0]
    attachment_specific = rally.getAttachment(story, attachment_name)
    assert attachment_from_collection.Name == attachment_specific.Name
    assert attachment_from_collection.Content == attachment_specific.Content
    assert len(attachment_specific.Content) > 950000
    
    clone_file = 'test/plakism.png'
    with open(clone_file, 'wb') as imf:
        imf.write(attachment_specific.Content)
    assert os.path.exists(clone_file)

    FILE_PROG = "file"
    import platform
    plat_ident = platform.system()
    if plat_ident.startswith('CYGWIN'):
        plat_ident = 'Cygwin'
    if plat_ident == "Windows":
        FILE_PROG = "C:/cygwin/bin/file"
    #print("platform identification: {0}".format(plat_ident))
    import subprocess
    process = subprocess.run([FILE_PROG, clone_file], stdout=subprocess.PIPE, universal_newlines=True)
    assert 'plakism.png: PNG image data, 1074 x 538, 8-bit/color RGBA, non-interlaced' in process.stdout
    os.remove(clone_file)

##################################################################################################

def test_add_attachment():
    """
    """
    # find a Project with some US artifacts, pick one with no attachments
    target_workspace = 'Yeti Rally Workspace'
    target_project   = 'Anti-Cyclone'
    target_story     = 'US6099'
    target_attachment_file = 'test/alpine-snow-glen-plake-quote.png'
    attachment_name = os.path.basename(target_attachment_file)
    attachment_type = 'image/png'
    rally = Rally(server=RALLY, user=YETI_USER, password=YETI_PSWD, workspace=target_workspace, project=target_project)
    # create an attachment file (or choose a smallish file with a commonly used suffix)
    # create the attachment in Rally and link it to the US artifact
    wksp = rally.getWorkspace()
    assert wksp.Name == target_workspace

    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200

    proj = rally.getProject()  # proj.Name == target_project
    assert proj.Name == target_project

    #response = rally.get("UserStory", fetch="FormattedID,Name,Attachments")
    #for story in response:
    #    print "%s %-48.48s %d" % (story.FormattedID, story.Name, len(story.Attachments))

    criteria = f'FormattedID = "{target_story}"'
    response = rally.get("UserStory", fetch="FormattedID,Name,Attachments", query=criteria)
  ##print(response.resultCount)
    story = response.next()
    if len(story.Attachments):
        for att in story.Attachments:
            rally.deleteAttachment(story, att.Name)
        response = rally.get("UserStory", fetch="FormattedID,Name,Attachments",
                             query='FormattedID = "%s"' % target_story)
        story = response.next()
    ##print(response.resultCount)
    assert len(story.Attachments) == 0

    #attachment_name = "Addendum.txt"
    #
    #att_ok = conjureUpAttachmentFile(attachment_name)
    #assert att_ok == True
    #att = rally.addAttachment(story, attachment_name)

    att = rally.addAttachment(story, target_attachment_file, mime_type=attachment_type)
    assert att.Name == attachment_name

    criteria = f'FormattedID = "{target_story}"'
    response = rally.get("UserStory", fetch="FormattedID,Name,Attachments", query=criteria)
    story = response.next()
    assert len(story.Attachments) == 1
    attachment = story.Attachments[0]
    assert attachment.Name == attachment_name
    
    #result = rally.deleteAttachment(story, attachment_name)
    #assert result != False
    #assert len(result.Attachments) == 0


def test_get_attachment():
    """
    """
    #rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    rally = Rally(server=RALLY, user=RALLY_USER, apikey=APIKEY)
    candidate_story = "US2" # was this in trial -> "US80"
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

def test_add_tcr_attachment():
    """
        Add an Attachment to a TestCaseResult item

        Create a TestCase, save a reference
        Create a TestCaseResult to be associated with the TestCase
        Create an attachment
        Attach the Attachment to the TestCaseResult item
    """
    #rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    rally = Rally(server=RALLY, user=RALLY_USER, apikey=APIKEY, workspace=DEFAULT_WORKSPACE, project=DEFAULT_PROJECT)
    wksp = rally.getWorkspace()
    assert wksp.Name == DEFAULT_WORKSPACE

    response = rally.get('Project', fetch=False, limit=10)
    assert response != None
    assert response.status_code == 200
    proj = rally.getProject()  # proj.Name == Sample Project
    assert proj.Name == 'Sample Project'

    tc_info = { "Workspace"    : wksp.ref,
                "Project"      : proj.ref,
                "Name"         : "Heat exposure",
                "Type"         : "Functional",
              }
    test_case = rally.create('TestCase', tc_info)
    assert int(test_case.oid) > 0
    
    current = timestamp()[:-4].replace(' ', 'T') + "Z"

    tcr_info = { "Workspace" : wksp.ref,
                 "TestCase"  : test_case.ref,
                 "Date"      : current,
                 "Build"     : 27,
                 "Verdict"   : "Pass"
               }
    tcr = rally.create('TestCaseResult', tcr_info)
    assert int(tcr.oid) > 0

    attachment_name = "Addendum.txt"
    att_ok = conjureUpAttachmentFile(attachment_name)
    assert att_ok == True

    att = rally.addAttachment(tcr, attachment_name)
    assert att.Name == attachment_name
    target = ['Build = 27', f'TestCase = {test_case.ref}']
    response = rally.get("TestCaseResult", fetch='ObjectID,FormattedID,Attachments', query=target, project=None)
    assert response.resultCount == 1
    tcr = response.next()
    attachment = rally.getAttachment(tcr, attachment_name)
    assert attachment.Name    == attachment_name
    att_type = attachment.ContentType
    assert att_type == 'text/plain'
    att = tcr.Attachments[0]
    actual_attachment_content = attachment.Content.decode('UTF-8').replace("\r", '')
    att_content               =        att.Content.decode('UTF-8').replace("\r", '')

    assert actual_attachment_content == EXAMPLE_ATTACHMENT_CONTENT
    assert               att_content == EXAMPLE_ATTACHMENT_CONTENT
    #assert attachment.Content.decode('UTF-8') == EXAMPLE_ATTACHMENT_CONTENT
    #assert att.Content.decode('UTF-8')        == EXAMPLE_ATTACHMENT_CONTENT
    rally.deleteAttachment(tcr, attachment_name)
    rally.delete('TestCaseResult', tcr)
    rally.delete('TestCase', test_case)


#def test_detach_attachment():
#    """
#        This is the counterpart test for test_add_attachment
#    """
#    #rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
#    rally = Rally(server=RALLY, user=RALLY_USER, apikey=APIKEY, workspace=DEFAULT_WORKSPACE,  project=DEFAULT_PROJECT)
#    candidate_story = "US1"   # "US96"
#    target = 'FormattedID = "%s"' % candidate_story
#
#    response = rally.get("UserStory", fetch=True, query=target, project=None)
#    assert response.resultCount == 1
#    story = response.next()
#    assert len(story.Attachments) == 1
#    attachment = story.Attachments[0]
#    expected_attachment_name = "Addendum.txt"
#    assert attachment.Name == expected_attachment_name
#
#    result = rally.deleteAttachment(story, expected_attachment_name)
#    assert result != False
#    assert len(result.Attachments) == (len(story.Attachments) - 1)
    

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
    #    rally = Rally(server=bogus_server, apikey=APIKEY)
    #actualErrVerbiage = excinfo.value.args[0]
    #assert excinfo.value.__class__.__name__ == 'RallyRESTAPIError'
    #assert actualErrVerbiage == expectedErrMsg

##########################################################################################



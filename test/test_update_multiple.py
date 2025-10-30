#!/usr/bin/env python

import sys, os
import types
from copy import copy

from dataclasses import dataclass, field

import pyral
from pyral import Rally

RallyRESTAPIError = pyral.context.RallyRESTAPIError

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD
#from rally_targets import APIKEY
from internal_rally_targets import APIKEY

#@dataclass
#class Story:
#    oid: int = field(default=-1)
#    Name: str = field(default="")
#    Description: str = field(default='')

##################################################################################################

def test_running_updateMultiple():
    """
         two modes are tested here, but both rely on retrieving some Stories in Rally
            1: use each retrieved Story (pyral.entity.HierarchicalRequirement instance)
               and stuff modified values in each instance and then provide a list of
               those instances the rally.updateMultiple method
            2: grab the ObjectID from each retrieved instance and use that
               as the initial value in a new update dict and then stuff the dict
               with the ElementName : new value for each attribute to be updated.
               Construct a list of those dicts and supply that list to the
               rally.updateMultiple method
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, workspace='Conny2', project='testwest')
    fields = "ObjectID,FormattedID,Name,Description,PlanEstimate,Notes,Color,ScheduleState,FlowState"

    #  mode 1: use the returned pyral.entity.HierarchicalRequirement instances to hold the updated attributes/values
    criteria = "((FormattedID >= US26) AND (FormattedID < 30))"
    response = rally.get('Story', fields=fields, query=criteria, project='testwest')
    stories = [story for story in response]

    checkd = {}
    upd_stories = []
    u_plan_estimate = 3
    u_notes         = "Dont' bother with screaming at the eagle, dive in to the hole!"
    #u_notes         = "Blather and bustle impress the addicted with attention fevers"
    u_display_color = '#4a1d7e'   # from official response in knowledge.broadcom.com inhttps://knowledge.broadcom.com/external/article/11610/rally-wsapi-display-colors-of-work-item.html
    # this seems to work, as the result in Rally item shows 'Purple'
    #u_display_color = 'Purple'   # when this value used, it appears darker that what purple is in Rally app selection...
    #u_display_color = '#AD7704'  # seen in a support response, appears to be some mustardy gold in real life...
    #u_display_color = '#a572ca'  # from eye dropper decode of Purple dot in Rally app
    #                              #   HTML Color picker https://a.atmos.washington.edu/~ovens/javascript/colorpicker.html
    #                              # although this may be accurate, in Rally it shows up as the Hex code for the color name (not Purple)
    for story in stories:
        cki = {'ObjectID': story.oid, 'FormattedID': story.FormattedID, 'PlanEstimate' : u_plan_estimate, 'Notes' : u_notes, 'DisplayColor' : u_display_color}
        checkd[story.FormattedID] =  copy(cki)
        story.PlanEstimate = u_plan_estimate
        story.Notes        = u_notes
        story.DisplayColor = u_display_color
        upd_stories.append(story)

    # check to see that stories actually had the fields updated that were intended...
    for story in stories:
        cki = checkd[story.FormattedID]
        if story.PlanEstimate != cki['PlanEstimate']:
            print(f"{story.FormattedID} PlanEstimate not actually set to test value: {cki['PlanEstimate']}")
            sys.exit(32)
        if story.DisplayColor != cki['DisplayColor']:
            print(f"{story.FormattedID} DisplayColor not actually set to test value: {cki['DisplayColor']}")
            sys.exit(32)
        if story.Notes != cki['Notes']:
            print(f"{story.FormattedID} Notes not actually set to test value: {cki['Notes']}")
            sys.exit(32)

    result = rally.updateMultiple('Story', upd_stories, fields=["PlanEstimate", "Notes", "DisplayColor"], project='testwest')
    # result should be a list of dicts with basic info about each updated item (ObjectID, FormattedID, Name, _ref)
    assert len(result) == 4

    # mode 2: create small dicts with ObjectID for item and just the updated attributes/values
    criteria = "((FormattedID >= US30) AND (FormattedID < US40))"
    response = rally.get('Story', fields=fields, query=criteria, project='testwest')
    stories = [story for story in response]
    upd_stories = []
    for story in stories:
        upd_dict = {'ObjectID' : story.oid }
        upd_dict['PlanEstimate'] = 7
        upd_dict['DisplayColor'] = 'DarkBlue'
        upd_dict['Notes']        = 'In a dozen years the plant will exceed the space allocated'
        upd_stories.append(upd_dict)
    if upd_stories:
        result = rally.updateMultiple('Story', upd_stories, fields=["PlanEstimate", "Notes", "DisplayColor"], project='testwest')
        assert 0 < len(result) < 40

##################################################################################################

#!/usr/bin/env python

import sys, os
import pprint

from pyral import Rally

##################################################################################################

from rally_targets import TRIAL, TRIAL_USER, TRIAL_PSWD

##################################################################################################

def test_rank_story_above():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and issue a get for Story items ordered by Rank ASC.
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, server_ping=False, isolated_workspace=True)
    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    assert len(stories) > 6

    story1 = stories[0]
    story2 = stories[4]
    assert story1.DragAndDropRank < story2.DragAndDropRank
    result = rally.rankAbove(story1, story2)
    assert result.status_code == 200

    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    assert stories[0].FormattedID == story2.FormattedID
    assert stories[0].DragAndDropRank < story2.DragAndDropRank

def test_rank_story_below():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, server_ping=False, isolated_workspace=True)
    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    assert len(stories) > 6

    story1 = stories[2]
    story2 = stories[4]
    assert story1.DragAndDropRank < story2.DragAndDropRank

    result = rally.rankBelow(story2, story1)
    assert result.status_code == 200

    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    assert stories[3].FormattedID    == story2.FormattedID
    assert stories[4].DragAndDropRank > story2.DragAndDropRank



def test_rank_story_to_top():
    """
    """
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, server_ping=False, isolated_workspace=True)
    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    assert len(stories) > 6

    first_story  = stories[0]
    target_story = stories[4]
    assert first_story.DragAndDropRank < target_story.DragAndDropRank
    result = rally.rankToTop(target_story)
    assert result.status_code == 200

    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    top_story    = stories[0]
    bottom_story = stories[-1]
    assert top_story.FormattedID == target_story.FormattedID
    assert top_story.DragAndDropRank < stories[1].DragAndDropRank

def test_rank_story_to_bottom():
    rally = Rally(server=TRIAL, user=TRIAL_USER, password=TRIAL_PSWD, server_ping=False, isolated_workspace=True)
    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    assert len(stories) > 6
    
    first_story   = stories[0]
    target_story  = stories[1]
    assert target_story.DragAndDropRank > first_story.DragAndDropRank

    result = rally.rankToBottom(target_story)
    assert result.status_code == 200
    response = rally.get('Story', fetch="FormattedID,Name,Description,State,DragAndDropRank", 
                                  order="Rank ASC", limit=100)
    stories = [story for story in response]
    top_story    = stories[0]
    bottom_story = stories[-1]
    assert bottom_story.FormattedID == target_story.FormattedID


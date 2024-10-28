#!/usr/bin/env python
#################################################################################################
#
# getwork.py -- Get All work items from top Portfolio Item Type down to Stories/Defects
#               Example:
#                   Theme
#                   Initiative
#                   Feature
#                   Story
#                   Defect
#
#################################################################################################

import sys, os

from pyral import Rally, rallyWorkset

#################################################################################################

LEVEL_NAME = \
    {
     1: 'Theme',
     2: 'Initiative',
     3: 'Feature',
     4: 'Story',
     5: 'Defect',
    }

#################################################################################################

def main(args):
    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    print(" ".join(["|%s|" % item for item in [server, username, '*******',  workspace, project]]))
    if apikey:
        rally = Rally(server, apikey=apikey, workspace=workspace, project=project, isolated_workspace=True)
    else:
        rally = Rally(server, user=username, password=password, workspace=workspace, project=project, isolated_workspace=True)

    #firstSwag(rally)
    #swagTwo(rally)
    locus_project         = args.pop(0) if args else 'ValueOps ConnectALL'
    start_of_interest_day = args.pop(0) if args else '2024-04-01'
    charmThree(rally, locus_project, start_of_interest_day)

#################################################################################################

def firstSwag(rally):
    timeblock = "CreationDate >= 2024-04-01T00:00:00Z"
    result = rally.get('Theme', fetch='FormattedID,Name,Project,State,Children,CreationDate,LastUpdateDate',
                                       query=timeblock,
                                       projectScopeDown=True,
                                       order='CreationDate ASC')

    counter = {}
    for level in [1,2,3,4,5]:
        level_name = LEVEL_NAME[level]
        counter[level_name] = 0
    print(f'Theme items: {result.resultCount}')
    themes = [item for item in result]
    showItems('Theme', themes, level=1, counter=counter)

    print(repr(counter))

#################################################################################################

def swagTwo(rally):
    timeblock = "LastUpdateDate >= 2024-04-01T00:00:00Z"
    fields = 'FormattedID,Name,Project,State,ScheduleState,Children,CreationDate,LastUpdateDate,Parent'

    result = rally.get('Story', fetch=fields, query=timeblock,
                       projectScopeDown=True,
                       order='CreationDate ASC')
    for story in result:
        if not story.Parent:
            #print(story.attributes())
            #print(story.details())
            state = story.ScheduleState if story.ScheduleState else '<NULL>'
            print(f'{story.FormattedID} [{story.Project.Name}] {story.Name}   {state}  has no Parent')
            continue
        if story.Parent.Project.Name != story.Project.Name:
            parent = story.Parent
            story_state = 'UNKNOWN'
            if story.ScheduleState:
                try:
                    story_state = story.ScheduleState.Name
                except AttributeError:
                    try:
                        story_state = story.ScheduleState
                    except AttributeError:
                        story_state = '<BAD>'
            blurb = f'{parent.FormattedID} [{parent.Project.Name}]   {story.FormattedID} [{story.Project.Name}]  {story.Name}   {story_state}'
            print(blurb)

#################################################################################################

def charmThree(rally, locus_project, first_day_of_interest):
    proj_tree_members = set()
    #response = rally.get('Project', fetch="Name,ObjectID,Children,State", query=f'Name = "{locus_project}"')
    #proj = response.next()
    #for cp in proj.Children:
    #    print(f'   {cp.Name}')
    ftr_bank = {}
    interest_date = f'{first_day_of_interest}T00:00:00Z'
    criteria = [f'LastUpdateDate >= "{interest_date}"']
    fields = 'FormattedID,Name,Project,ScheduleState,CreationDate,LastUpdateDate,Parent,Feature'
    result = rally.get('Story', fetch=fields, query=criteria,
                       project=locus_project,
                       projectScopeDown=True,
                       order='CreationDate ASC')

    proj_tree_stories = 0
    featureless_stories = 0
    #print(f'qualifying Story items: {result.resultCount}')
    for story in result:
        parent  = None
        feature = None
        try:
            parent = story.Parent
        except AttributeError:
            pass
        try:
            feature = story.Feature
        except AttributeError:
            pass
        if not parent and not feature:
            ##print(f'{story.FormattedID} [{story.Project.Name}] {story.Name}  has no Parent/Feature')
            featureless_stories += 1
            continue
        parent = feature if feature else parent
        proj_tree_stories += 1
        proj_tree_members.add(story.Project.Name)
        parent_fid = parent.FormattedID
        ftr_bank[parent_fid] = parent

    print(f'Stories in project sub-tree not having a Feature: {featureless_stories}')
    print(f'{locus_project} project sub-tree qualifying Story items: {proj_tree_stories}')
    print(f'ftr_bank has {len(ftr_bank)} Features')
    clean_features = []
    muddy_features = {}
    for ffid in ftr_bank.keys():
        #print(ffid)
        ftr = ftr_bank[ffid]
        stories = [story for story in ftr.UserStories]
        proj_tree_stories = [story for story in stories if story.Project.Name     in proj_tree_members]
        if len(proj_tree_stories) == ftr.DirectChildrenCount:
            clean_features.append(ffid)
        alien_stories  = [story for story in stories if story.Project.Name not in proj_tree_members]
        if alien_stories:
            muddy_features[ffid] = []
            for story in alien_stories:  # mfaps - muddy feature alien project story
                mfaps = f'{story.FormattedID}   [{story.Project.Name}]   {story.Name}'
                muddy_features[ffid].append(mfaps)
                #print(f'    {mfaps}')

    print(f'Clean Features - Features whose UserStories have projects within the \'{locus_project}\' project sub-tree')
    for ffid in clean_features:
        print(f'{ffid}')
    print("")

    print(f'Muddy Features - Features that have UserStories in projects outside the \'{locus_project}\' project sub-tree')
    for ffid, m_stories in muddy_features.items():
        print(f'{ffid}')
        for m_story in m_stories:
            print(f'    {m_story}')

    print('DONE')

#################################################################################################

def showItems(item_type, items, level=1, counter={}):
    indent = '' if level == 1 else ' ' * (4 * level-1)
    for item in items:
        try:
            state = item.State.Name
        except AttributeError:
            try:
                state = item.ScheduleState.Name
            except AttributeError:
                #print(f'{item.FormattedID}  [{item.Project.Name}] has no State attribute')
                state = '<NO STATE>'
        nit = f'{item.FormattedID}   [{item.Project.Name}]  {state:10.10}   {item.Name}'
        try:
            num_children = len(item.Children)
        except AttributeError:
            num_children = 0
        print(f'{indent}{nit}    {num_children} sub-items' )
        counter[LEVEL_NAME[level]] += 1
        if not num_children:
            continue
        next_level = level + 1
        showItems(LEVEL_NAME[next_level], item.Children, level=next_level, counter=counter)

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

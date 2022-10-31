#!/usr/bin/env python3

#################################################################################################
#
# release_start_items.py -- demonstration script to obtain the Features, Stories
# #                         with their assignment and ScheduleState value
##                          for those items in a specific project
# #                         right at the beginning of the Release identified
# #                         in the second argument.
#
USAGE = """
Usage: release_start_items.py <project name> <release name>
"""
#################################################################################################

import sys, os
import time
import json
from pprint import pprint

from pyral import Rally, rallyWorkset

import requests

#################################################################################################

global rally   # Living with this ugly wart temporarily...
rally = None

errout = sys.stderr.write

RALLY_LBAPI_BASE = "https://rally1.rallydev.com/analytics/v2.0/service/rally"
#LOOKBACK_API_URL = f"{RALLY_LBAPI_BASE}/workspace/{workspace_oid}/artifact/snapshot/query.js"

TARGET_ROOT_PROJECT = "Rally Engineering"

#################################################################################################

def main(args):

    global rally

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    project, target_release_name = args[0:2]
    #print(" ".join(["|%s|" % item for item in [server, username, password, workspace, project]]))
    if apikey:
        rally = Rally(server, username, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, username, password, workspace=workspace, project=project)

    today = time.strftime("%Y-%m-%d", time.localtime(time.time()))

    wksp = rally.getWorkspace()
    proj = rally.getProject(project)
    TARGET_ROOT_PROJECT = "Rally Engineering"
    root_proj = rally.getProject(TARGET_ROOT_PROJECT)
    root_proj_oid = root_proj.oid

    print(wksp.oid, wksp.Name)
    print(proj.oid, proj.Name)
    print("=" * 60)

    response = rally.get('Release',
                         fetch="ObjectID,Name,Project,ReleaseStartDate,ReleaseDate,State",
                         query=[f'Name = "{target_release_name}"'],
                         #order="StartDate ASC, Name",
                         order="Name,StartDate",
                         workspace=workspace,
                         project=TARGET_ROOT_PROJECT,
                         projectScopeUp=False,
                         projectScopeDown=True,
                         pagesize=100, limit=500)

    release_items = [item for item in response]
    project_names = [rls.Project.Name for rls in release_items]
    sorted_project_names = sorted(project_names)
    MAX_PROJECTS = 3

    # Get info from Rally on the Features associated with each project in sorted_project_names
    # we need to build a lookup (dict) keyed by Feature ObjectID with the associated Feature instance
    feature_info = {}
    for project_name in sorted_project_names:
        response = rally.get('Feature', fetch="ObjectID,FormattedID,Name,Project,Release,State",
                             query = [f'Release.Name = "{target_release_name}"'],
                             workspace=workspace,
                             project=project_name,
                             projectScopeUp=False,
                             projectScopeDown=True,
                             pagesize = 1000, limit = 1000
                            )
        for ftr in response:
            feature_info[ftr.ObjectID] = ftr
    # Features associated with the Release for {target_release_name}
    #for oid, ftr in feature_info.items():
    #    print(f'{ftr.FormattedID}  {oid} {ftr.Name:<44.44} {ftr.Project.Name}')

    plan = {}  # to be keyed by 'inception', 'current' and 'variance'
    plan['inception'] = {}
    ix = 0
    for project_name in sorted_project_names:
        ix += 1
        hits = [rls for rls in release_items if rls.Project.Name == project_name]
        if not hits:
            print(f"Unable to find a Release item for Project.Name of {project_name}")
            sys.exit(1)
        rls_item = hits[0]
        rls_ident, project = rls_item.oid, rls_item.Project
        print("")
        print(f" {project.Name:<36.36}  {rls_item.Name}   {rls_item.ReleaseStartDate}   {rls_item.State}    Release OID: {rls_ident}")
        elements = captureFeaturesAndStoriesAtStartOfIncrement(wksp, project, rls_item, feature_info, apikey)
        plan['inception'][project_name] = elements
        if ix >= MAX_PROJECTS:
            break

    print(f"\nCurrent state of the PI plan for the {target_release_name} Release\n")

    plan['current'] = {}
    ix = 0
    for project_name in sorted_project_names:
        ix += 1
        hits = [rls for rls in release_items if rls.Project.Name == project_name]
        rls_item = hits[0]
        rls_ident, project = rls_item.oid, rls_item.Project
        print(f" {project.Name:<36.36}  {rls_item.Name}   {rls_item.ReleaseDate}")
        elements = captureFeaturesAndStoriesForCurrentDate(wksp, project, rls_item, feature_info, rally)
        plan['current'][project_name] = elements
        if ix >= MAX_PROJECTS:
            break

    print(f"\nVariances to the PI plan for the {target_release_name} Release\n")
    plan['variance'] = {}
    ix = 0
    for project_name in sorted_project_names:
        ix += 1
        print(project_name)
        elements = identifyFeaturesAndStoriesVariances(project_name, plan['inception'], plan['current'])
        plan['variance'][project_name] = elements
        for key, element in plan['variance'][project_name].items():
            if element:
                print(key)
                pprint(element)
                print()
        if ix >= MAX_PROJECTS:
            break

#################################################################################################

def captureFeaturesAndStoriesAtStartOfIncrement(wksp, project, rls_item, feature_info, apikey):

    global rally   # probably make this a passed parameter at some point
    rls_name  = rls_item.Name
    rls_ident = rls_item.oid

    art_type = "PortfolioItem/Feature"
    # wksp is a pyral.entity.Workspace instance for the workspace identified by the command line arg
    proj_features = getLookbackInfoFor(wksp, project, rls_ident, art_type, apikey)

    rls_tagged_features = [ftr for ftr in proj_features if 'Release' in list(ftr.keys())]
    release_features    = [ftr for ftr in rls_tagged_features
                                       if ftr.Release.Name == rls_name]

    ftr_stories = {}   # we'll be returning this as the function result
    for ftr in release_features:
        indent = " " * 4
        # Project, Name, Owner, Iteration, CreationDate, Release, State
        try:
            ftr_state = ftr.State
        except (KeyError,ValueError) as exc:
            ftr_state = 'NO STATE PRESENT'
        #print(f"{indent}{ftr.FormattedID} {ftr.Name:<48.48}  {ftr.Release.Name}  [{ftr_state:<12}]        Project OID: {ftr.Project} ")
        ftr_stories[ftr.FormattedID] = {'Feature' : ftr}

    art_type = "HierarchicalRequirement"
    proj_stories = getLookbackInfoFor(wksp, project, rls_ident, art_type, apikey)
    rls_tagged_stories = [story for story in proj_stories if 'Release' in list(story.keys())]
    release_stories    = [story for story in rls_tagged_stories
                                 if story.Release.Name == rls_name]

    indent4 = ' ' * 4
    feature_covered_stories = []
    for ftr in release_features:
        try:
            ftr_state = ftr.State
        except (KeyError,ValueError) as exc:
            ftr_state = '    '
        print(f"{indent4}{ftr.FormattedID} {ftr.Name:<48.48}  {ftr.Release.Name}  [{ftr_state}]")
        assoc_stories = [story for story in release_stories
                                if 'Feature' in story
                                and story.Feature
                                and story.Feature == ftr.ObjectID]
        indent8 = ' ' * 8
        for story in assoc_stories:
            print(f"{indent8}{story.FormattedID} {story.Name:<48.48}  {story.Release.Name}  [{story.ScheduleState}]")
            ftr_stories[ftr.FormattedID][story.FormattedID] = story
        feature_covered_stories.extend(assoc_stories)

    # ffep_stories  # feature from external project stories
    ffep_stories = [story for story in release_stories
                           if 'Feature' in story
                          and story.Feature
                          and story not in feature_covered_stories]
    if ffep_stories:
        print(f"    Stories associated with a Feature defined in another project ")
        for story in ffep_stories:
            ftr, ftr_fid = None, None
            try:
                ftr = feature_info[story.Feature]
                ftr_fid = ftr.FormattedID
                ftr_project_name = ftr.Project.Name
            except:
                try:
                    ftr = rally.get('Feature', fetch="ObjectID,FormattedID,Name,Project,State",
                                     query=[f'ObjectID = {story.Feature}'],
                                     workspace=wksp.Name, project=None, instance=True)
                    ftr_fid = ftr.FormattedID
                    ftr_project_name = ftr.Project.Name
                except:
                    ftr_fid = 'UNAVBL'
            if ftr_fid not in ftr_stories:
                ftr_stories[ftr_fid] = {'Feature': ftr}   # and it is true that maybe ftr will be None...
            ftr_stories[ftr_fid][story.FormattedID] = story
            print(f"{indent4}|{ftr_fid}|  {story.FormattedID} {story.Name:<48.48}  {story.Release.Name}  [{story.ScheduleState:<12}]   {ftr_project_name}")

    # noaf_stories  # no associated feature stories
    noaf_stories = [story for story in release_stories if 'Feature' not in (story)]
    if noaf_stories:
        print(f"    There are {len(noaf_stories)} Stories that are no associated with a Feature")
        for story in noaf_stories:
            if 'NONE' not in ftr_stories:
                ftr_stories['NONE'] = {'Feature' : None}
            ftr_stories['NONE'][story.FormattedID] = story
            print(f"{indent8}{story.FormattedID} {story.Name:<48.48}  {story.Release.Name}  [{story.ScheduleState}]")

    return ftr_stories

#################################################################################################

def captureFeaturesAndStoriesForCurrentDate(wksp, project, rls_item, feature_info, rally):
    """
        wksp    is a pyral.entity.Workspace instance
        project is a pyral.entity.Project   instance
        rls_item is a ?
        feature_info is a dict
        rally is a "connected' pyral.Rally instance

        Use the rally parameter to make WSAPI queries to find the Features and Stories
        associated with the project that are associated with the Release identified by the rls_item.
        The return value is a dict  keyed at the top level by a Feature FormattedID or 'NONE"
        whose associated values are in turn a dict that always has an entry for the
        Feature.FormattedID (or 'NONE') associate with a Feature instance
        and additional entries of Story.FormattedID : Story instance pairs.
    """
    # feature_info is dict keyed by a Feature.ObjectID (aka oid) with an associated Feature instance
    # for each Feature

    ftr_stories = {}

    # query for Stories associated with the given project and rls_item.Name
    criteria = [
                f'Release.Name = "{rls_item.Name}"',
                'CreationDate >= 2022-07-01'
               ]
    response = rally.get('HierarchicalRequirement',
                         fetch="ObjectID,FormattedID,Name,Project,Release,Feature,ScheduleState,State",
                         query=criteria,
                         workspace=wksp.Name,
                         project=project.Name,
                         projectScopeUp=False,
                         projectScopeDown=False,
                        )
    for story in response:
        if story.Feature:
            ftr_fid = story.Feature.FormattedID
            if ftr_fid not in ftr_stories:
                ftr_stories[ftr_fid] = {'Feature' : story.Feature}
        else:
            ftr_fid = 'NONE'
            if ftr_fid not in ftr_stories:
                ftr_stories[ftr_fid] = {'Feature' : None}
        ftr_stories[ftr_fid][story.FormattedID] = story

    real_features = [ftr for ftr in ftr_stories.keys() if ftr != 'NONE']
    indent4 = " " * 4
    indent8 = " " * 8
    for feature_fid in ftr_stories:
        feature = ftr_stories[feature_fid]['Feature']
        if feature:
            # guard again a feature.Release not being assigned...
            ftr_release_name = 'MISSING'
            try:
                ftr_release_name = feature.Release.Name
            except:
                pass
            print(f"{indent4}{feature_fid}   {feature.Name:<23.23}  {ftr_release_name}")
        else:
            print(f"{indent4}UNAVBL    Stories not associated with a Feature")
        stories = [key for key in ftr_stories[feature_fid].keys() if key != 'Feature']
        for story_fid in stories:
            story = ftr_stories[feature_fid][story_fid]
            print(f"{indent8}{story_fid}  {story.Name:<48.48}  {story.Release.Name}    {story.ScheduleState}")

    none_features = [ftr for ftr in ftr_stories.keys() if ftr == 'NONE']

    return ftr_stories

#################################################################################################

def identifyFeaturesAndStoriesVariances(project_name, inception, current):
    """
        Both start_status and current_status have the same structure, ie.
        the same as the ftr_stories dicts in the capture*X methods above

        We want to find the Features that were dropped, added or reassigned between projects
                   and the Features that are not in the 'end' State
        For each Feature we want to find the Stories that were dropped, added or reassigned between
               projects and find the Stories that are not in the 'end' ScheduledState

        To find the Features that were dropped, for each Feature present in the plan["inception"]
        if the same Feature is NOT present in the plan["current"] then that Feature is classified
        as dropped.
        To find the Features that were added, for each Feature present in the plan["current"]
        if the same Feature is NOT present in the plan['inception'] then that Feature is classified
        as added.
        For any Feature that is both inception and current if the Feature in th current
        has a State value that is not the end value (Released) then that is a variance from the plan.
    """
    ftr_stories = {}
    for ftr_key, slot_tank in current[project_name].items():
        ftr_name = ''
        if ftr_key != 'NONE':
            feature = slot_tank['Feature']
            ftr_name = feature.Name
        print(f"    {ftr_key}  {ftr_name}")
        stories_for_feature = [(story_id, story) for story_id, story in slot_tank.items()
                                                  if story_id not in ['NONE', 'Feature']]
        indent8 = " " * 8
        for sd in stories_for_feature:
            story_id, story = sd
            print(f"{indent8}{story_id}  {story.Name:<48.48}    {story.ScheduleState}")
    print()

    variance = {'Feature Drops'  : [],
                'Feature Adds'   : [],
                'Feature Status' : [],   # to be keyed by Feature FormattedID
                'Feature Stories' : {}
               }

    inception_features = set(list(inception[project_name].keys()))
    current_features   = set(list(current[project_name].keys()))

    feature_drops_fids = inception_features - current_features
    feature_drops = [(ftr_fid,
                      inception[project_name][ftr_fid]['Feature'].Name,
                      inception[project_name][ftr_fid]['Feature'].State.Name)
                    for ftr_fid in feature_drops_fids]

    feature_adds_fids  = current_features - inception_features
    feature_adds = [(ftr_fid,
                     inception[project_name][ftr_fid]['Feature'].Name,
                     inception[project_name][ftr_fid]['Feature'].State.Name)
                    for ftr_fid in feature_adds_fids]

    common_features = inception_features.intersection(current_features)

    variance['Feature Drops'] = feature_drops
    variance['Feature Adds']  = feature_adds
    for ftr_fid in common_features:
        inc_ftr = inception[project_name][ftr_fid]['Feature']
        cur_ftr =   current[project_name][ftr_fid]['Feature']
        if cur_ftr.State != 'Released':
                variance['Feature Status'].append((ftr_fid, cur_ftr.Name, cur_ftr.State.Name))
        inc_story_fids = [story_fid for story_fid in inception[project_name][ftr_fid].keys()
                                     if story_fid != 'Feature']
        cur_story_fids = [story_fid for story_fid in current[project_name][ftr_fid].keys()
                                     if story_fid != 'Feature']
        ftr_stories_dropped_fids = set(inc_story_fids) - set(cur_story_fids)
        ftr_stories_added_fids   = set(cur_story_fids) - set(inc_story_fids)
        ftr_stories_dropped = [(fid,
                                inception[project_name][ftr_fid][fid].Name,
                                inception[project_name][ftr_fid][fid].ScheduleState
                               )
                               for fid in ftr_stories_dropped_fids]
        ftr_stories_added   = [(fid,
                                current[project_name][ftr_fid][fid].Name,
                                current[project_name][ftr_fid][fid].ScheduleState
                               )
                               for fid in ftr_stories_added_fids]
        variance[f"{ftr_fid} Story Drops"] = ftr_stories_dropped
        variance[f"{ftr_fid} Story Adds"]  = ftr_stories_added
        ftr_stories_not_released = []
        common_ftr_stories = set(inc_story_fids) & set(cur_story_fids)
        for story_fid in common_ftr_stories:
            inc_ftr_story = inception[project_name][ftr_fid][story_fid]
            cur_ftr_story =   current[project_name][ftr_fid][story_fid]
            cur_story_state = cur_ftr_story.ScheduleState
            if cur_story_state != 'Released':
                ftr_stories_not_released.append((story_fid, cur_ftr_story.Name, cur_story_state))
        variance[f"{ftr_fid} Stories Not Released"]  = ftr_stories_not_released[:]

    return variance

#################################################################################################

def getLookbackInfoFor(workspace, project, rls_ident, artifact_type,  apikey):
    post_data = {"find": {"_ProjectHierarchy": project.oid,
                          "_TypeHierarchy": artifact_type,
                          "Release": rls_ident,
                          "__At": "2022-08-15T00Z"
                         },
                 "fields": ["ObjectID", "FormattedID", "Project", "PortfolioItem", "Feature", "Name",
                            "Release", "Iteration", "ScheduleState", "State", "CreationDate", "Owner"],
                 "hydrate": ["Release", "Iteration", "ScheduleState", "State"],
                 # "hydrate" : ["Release", "Iteration", "ScheduleState", "Feature"],
                 "start": 0,
                 "pagesize": 1000,
                 "removeUnauthorizedSnapshots": True
                }

    endpoint = f"workspace/{workspace.oid}/artifact/snapshot/query.js"
    lb_post_url = f"{RALLY_LBAPI_BASE}/{endpoint}"

    # since we are using the POST method, we leave this query_string and lb_url assignment here
    # as vestiges of initial development
    #query_string = "{%22_ProjectHierarchy%22:51763678032,%22_TypeHierarchy%22:%22HierarchicalRequirement%22,%22__At%22:%222022-08-15T00Z%22}&fields=[%22ObjectID%22,%22FormattedID%22,%22Project%22,%20%22PortfolioItem%22,%22Feature%22,%20%22Name%22,%20%22Owner%22,%20%22Release%22,%20%22Iteration%22,%20%22ScheduleState%22,%20%22CreationDate%22]&hydrate=[%22Release%22,%20%22Iteration%22,%20%22ScheduleState%22]&start=0&pagesize=1000&removeUnauthorizedSnapshots=true"
    #query_string = "{%22_ProjectHierarchy%22:51763678032,%22_TypeHierarchy%22:%22PortfolioItem/Feature%22,%22__At%22:%222022-08-15T00Z%22}&fields=[%22ObjectID%22,%22FormattedID%22,%22Project%22,%20%22PortfolioItem%22,%22Feature%22,%20%22Name%22,%20%22Owner%22,%20%22Release%22,%20%22Iteration%22,%20%22ScheduleState%22,%20%22CreationDate%22]&hydrate=[%22Release%22,%20%22Iteration%22,%20%22ScheduleState%22]&start=0&pagesize=1000&removeUnauthorizedSnapshots=true"
    #lb_url = f"{RALLY_LBAPI_BASE}/{endpoint}?find={query_string}"
    # response = requests.get(lb_url, headers={'ZSESSIONID' : apikey})

    access_header ={'ZSESSIONID' : apikey}

    response = requests.post(lb_post_url, data=json.dumps(post_data), headers=access_header)
    #print(response.status_code)
    #print("")
    lbd = json.loads(response.text)
    results = [AttributeDict(**result) for result in lbd['Results']]
    return results

#################################################################################################

class AttributeDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        # if the value for an attribute is itself a dict,
        # then turn that into a AttributeDict instance
        # we only do this at the first level
        for attr in self.keys():
            if isinstance(self[attr], dict):
                self[attr] = AttributeDict(**self[attr])

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        self[name] = value

#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

#!/usr/bin/env python3

#################################################################################################
#
# currls.py -- demonstration script to obtain the current Release
#               for a particular project
#
#################################################################################################

import sys, os
import time

from pyral import Rally, rallyWorkset

#################################################################################################

errout = sys.stderr.write

#################################################################################################

def main(args):

    options = [opt for opt in args if opt.startswith('--')]
    args    = [arg for arg in args if arg not in options]
    server, username, password, apikey, workspace, project = rallyWorkset(options)
    #print(" ".join(["|%s|" % item for item in [server, username, password, workspace, project]]))
    if apikey:
        rally = Rally(server, username, apikey=apikey, workspace=workspace, project=project)
    else:
        rally = Rally(server, username, password, workspace=workspace, project=project)

    today = time.strftime("%Y-%m-%d", time.localtime(time.time()))

    target_release_name = 'FY22-Q4'

    response = rally.get('Feature',
                         workspace=workspace,
                         fetch="Name,FormattedID,Project,Release,Iteration,State,PlanEstimate",
                         #query=[f"CreationDate >= 2022-08-15", "Release.StartDate <= 2022-11-07"],
                         query=[f'Release.Name = "{target_release_name}"'],
                         order="Project.Name",
                         projectScopeUp=False,
                         projectScopeDown=True,
                         pagesize=200, limit=1000)
    pi_features = [item for item in response]
    pi_features = sorted(pi_features, key=lambda x: (x.Project.Name, x.FormattedID))

    response = rally.get('Release',
                         workspace=workspace,
                         fetch="Name,Project,ReleaseStartDate,ReleaseDate,State,PlanEstimate,WorkProducts",
                         #query=[f"ReleaseStartDate <= {today}", f"ReleaseDate >= {today}"],
                         query=[f'Name = "{target_release_name}"'],
                         order="StartDate ASC",
                         projectScopeUp=False, 
                         projectScopeDown=True,
                         pagesize=100, limit=500)

    if response.errors:
        errout("Request could not be successfully serviced, error code: %d\n" % response.status_code)
        errout("\n".join(response.errors))
        sys.exit(1)

    rls_items = [rls for rls in response]
    alphabetic_team_list = sorted(rls_items, key=lambda x: x.Project.Name)

    for ix, release in enumerate(alphabetic_team_list):
        showTeamArtifacts(target_release_name, release, pi_features)
        print("")

#################################################################################################

def showTeamArtifacts(target_release_name, release, pi_features):
    proj_name = release.Project.Name
    rlsStart = release.ReleaseStartDate.split('T')[0]
    rlsEnd   = release.ReleaseDate.split('T')[0]
    print(f"{proj_name:<36.36}  {release.Name:<24} {rlsStart}  {rlsEnd}  {release.State}")
    proj_features = [ftr for ftr in pi_features if ftr.Project.Name == proj_name]

    work_products = [wp for wp in release.WorkProducts if wp._type not in ['TestSet', 'TestCase']]
    stories = [art for art in work_products if art._type == 'HierarchicalRequirement']
    defects = [art for art in work_products if art._type == 'Defect']
    tasks   = [art for art in work_products if art._type == 'Task']
    pifs    = [art for art in work_products if 'feature' in art._type.lower()]
    others  = [art for art in work_products if art._type not in ['HierarchicalRequirement', 'Defect', 'Task', 'TestSet', 'TestCase']]
    # release.WorkProducts may not actually hold all the Features involved
    # and that is why there was a separate query in to get the full set of Features

    ftr_stories = slotStoriesToFeatures(stories, target_release_name)
    gross_story_count = sum(len(ftr_stories[key]) for key in ftr_stories)

    # now account for situation where a team may have worked on a Feature that was defined
    # for another team (this may or may not be a great practice, but it does happen.
    #
    bona_fide_features = list(ftr_stories.keys())
    bona_fide_features.remove('UN_TETHERED')
    bona_fide_features = sorted(bona_fide_features)

    feature_fids = {f.FormattedID for f in proj_features}
    missing_fids = set(bona_fide_features) - feature_fids
    if missing_fids:
        for miss_fid in missing_fids:
            hits = [ftr for ftr in pi_features if ftr.FormattedID == miss_fid]
            if hits:
                pif = hits[0]
                proj_features.append(pif)
                #print(f'    adding Feature {pif.FormattedID} from Project {pif.Project.Name} to the list of Features relevant to the Stories in this Project')

    print(f"    Features: {len(bona_fide_features)}    Stories: {gross_story_count}")
    indent = " " * 8

    #untethered_stories = [story for story in stories
    #                             if story.Feature
    #                            and not hasattr(story.Feature, 'FormattedID')]

    for feature_fid in bona_fide_features:
        hits = [ftr for ftr in proj_features if ftr.FormattedID == feature_fid]
        if not hits:
            # this can happen when a Feature is referenced whose Release value
            # might be different than the target_release value
            #print(f"    Unable to find a Feature with FormattedID value of {feature_fid}")
            continue
        proj_pif = hits[0]
        state = ""   # Some PortfolioItem/Feature items don't have a State value set...
        if hasattr(proj_pif.State, 'Name'):
            state = proj_pif.State.Name
        if state == 'PI Committed Backlog':
            state = 'Backlog'
        print(f"    {proj_pif.FormattedID}   {state:>8}  {proj_pif.Name}")
        feature_stories = [story for story in stories
                                  if story.Feature
                                 and hasattr(story.Feature, 'FormattedID')
                                 and story.Feature.FormattedID == proj_pif.FormattedID]
        #print(f"{indent}    {len(feature_stories)} Stories associated with this Feature (per release.WorkProducts)")

        showTeamFeatureStories(feature_stories, target_release_name)

        indent = " " * 8
        if ftr_stories['UN_TETHERED']:
            print("     Stories not associated with a Feature")
            for story_fid, story in ftr_stories['UN_TETHERED'].items():
                estimate = getEstimate(story)
                state    = getScheduleStateOrState(story)
                print(f"{indent}{story.FormattedID}  {estimate}  {state:>12}  {story.Name}")

        """
        if defects:
            print(f"\n    Defects ({len(defects)}) addressed in this Release timeframe")
            for defect in defects:
                estimate = getEstimate(defect)
                state = getScheduleStateOrState(defect)
                print(f"{indent}{defect.FormattedID}  {estimate}  {state:>12}  {defect.Name}")
        """

#################################################################################################

def showTeamFeatureStories(feature_stories, target_release_name):
    indent = " " * 8
    for story in feature_stories:
        sfid = story.FormattedID
        srls_name = 'UNKNOWN!'
        if hasattr(story, 'Release') and story.Release and hasattr(story.Release, 'Name') and story.Release.Name:
            srls_name = story.Release.Name
        else:
            print(f'Unable to suss out the Release for Story: {story.FormattedID}')
        sfrls_name = 'BONKO!'
        if not story.Feature:
        #    print(f"     {story.FormattedID}   is not associated with a Feature...")
            continue
        if story.Feature and hasattr(story.Feature, 'Release') and not story.Feature.Release:
            print(f"     {story.FormattedID} Release: {srls_name}  Feature {story.Feature.FormattedID} not associated with a Release")
            continue
        if story.Feature and story.Feature.Release and story.Feature.Release.Name:
            sfrls_name = story.Feature.Release.Name
            if sfrls_name != target_release_name:
                continue
        #print(f"{indent}{story.FormattedID} Release: {srls_name}  Feature: {story.Feature.FormattedID} Release: {sfrls_name}")
        estimate = getEstimate(story)
        state    = getScheduleStateOrState(story)
        print(f"{indent}{story.FormattedID}  {estimate}  {state:>12}  {story.Name}")

#################################################################################################

def slotStoriesToFeatures(stories, target_release_name):
    """
        stories are the subset of the WorkProducts associated with the
        release whose artifact type is 'HierarchicalRequirement'.
        This function creates a dict keyed by a Feature Formatted id
        whose value is a sub-dict keyed by a Story FormattedID whose
        associated value is a pyral.Story instance.
        If a Story doesn't have an associated Feature, then it is
        tagged as an untethered Story.
    """
    ftr_stories = {'UN_TETHERED' : {}}
    for story in stories:
        if not story.Feature:
            ftr_stories['UN_TETHERED'][story.FormattedID] = story
            continue
        feature = None
        if story.Feature and hasattr(story.Feature, 'FormattedID') and story.Feature.FormattedID \
                and hasattr(story.Feature, 'Name'):
            feature = story.Feature.FormattedID
            if feature not in ftr_stories:
                ftr_stories[feature] = {}
        if story.Feature and not story.Feature.Release:
            continue
        if story.Feature and story.Feature.Release and story.Feature.Release.Name != target_release_name:
            continue
        if not feature:
            continue
        ftr_stories[feature][story.FormattedID] = story
    return ftr_stories

#################################################################################################

def getEstimate(artifact):
    estimate = " "
    if hasattr(artifact, "PlanEstimate"):
        estimate = artifact.PlanEstimate
        try:
            estimate = int(estimate)
        except TypeError:
            estimate = " "
    return estimate

#################################################################################################

def getScheduleStateOrState(artifact):
    state = "N/A"
    if hasattr(artifact, 'ScheduleState'):
        state = artifact.ScheduleState
    elif hasattr(artifact, 'State'):
        state = artifact.State
    if state == "PI Committed Backlog":
        state = "Backlog"
    return state

#################################################################################################
#################################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])

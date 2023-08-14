#!/usr/bin/env python

import sys, os
import types
import pprint
import time

from pyral import Rally

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD #, APIKEY
from rally_targets import RALLY_NICKNAME, DEFAULT_WORKSPACE

#APIKEY = "_leL4WkuWRNGNAgfhN3qFkTzgSpKlIkKsi21JDkg82k"  # for nick@denver.com

APIKEY = "_dgu5WvHTwSrsvhNIchf98oxfHRgkkG7oxfZRwqdOqU"   # for nick@denver.com
NICK_WKSP = 'NMTest'
WACKY_PROJ = '*MFA Benefit Durt'

##################################################################################################

def test_getSchemaInfo():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance and call the getSchemaInfo method for the
        default workspace.
    """
    rally = Rally(server=RALLY, apikey=APIKEY, workspace=NICK_WKSP, project=WACKY_PROJ)
    schema_info = rally.getSchemaInfo(rally.getWorkspace())
    assert type(schema_info) == list
    assert len(schema_info) > 50
    subs_schema = [item for item in schema_info if item['Name'] == 'Subscription']
    assert subs_schema != None
    assert len(subs_schema) == 1
    assert type(subs_schema) == list
    assert u'Attributes' in subs_schema[0]
    assert len(subs_schema[0][u'Attributes']) > 15

    epic_schema = [item for item in schema_info if item['Name'] == 'Epic']
    assert epic_schema != None


def test_typedef():
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.typedef convenience method using 'Portfolio/Epic'
        as a target.
    """
    rally = Rally(server=RALLY, apikey=APIKEY, workspace=NICK_WKSP, project=WACKY_PROJ)
    target_type = 'PortfolioItem/Epic'
    td = rally.typedef(target_type)
    assert td != None
    assert td._type == 'TypeDefinition'
    assert td.TypePath == 'PortfolioItem/Epic'
    assert td.ref.startswith('typedefinition/')

def test_epic_creation():
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.create method to create an Epic instance and be handed
        back a usable pyral.entity representing the newly created Epic PortfoloItem instance.
    """
    rally = Rally(server=RALLY, apikey=APIKEY, workspace=NICK_WKSP, project=WACKY_PROJ)
    target_workspace = rally.getWorkspace()

    wksp_projs = rally.getProjects(workspace='NMTest')
    print(wksp_projs)
    assert len(wksp_projs) > 0
    for proj in wksp_projs:
        print(proj.Name)

    rally.setProject('*MFA Benefit Durt')
    target_project = rally.getProject()
##
    #response = rally.get('Feature', fetch=True, workspace=target_workspace.Name, project=None, instance=True)
    #if response.resultCount == 0:
    #    raise Exception("Unable to retrieve any Feature items...  so sad")
    #features = [f for f in response]
    #feature = [f for f in features if f.FormattedID == 'F1']
##

    feature = rally.get('Feature', fetch=True, query='FormattedID = F1', 
                        workspace=target_workspace.Name, project=None, 
                        instance=True)
##  print(feature.details())
    info = {
             "Workspace"   : target_workspace._ref,
             "Project"     : target_project._ref,
             "Name"        : "VacuumHajCracklings",
             "Description" : "420 CuHectare capacity.  It is a big place and partygoers are sloppy.  Big fast clean mandatory.",
             #"Notes"       : "Hoover or Dustmatic it makes no difference",
             #"Ready"       : False,
             "Parent"      : feature._ref
           }

    print("Creating Epic ...")
    epic = rally.put('Epic', info)
    assert epic
    assert epic.Name == 'VacuumHajCracklings'
    #print("Created  Epic: %s   OID: %s  Name: %s   Description: %s" % \
    #        (epic.FormattedID, epic.oid, epic.Name, epic.Description))
    assert epic.Ready == False

    print("Epic's Parent.Name  value: {0}".format(epic.Parent.Name))
    print("Epic's Parent.Project.Name  value: {0}".format(epic.Parent.Project.Name))
    print("Epic's Parent.DisplayColor value: {0}".format(epic.Parent.DisplayColor))
    print("Epic's Parent.InvestmentCategory value: {0}".format(epic.Parent.InvestmentCategory))


def test_epic_query_by_formatted_id():            
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.get  method to retrieve and Epic instance that has been created offline
        and be handed back a usable pyral.entity representing the PortfoloItem/Epic instance.
    """
    rally = Rally(server=RALLY, apikey=APIKEY, workspace=NICK_WKSP, project=WACKY_PROJ)
    target_workspace = rally.getWorkspace()
    rally.setProject('*MFA Benefit Durt')
    target_project = rally.getProject()

    epic = rally.get('PortfolioItem/Epic', fetch=True, query='FormattedID = E876',
                      workspace=target_workspace.Name, project=None, instance=True)
    assert epic.FormattedID == 'E876'
    print("{0} {1}".format(epic.FormattedID, epic.Name))

    epic = rally.get('PortfolioItem/Epic', fetch=True, query='FormattedID = E876', instance=True)
    assert epic.FormattedID == 'E876'

    epic = rally.get('PortfolioItem/Epic', fetch=True, query="FormattedID = \"E876\"", instance=True) 
    assert epic.FormattedID == 'E876'

    epic = rally.get('Epic', fetch=True, query='FormattedID = "E876"', instance=True)
    assert epic.FormattedID == 'E876'


def test_epic_update():
    """
        Using a known valid Rally server and known valid access credentials,
        exercise the Rally.create method to create an Epic instance and be handed
        back a usable pyral.entity representing the newly created Epic PortfoloItem instance.
        Then a few seconds later, query for that newly created Epic and update a couple
        of the attributes of the Epic (Name, Ready) and receive back an instance of the updated Epic
        that is non-None and can be interrogated for all atribute information.
    """
    rally = Rally(server=RALLY, apikey=APIKEY, workspace=NICK_WKSP, project=WACKY_PROJ)
    target_workspace = rally.getWorkspace()
    target_project = rally.getProject()

    #rally.setProject('*MFA Benefit Durt')

    epic_info = {
                 "Workspace"   : target_workspace._ref,
                 "Project"     : target_project._ref,
                 "Name"        : "Funicular Wax Shine-athon",
                 "Description" : "Guests hands must not stick on the gate handle and must slide off the viewing port without leaving a dirty handprint",
                 #"Ready"       : False,
                 #"Parent"      : don't need a Feature ref for this test
               }

    print("Creating Funicular Epic ...")
    epic = rally.create('PortfolioItem/Epic', epic_info)
    assert epic
    print("Created Epic item {0}".format(epic.FormattedID))
    assert epic.Name == "Funicular Wax Shine-athon"
    assert epic.Ready == False
    time.sleep(3)

    print("Updating Funicular Epic {0}...".format(epic.FormattedID))
    upd_info = {'FormattedID' : epic.FormattedID, 'Name' : "Funicular haz beenz shinola-ed", 'Ready' : True}
    upd_epic = rally.update('PortfolioItem/Epic', upd_info)
    assert upd_epic
    assert upd_epic.Name == "Funicular haz beenz shinola-ed"
    assert upd_epic.Ready == True
    print("PortfolioItem/Epic update was successful")

    time.sleep(2)
    result = rally.delete('PortfolioItem/Epic', upd_epic.FormattedID)
    assert result == True
    print("PortfolioItem/Epic crash-test-dummy {0} has been deleted".format(epic.FormattedID))


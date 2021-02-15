#!/usr/bin/env python

import sys, os
import types
import urllib
import py

try:
    from urllib import unquote
except:
    from urllib.parse import unquote

import pyral
from pyral import Rally

RallyRESTAPIError  = pyral.context.RallyRESTAPIError

##################################################################################################

from rally_targets import RALLY, RALLY_USER, RALLY_PSWD
from rally_targets import         YETI_USER,   YETI_PSWD
from rally_targets import DEFAULT_WORKSPACE, DEFAULT_PROJECT, NON_DEFAULT_PROJECT
from rally_targets import BOONDOCKS_WORKSPACE, BOONDOCKS_PROJECT
from rally_targets import PROJECT_SCOPING_TREE

##################################################################################################

def test_update_defect_in_other_project():
    """
        Using a known valid Rally server and known valid access credentials,
        obtain a Rally instance for the DEFAULT_WORKSPACE and DEFAULT_PROJECT.
        Update the State value of a Defect identified by a FormattedID that
        is associated with a non-DEFAULT_PROJECT project in the DEFAULT_WORKSPACE.
    """
    rally = Rally(server=RALLY, user=YETI_USER, password=YETI_PSWD,
                                 workspace=DEFAULT_WORKSPACE, project=DEFAULT_PROJECT)
    response = rally.get('Project', fetch=False, limit=100)
    proj = response.next()
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount > 0

    minimal_attrs = "ObjectID,FormattedID,CreationDate,State,ScheduleState,LastUpdateDate"
    criteria = "FormattedID >= DE60"
    defects = rally.get('Defect', fetch=minimal_attrs, query=criteria, project=None)
    assert response.status_code == 200
    assert response.errors   == []
    assert response.warnings == []
    assert response.resultCount > 0

    print("\nDefect set before updates:")
    for defect in defects:
        print("%s   %-10.10s  %-12.12s  %-20.20s" % \
          (defect.FormattedID, defect.State, defect.ScheduleState, defect.LastUpdateDate))

    target_defect = 'DE58'
    upd_info = {"FormattedID" : target_defect,
                'State'       : 'Fixed'
               }
    with py.test.raises(RallyRESTAPIError) as excinfo:
        rally.update('Defect', upd_info, project='Aurora Borealis')
    actualErrVerbiage = excinfo.value.args[0]
    assert 'Aurora Borealis' in actualErrVerbiage
    assert 'not accessible with current credentials' in actualErrVerbiage

    target_defect = 'DE59'
    upd_info = {"FormattedID" : target_defect,
                'State'       : 'Fixed'
               }
    with py.test.raises(Exception) as excinfo:
        rally.update('Defect', upd_info, project='Bristol Bay Barons')
    actualErrVerbiage = excinfo.value.args[0]
    assert 'Unable to update the Defect' in actualErrVerbiage

    target_defect = 'DE60'
    upd_info = {"FormattedID" : target_defect,
                'State'       : 'Fixed'
               }
    result = rally.update('Defect', upd_info, project='Arctic Elevation')
    assert result.State == 'Fixed'

    target_defect = 'DE61'
    upd_info = {"FormattedID" : target_defect,
                'State'       : 'Fixed'
                }
    result = rally.update('Defect', upd_info, project=None)
    assert result.State == 'Fixed'

    defects_after = rally.get('Defect', fetch=minimal_attrs, query=criteria, project=None)
    print("\nDefect set after updates:")
    for defect in defects_after:
        print("%s   %-10.10s  %-12.12s  %-19.19s" % \
              (defect.FormattedID, defect.State, defect.ScheduleState, defect.LastUpdateDate))

    print("\nReset Defect State value:")
    reset_info = {'FormattedID' : 'DE60', 'State' : 'Open'}
    defect = rally.update('Defect', reset_info, project='Arctic Elevation')
    print("%s  %s" % (defect.FormattedID, defect.State))

    reset_info = {'FormattedID' : 'DE61', 'State' : 'Open'}
    defect = rally.update('Defect', reset_info, project=None)
    print("%s  %s" % (defect.FormattedID, defect.State))

    criteria = "FormattedID >= DE60"
    defects_after = rally.get('Defect', fetch=minimal_attrs, query=criteria, project=None)
    print("\ntarget Defects after reset:")
    for defect in defects_after:
        print("%s   %-10.10s  %-12.12s  %-19.19s" % \
              (defect.FormattedID, defect.State, defect.ScheduleState, defect.LastUpdateDate))

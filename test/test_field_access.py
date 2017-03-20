#!/usr/bin/env python

import sys, os
import py

from pyral import Rally
import pyral

##################################################################################################

from rally_targets import AGICEN, AGICEN_USER, AGICEN_PSWD

##################################################################################################

def test_story_fields():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity, and observe that you can access both standard and 
        custom fields by the field Display Name.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    response = rally.get('Story', fetch=True, query=['NumberofCases = 9', 'AffectedCustomers = "abc, xyz"'])
    assert response.status_code == 200
    story = response.next()

    assert story.NumberofCases == 9
    assert story.AffectedCustomers == 'abc, xyz'


def test_defect_fields():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity, and observe that you can access both standard and 
        custom fields by the field Display Name.
    """
    rally = Rally(server=AGICEN, user=AGICEN_USER, password=AGICEN_PSWD)
    cust_field_criteria = {"BugzillaID" : 7224, "JiraKey" : "SLO-109", "QCDefectID" : 5724}
    response = rally.get('Defect', fetch=True, query=cust_field_criteria)
    assert response.status_code == 200
    defect = response.next()
    assert defect.NumberofCases == 4
    assert 'def, jkl, qrs, uvw' in defect.AffectedCustomers

#def test_task_fields():
#    """
#    """


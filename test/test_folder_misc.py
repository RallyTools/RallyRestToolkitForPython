#!/usr/bin/env python

from pyral import Rally

from internal_rally_targets import APIKEY, WORKSPACE, PROJECT

##################################################################################################

def test_test_folder_fields():
    """
        Using a known valid Rally server and known valid access credentials,
        issue a simple query (no qualifying criteria) for a known valid 
        Rally entity, and observe that you can access both standard and 
        custom fields by the field Display Name.
    """
    rally = Rally(apikey=APIKEY, workspace=WORKSPACE, project=PROJECT, isolated_workspace=True)
    response = rally.get('TestFolder', fetch=True, projectScopeDown=True)
    assert response.status_code == 200
    assert response.resultCount > 10
    tf = response.next()

    assert tf.TestFolderStatus is not None
    assert tf.TestFolderStatus.Name == 'Unknown'

    response2 = rally.get('TestFolder', fetch="FormattedID,Name,Parent,Children", projectScopeDown=True)
    assert response2.status_code == 200
    assert response2.resultCount > 10
    tf = response2.next()


# def test_test_folder_subfields():
#     """
#         Using a known valid Rally server and known valid access credentials,
#         issue a simple query (no qualifying criteria) for a known valid
#         Rally entity, and observe that you can access both standard and
#         custom fields by the field Display Name.
#     """
#     agicen = Rally(apikey=APIKEY, workspace=WORKSPACE, password=PROJECT, isolated_workspace=True)
#     #response = rally.get('TestFolder', fetch="FormattedID,Name,Parent,Children", projectScopeDown=True, isolated_workspace=True)
#     response = agicen.get('TestFolder', fetch=True, projectScopeDown=True)
#     assert response.status_code == 200
#     assert response.resultCount > 10
#     tf = response.next()
#     assert tf.TestFolderStatus.Name == 'Unknown'


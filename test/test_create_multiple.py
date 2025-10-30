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

@dataclass
class Story:
    oid: int = field(default=-1)
    Name: str = field(default="")
    Description: str = field(default='')

##################################################################################################

def test_running_createMultiple():
    """
        Two modes are tested here, the first by putting desired attributes in dicts and supplying that list
        and the second by creating some local Story items (Data like instances) and putting those in a
        list supplied to the rally.createMultiple method
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD, workspace='Conny2', project='testwest')
    entity_name = 'Story'
    item_1 = {'Name' : 'Time waits for no one', 'Description': 'mesopotamian gruel spalsh'}
    item_2 = {'Name' : 'Rock my soul today',    'Description': 'baelooka moln vrikfy'}
    dict_items = [item_1, item_2]
    result = rally.createMultiple(entity_name, dict_items)
    assert len(result) == 2

    # see if we can create some golem Story items and use those
    story_1 = Story(Name='Waiting for time to stand still', Description='Back up the truck until the gold drops in')
    story_2 = Story(Name='Bring the mini-bar for Sally',    Description='Need to offer libations to recalcitant prospects')
    inst_items = [story_1, story_2]
    result = rally.createMultiple(entity_name, inst_items)
    assert len(result) == 2

##################################################################################################

def prereq_createMultiple_preamble():
    """
        Using a known valid Rally server and known valid access credentials,
        Grab the Rally schema for a Story entity
          and divvy the results up to be able to show
            attributes that cannot be created via the WSAPI (like CreatDate, ObjectID, etc)
            attributes that are defined as COLLECTION
            attributes that are custom fields where the ElementName is prefixed with 'c_'
            attributes that are Required to be supplied on creation of an actual Story instance
            attributes that are Optional to be supplied on creation of an actual Story instance
    """
    rally = Rally(server=RALLY, user=RALLY_USER, password=RALLY_PSWD)
    stod = rally.typedef('Story')
    story_attrs = stod.Attributes
    # show the non-createable attrs and whether they are/aren't Required
    # show the creatable COLLECTION attrs
    # show the Required creatable non-COLLECTION attrs and whether they are CUSTOM
    # show the Optional creatable non-COLLECTION attrs and where they are CUSTOM
    #    ElementName, Custom, Required, ReadOnly, AttributeType, SchemaType
    nc_attrs     = [attr for attr in story_attrs if attr.ReadOnly]
    crcoll_attrs = [attr for attr in story_attrs if not attr.ReadOnly and attr.AttributeType == 'COLLECTION'] # show whether Required
    ncreq_attrs  = [attr for attr in story_attrs if not attr.ReadOnly and attr.AttributeType != 'COLLECTION' and attr.Required] # show whether CUSTOM
    ncopt_attrs  = [attr for attr in story_attrs if not attr.ReadOnly and attr.AttributeType != 'COLLECTION' and not attr.Required] # show whether CUSTOM

    print("Non-Createable attrs")
    for attr in nc_attrs:
        spad = f'{attr.ElementName:30.30}  Required? {'True' if attr.Required else 'False'} '
        print(spad)
    print("-" * 90)

    print("Createable Collection attrs")
    for attr in crcoll_attrs:
        spad = f'{attr.ElementName:30.30}  Required? {'True' if attr.Required else 'False'}   COLLECTION'
        print(spad)
    print("-" * 90)

    print("Required Createable attrs")
    for attr in ncreq_attrs:
        spad = f'{attr.ElementName:30.30}  Required? {'True' if attr.Required else 'False'}   {attr.AttributeType:8.8}   Custom? {attr.Custom}'
        print(spad)
    print("-" * 90)

    print("Optional Createable attrs")
    for attr in ncopt_attrs:
        spad = f'{attr.ElementName:30.30}  Required? {'True' if attr.Required else 'False'}   {attr.AttributeType:8.8}   Custom? {attr.Custom}'
        print(spad)

    assert 'Moar' == 'moar'.title()


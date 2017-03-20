
###################################################################################################
#
#  pyral.hydrate - Python Rally REST API module to hydrate local Rally type instances
#          dependencies:
#               intra-package: classFor           from pyral.entity
#                              VERSION_ATTRIBUTES from pyral.entity
#                              MINIMAL_ATTRIBUTES from pyral.entity
#
###################################################################################################

__version__ = (1, 2, 4)

import sys
import imp
imp.reload(sys)  # Reload gets a sys module that has the setdefaultencoding before site.py deletes it
import six
six.PY2 and sys.setdefaultencoding('UTF8') # not required in python 3

from .entity import classFor, VERSION_ATTRIBUTES, MINIMAL_ATTRIBUTES, PORTFOLIO_ITEM_SUB_TYPES

##################################################################################################

class EntityHydrator(object):
    """
        An instance of this class is used to instantiate an instance of a class directly
        related to a Rally entity.  An instance is given the information from a JSON object
        in the form of a dict.  From the information in the item dict, the correct class for
        a new Rally equivalent instance is determined and an instance produced.  
        The EntityHydrator then uses the other information in the item dict to populate the
        attributes in the manufactured instance.
    """

    def __init__(self, context, hydration="full"):
        self.context   = context
        self.hydration = hydration


    def _attributes(self, item):
        return [attr for attr in list(item.keys()) 
                      if attr not in MINIMAL_ATTRIBUTES
                     and attr not in VERSION_ATTRIBUTES]


    def hydrateInstance(self, item, existingInstance=None):
        """
            Given a dict representing an item in a result set returned from a query (GET),
            instantiate an instance of the class associated with the _type, and populate
            the instance attributes with values from the dict item.
            The OID value is embedded in the value for the '_ref' key
            Use this OID and the name in the call to instantiate the object of the desired type.
        """ 

        if not existingInstance:
            instance = self._basicInstance(item)
        else:
            instance = existingInstance

        attributeNames = self._attributes(item)
        for attrName in attributeNames:
            attrValue = item.get(attrName)
            self._setAppropriateAttrValueForType(instance, attrName, attrValue, 1)

        if self.hydration == "full":
            instance._hydrated = True
##
##        print("hydrated %s has these attributes: %s, hydration setting: %s" % \
##              (instance._type, instance.attributes(), self.hydration))
##
        return instance


    def _basicInstance(self, item):
        """
            All native Rally entities have '_type', '_ref', '_refObjectName' in the item dict.
            However, there are entities with attributes that are non-scalar and do not have a '_type' entry.
            So, we cheat and make an instance of a CustomField class and return that. 
        """
        itemType = item.get('_type', "CustomField")
##
##        print("in EntityHydrator.hydrateInstance, _basicInstance to create a %s for %s" % (itemType, item))
##
        name = item.get('_refObjectName', "Unknown")
        if itemType == 'AllowedQueryOperator':
            name = item['OperatorName']
        oid = 0
        resource_url = item.get('_ref', "") 
        if resource_url:
            oid = resource_url.split('/')[-1]
        try:
            instance = classFor[str(itemType)](oid, name, resource_url, self.context)
        except KeyError as e:
            bonked = True
            if '/' in itemType:  # valid after intro of dyna-types in 1.37
                try:
                    type_name, type_subdivision = itemType.split('/')
                    instance = classFor[str(type_name)](oid, name, resource_url, self.context)
                    itemType = type_name
                    bonked = False
                except KeyError as e:
                    raise
            elif itemType in PORTFOLIO_ITEM_SUB_TYPES:
                try:
                    type_name = "PortfolioItem_%s" % itemType
                    instance = classFor[str(type_name)](oid, name, resource_url, self.context)
                    itemType = type_name
                    bonked = False
                except KeyError as e:
                    raise
            if bonked:    
                print("No classFor item for |%s|" % itemType)
                raise KeyError(itemType)

        instance._type = itemType  # although, this info is also available via instance.__class__.__name__
        if itemType == 'AllowedAttributeValue':
            instance.Name  = 'AllowedValue'
            instance.value = item['StringValue']
##
##        print("in EntityHydrator.hydrateInstance, _basicInstance returning a %s" % instance._type)
##
        return instance

    def _setAppropriateAttrValueForType(self, instance, attrName, attrValue, level=0):
##
##        indent = "  " * level
##        print("%s attr level: %d  attrName |%s| attrValue: |%s|" % (indent, level, attrName, attrValue))
##
        if attrValue == None:
            setattr(instance, attrName, attrValue)
            return 

        if type(attrValue) == list:
            elements = [self._unravel(element) for element in attrValue]
            setattr(instance, attrName, elements)
            return

        if type(attrValue) != dict:
            setattr(instance, attrName, attrValue)
            return 

        # if we're here, then  type(attrValue) has to be a dict
        # for now, only attempt to populate fully to the third level, after that, short-circuit
        if '_rallyAPIMajor' in attrValue:
            del attrValue['_rallyAPIMajor']
        if '_rallyAPIMinor' in attrValue:
            del attrValue['_rallyAPIMinor']

        if level > 3:
            setattr(instance, attrName, attrValue)
            return

        # if the attrValue contains a Count key and a _ref key and the Count is > 0, then 
        # yank the collection ref at _ref and rename the attrName to __collection_ref_for_<attrName>
        if '_ref' in attrValue and 'Count' in attrValue:
            if attrValue['Count'] == 0:
                setattr(instance, attrName, [])
            else:
                collection_ref = attrValue['_ref']
                setattr(instance, "__collection_ref_for_%s" % attrName, collection_ref)
            return

        if attrName == 'RevisionHistory':  # this gets treated as a collection ref also at this point
            collection_ref = attrValue['_ref']
            setattr(instance, "__collection_ref_for_%s" % attrName, collection_ref)
            return
            
        attrInstance = self._basicInstance(attrValue)
        setattr(instance, attrName, attrInstance)
        subAttrNames = self._attributes(attrValue)
        for subAttrName in subAttrNames:
            subAttrValue = attrValue.get(subAttrName)
            self._setAppropriateAttrValueForType(attrInstance, subAttrName, subAttrValue, level+1)

        # the following left over from refactoring.
        # commented out as it led to entities being set as being fully hydrated when
        # in fact, they weren't.  May want to determine if the commenting out has a
        # an impact in terms of unnecessary requests back to Rally to get 
        # attribute.sub-attr values when they might actually be hydrated.
        # 
        # Addendum 2015-02-21: this has been commented out since 0.9.x timeframe
        #                      get rid of these comments and commented out code
        #                      as part of 1.2.0 release
        #if self.hydration == 'full':
        #    attrInstance._hydrated = True
        return


    def _unravel(self, thing):
        if type(thing) == dict and thing.get('_type', None):
            return self._basicInstance(thing)
        else:
            return thing

##################################################################################################

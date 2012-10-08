
###################################################################################################
#
#  pyral.hydrate - Python Rally REST API module to hydrate local Rally type instances
#          dependencies:
#               intra-package: classFor           from pyral.entity
#                              VERSION_ATTRIBUTES from pyral.entity
#                              MINIMAL_ATTRIBUTES from pyral.entity
#
###################################################################################################

__version__ = (0, 9, 3)

import types
from pprint import pprint

from .entity import classFor, VERSION_ATTRIBUTES, MINIMAL_ATTRIBUTES

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
##
##        print "in hydrateInstance, item contents:\n    %s" % repr(item)
##
        return [attr for attr in item.keys() 
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
##        print "hydrated %s has these attributes: %s, hydration setting: %s" % \
##              (instance._type, instance.attributes(), self.hydration)
##
        return instance


    def _basicInstance(self, item):
        """
            All native Rally entities have '_type', '_ref', '_refObjectName' in the item dict.
            However, there are entities with attributes that are non-scalar and do not have a '_type' entry.
            So, we cheat and make an instance of a CustomField class and return that. 

            For now we are not using try/except as in development we want any Exception to be 
            raised to see what sort of problems might be encountered
        """
        itemType = item.get(u'_type', "CustomField")
##
##        print "in EntityHydrator.hydrateInstance, _basicInstance to create a %s" % itemType
##
        name = item.get(u'_refObjectName', "Unknown")
        if itemType == 'AllowedQueryOperator':
            name = item[u'OperatorName']
        #elif not item.get(u'_refObjectName', None):
        #    print "item has no _refObjectName, has the following info..."
        #    pprint(item)
        oid = 0
        resource_url = item.get(u'_ref', "") 
        if resource_url:
            oid = resource_url.split('/')[-1].replace('.js', '')
        try:
            instance = classFor[str(itemType)](oid, name, resource_url, self.context)
        except KeyError, e:
            bonked = True
            if '/' in itemType:  # valid after intro of dyna-types in 1.37
                try:
                    type_name, type_subdivision = itemType.split('/')
                    instance = classFor[str(type_name)](oid, name, resource_url, self.context)
                    itemType = type_name
                    bonked = False
                except KeyError, e:
                    raise
            if bonked:    
                print "No classFor item for |%s|" % itemType
                raise KeyError(itemType)

        instance._type = itemType  # although, this info is also available via instance.__class__.__name__
        if itemType == 'AllowedAttributeValue':
            instance.Name  = 'AllowedValue'
            instance.value = item[u'StringValue']
        return instance


    def _setAppropriateAttrValueForType(self, instance, attrName, attrValue, level=0):
##
##        print "setting attribute level: %d  attrName |%s|" % (level, attrName)
##
        if attrValue == None:
            setattr(instance, attrName, attrValue)
            return 

        if type(attrValue) == types.ListType:
            elements = [self._unravel(element) for element in attrValue]
            setattr(instance, attrName, elements)
            return

        if type(attrValue) != types.DictType:
            setattr(instance, attrName, attrValue)
            return 

        # if we're here, then  type(attrValue) == types.DictType
        # for now, only attempt to populate fully to the third level, after that, short-circuit
        if level > 3:
            setattr(instance, attrName, attrValue)
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
        #if self.hydration == 'full':
        #    attrInstance._hydrated = True
        return


    def _unravel(self, thing):
        if type(thing) == types.DictType and thing.get(u'_type', None):
            return self._basicInstance(thing)
        else:
            return thing


##################################################################################################

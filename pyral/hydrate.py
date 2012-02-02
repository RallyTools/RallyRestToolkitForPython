
###################################################################################################
#
#  pyral.hydrate - Python Rally REST API module to hydrate local Rally type instances
#          dependencies:
#               intra-package: classFor           from pyral.entity
#                              VERSION_ATTRIBUTES from pyral.entity
#                              MINIMAL_ATTRIBUTES from pyral.entity
#
###################################################################################################

__version__ = (0, 8, 9)

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

    def hydrateInstance(self, item, existingInstance=None):
        """
            Given a dict representing an item in a result set returned from a query (GET),
            instantiate an instance of the class associated with the _type, and populate
            the instance attributes with values from the dict item.
            The OID value is embedded in the value for the '_ref' key
            Use this OID and the name in the call to instantiate the object of the desired type.
        """
        def basicInstance(item):
            """
                All native Rally entities have '_type', '_ref', '_refObjectName' in the item dict.
                However, there are entities with attributes that are non-scalar and do not have a '_type' entry.
                So, we cheat and make an instance of a CustomField class and return that. 

                For now we are not using try/except as in development we want any Exception to be 
                raised to see what sort of problems might be encountered
            """
            itemType = item.get(u'_type',          "CustomField")
##
##            print "in hydrateInstance, basicInstance to create a %s" % itemType
##
            name     = item.get(u'_refObjectName', "Unknown")
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
                instance = classFor[itemType](oid, name, resource_url, self.context)
            except KeyError, e:
                print "No classFor item for |%s|" % itemType
                raise KeyError(itemType)
            instance = classFor[itemType](oid, name, resource_url, self.context)
            instance._type = itemType  # although, this info is also available via instance.__class__.__name__
            if itemType == 'AllowedAttributeValue':
                instance.Name  = 'AllowedValue'
                instance.value = item[u'StringValue']
            return instance


        def _attributes(item):
            return [attr for attr in item.keys() 
                          if attr not in MINIMAL_ATTRIBUTES
                         and attr not in VERSION_ATTRIBUTES]
            
##
##        print "in hydrateInstance, item contents:\n    %s" % repr(item)
##
        if not existingInstance:
            instance = basicInstance(item)
        else:
            instance = existingInstance
        attributeNames = _attributes(item)
        for attrName in attributeNames:
            attrValue = item.get(attrName)
            if attrValue == None:
                setattr(instance, attrName, attrValue)
            elif type(attrValue) == types.ListType:
                def unravel(thing):
                    if type(thing) == types.DictType and thing.get(u'_type', None):
                        return basicInstance(thing)
                    else:
                        return thing
                elements = [unravel(element) for element in attrValue]
                setattr(instance, attrName, elements)
            elif type(attrValue) != types.DictType:  
                setattr(instance, attrName, attrValue)
            else:  #  type(attrValue) == types.DictType
                # for now only go 1 level deep
##
##                print "instance.%s value : |%s|  (is a %s)" % (attrName, attrValue, type(attrValue))
##
                attrInstance = basicInstance(attrValue)
                setattr(instance, attrName, attrInstance)
                subAttrNames = _attributes(attrValue)
                for subAttrName in subAttrNames:
                    subAttrValue = attrValue.get(subAttrName)
                    if type(subAttrValue) != types.DictType:
                        setattr(attrInstance, subAttrName, subAttrValue)

        if self.hydration == "full":
            instance._hydrated = True

        return instance

##################################################################################################

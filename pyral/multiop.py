import sys
import re
from collections import OrderedDict
from pprint import pprint, pformat  # use sort_dicts=False
import json

class MultipleOperationError(Exception): pass

ITEM_TYPE_INCONSISTENCY_ERROR = 'All items must be consistent, ie., all dicts or all data-like instances'

################################################################################################

def looksLikeDataInstance(target):
    item_dir = dir(target)
    if '__dataclass_fields__' in item_dir:
        return True
    if 'pyral.entity' in target.__class__.__name__:
        return True
    return False

################################################################################################

def createMultiple(self, entityName, items, fields=None, workspace='current', project='current', **kwargs):
    """
        Given an entityName (for a valid Rally entity type) and a sequence of items (described below) and
        potential a list of Rally entity attribute names, use the Rally WSAPI /batch endpoint
        to effect the creation of items corresponding to the elements in list.
        The elements in the list MUST have information about ALL of the required fields of the Rally entity.
        The elements CAN have information about non-required fields.
        An item in the list of items CANNOT have any attributes that are of the Rally COLLECTION type.

        items can be all dict instances
        OR
        items can be all pyral entity instances (or instances of "data" class)

    """
    if not items:
        return []

    num_dict_items = len([item for item in items if     isinstance(item, dict)])
    num_inst_items = len([item for item in items if not isinstance(item, dict) and looksLikeDataInstance(item)])

    if num_dict_items and len(items) != num_dict_items:
        raise MultipleOperationError(ITEM_TYPE_INCONSISTENCY_ERROR)
    elif num_inst_items and len(items) != num_inst_items:
        raise MultipleOperationError(ITEM_TYPE_INCONSISTENCY_ERROR)

    td = self.typedef(entityName)
    entity_attrs = td.Attributes

    status, problems, xformed_items = vetSuppliedAttributes(entityName, entity_attrs, items, fields)
    if status != 'OK':
        raise MultipleOperationError(f'Invalid or insufficient attributes for data items: {status} ==> {repr(problems)}')

    batch_bomb = batchPacker(entityName, 'create', xformed_items)
    result = doBatchOperation(self, entityName, batch_bomb, 'create')
    return result

################################################################################################

def updateMultiple(self, entityName, items, fields=None, workspace='current', project='current', **kwargs):
    """
        Given an entityName (for a valid Rally entity type) and a sequence of items (described below)
        and a list of Rally entity attribute names that are to be updated (fields),
        use the Rally WSAPI /batch endpoint to effect the update of items corresponding
        to the elements in list of items.
        Each item MUST contain an identifying attribute name and value (usually ObjectID is used).
        The other elements in the list CAN only be attributes that are editable AND
        an item in the list of elements CANNOT have any attributes that are of the Rally COLLECTION type.

        items can be all dict instances
        OR
        items can be all pyral entity instances (or instances of "data" class)

        If the items have attributes present with non-null values and the attribute name is NOT
        in the fields list, then those attributes will not be updated via this mechanism.
    """
    if not items:
        return []

    num_dict_items = len([item for item in items if     isinstance(item, dict)])
    num_inst_items = len([item for item in items if not isinstance(item, dict) and looksLikeDataInstance(item)])

    if num_dict_items and len(items) != num_dict_items:
        raise MultipleOperationError(ITEM_TYPE_INCONSISTENCY_ERROR)
    elif num_inst_items and len(items) != num_inst_items:
        raise MultipleOperationError(ITEM_TYPE_INCONSISTENCY_ERROR)

    td = self.typedef(entityName)
    entity_attrs = td.Attributes

    item_type = 'dict' if num_dict_items else 'instance'
    result = prepItemsForUpdate(entityName, entity_attrs, item_type, items, fields=fields)
    status, problems, xformed_items = result

    if status != 'OK':
        raise MultipleOperationError(f'Invalid or insufficient attributes for data items: {status} ==> {repr(problems)}')

    batch_bomb = batchPacker(entityName, 'update', xformed_items)
    result = doBatchOperation(self, entityName, batch_bomb, 'update')
    return result

###################################################################################################

def prepItemsForUpdate(entity_name, entity_attrs, item_type, items, fields):
    """
         Have to add ObjectID value to a xfmd_item (get this out of item)
    """
    xformed_items = []
    upd_candidates = []
    # item_type is either 'dict' or 'instance'
    if item_type == 'dict':
        if not fields:
            upd_candidates = items[:]
        else:
            for dict_item in items:
                candup = {en:av for en, av in dict_item.items() if en in fields}
                candup['ObjectID'] = dict_item['ObjectID']
                upd_candidates.append(candup)
    else:
        if not fields:
            for dinst in items:
                candup = {an:getattr(dinst,an, None) for an in entity_attrs}
                candup['ObjectID'] = dinst.oid if hasattr(dinst, 'oid') else dinst.ObjectID
                upd_candidates.append(candup)
        else:
            for dinst in items:
                candup = {field:getattr(dinst, field, None) for field in fields if hasattr(dinst, field) }
                candup['ObjectID'] = dinst.oid if hasattr(dinst, 'oid') else dinst.ObjectID
                upd_candidates.append(candup)

    # at this point the input fodder in upd_candidates is a list of dicts, vet them for validity
    allwd_attrs  = [attr for attr in entity_attrs if not attr.ReadOnly and attr.AttributeType != 'COLLECTION']
    allowed_attr_names = [attr.ElementName for attr in allwd_attrs]

    # recast attr names of custom fields to the Rally internal name of the custom field
    for cand in upd_candidates:
        obj_id = cand['ObjectID']
        xfmd_item = OrderedDict([('ObjectID', obj_id)])
        for attr_name, attr_value in cand.items():
            if attr_name == 'ObjectID': continue
            # is this a custom field, if so prefix the c_ to the attr_name before placing it in the xfmd_item dict
            cf = [aen for aen in allowed_attr_names if f'c_{attr_name}' == aen]
            field_name = f'c_{attr_name}' if cf else attr_name
            xfmd_item[field_name] = attr_value
        xformed_items.append(xfmd_item)

    # identify any field in any item that is ReadOnly or COLLECTION type
    read_only_attrs  = []
    collection_attrs = []
    def isReadOnlyAttribute(attr_name, entity_attrs):
        matching_rally_attr = [attr for attr in entity_attrs if attr.ElementName == attr_name ]
        if matching_rally_attr:
            if not matching_rally_attr[0].ReadOnly: return False
        return True

    def isCollectionAttribute(attr_name, entity_attrs):
        matching_rally_attr = [attr for attr in entity_attrs if attr.ElementName == attr_name ]
        if matching_rally_attr:
            if matching_rally_attr[0].AttributeType == 'COLLECTION': return True
        return False

    read_only_attrs  = set()
    collection_attrs = set()
    mistyped_attrs   = set()
    for xfmd_item in xformed_items:
        for attr_name, attr_value in xfmd_item.items():
            if attr_name == 'ObjectID':
                continue
            if isReadOnlyAttribute(attr_name, entity_attrs):
                read_only_attrs.add(attr_name)
            elif isCollectionAttribute(attr_name, entity_attrs):
                collection_attrs.add(attr_name)
            else:
                avt = [attr.AttributeType for attr in entity_attrs if attr.ElementName == attr_name]
                avt_ok, rally_value = transformToRallyValue(attr_name, attr_value, avt.pop(0))
                if not avt_ok:
                    mistyped_attrs.add((attr_name, attr_value))
                else:
                    xfmd_item[attr_name] = rally_value

    status = 'OK'
    problems = []
    if read_only_attrs:
        status = 'READ_ONLY'
        problems = list(read_only_attrs.copy())
    elif collection_attrs:
        status = 'COLLECTION'
        problems = list(collection_attrs.copy())
    elif mistyped_attrs:
        status = "MISTYPED"
        problems = list(mistyped_attrs.copy())

    return (status, problems, xformed_items)

###################################################################################################

def vetSuppliedAttributes(entity_name, entity_attrs, items, fields):
    """
        entity_name, entity_attrs, items are all required to have a value or values
        entity_attrs is a complete list of valid attributes for the entity_name.
        items is a sequence of either dicts or Data class-like instances.
        fields is either None or a sequence of valid attributes names that are
        intended to include in the payload for each item.  If fields is None
        then the attributes present in each dict in items (or data item attribute)
        will be part of the JSON data payload for each batch item.

          identify the non-createable attrs and whether they are/aren't Required
          identify the creatable COLLECTION attrs
          identify the Required creatable non-COLLECTION attrs and whether they are CUSTOM
          identify the Optional creatable non-COLLECTION attrs and where they are CUSTOM
             ElementName, Custom, Required, ReadOnly, AttributeType, SchemaType

        we want to return a tuple of:
           status  -  'OK', 'INVALIDS', 'MISSING', 'MISTYPED'
           attributes = []
           xformed_items (., ., .)

        If _any_ of items contain an attribute that is one of:
            non-creatable attribute
            COLLECTION type attribute
          then we'll add the name of the attr to a function var  named 'disallowed_attrs'
          and return a tuple of:
             'INVALIDS"
             disallowed_attrs
             xformed_items list

         If _any_ of items are found to contain an attr whose value is NOT the right type
           we'll add the "attr_name:attr_value" to a function var named 'mistyped_attr_values'
           and return a tuple of:
            'MISTYPED'
            mistyped_attr_values
            xformed_items list

         if _any_ of items are found to be missing a required attr isn't in the following list
            'Project', 'FlowState', 'ScheduleState', ...
         we'll add the name of the missing required attribute to a function var named 'missing_reqd_attrs'
         and return a tuple of:
           'MISSING'
            missing_reqd_attrs
            xformed_items list

        If the items referenced only createable and non-COLLECTION attributes and had a reasonable value type
          internally we'll build up a list of items where any Custom field has the attribute name supplied by the
          caller replaced with the correct c_ prefixed attribute name, call this list xformed_items
          then we'll return ('OK', [list of the valid attributes found in items], xfofmed_items)
    """
    noncr_attrs  = [attr for attr in entity_attrs if attr.ReadOnly]
    crcoll_attrs = [attr for attr in entity_attrs if not attr.ReadOnly and attr.AttributeType == 'COLLECTION']
    ncreq_attrs  = [attr for attr in entity_attrs if not attr.ReadOnly and attr.AttributeType != 'COLLECTION' and attr.Required] # show whether CUSTOM
    ncopt_attrs  = [attr for attr in entity_attrs if not attr.ReadOnly and attr.AttributeType != 'COLLECTION' and not attr.Required] # show whether CUSTOM
    allwd_attrs  = [attr for attr in entity_attrs if not attr.ReadOnly and attr.AttributeType != 'COLLECTION']
    reqd_attr_names = [attr.ElementName for attr in ncreq_attrs]

    disallowed_attrs     = set()
    mistyped_attr_values = set()
    missing_reqd_attrs   = set()
    xformed_items = []
    for item in items:
        xfmd_item = OrderedDict()
        if not isinstance(item, dict) and hasattr(item, '__dict__'):  # this is an instance of a Data-like class
            # recast item as a dict
            recast_dict = {an:av for an,av in item.__dict__.items()}
            item = recast_dict

        # identify any attr(s) that are not createable (ie., disallowed)
        for attr_name, attr_value in item.items():
            rf = [attr.ElementName for attr in noncr_attrs if attr.ElementName == attr_name]
            if rf:
                disallowed_attrs.add(attr_name)

        # recast attr names of custom fields to the Rally internal name of the custom field
        for attr_name, attr_value in item.items():
            # is this a custom field, if so prefix the c_ to the attr_name before placing it in the xfmd_item dict
            cf = [attr.ElementName for attr in ncopt_attrs if attr.ElementName == f'c_{attr_name}']
            fn = f'c_{attr_name}' if cf else attr_name
            xfmd_item[fn] = attr_value

        # identify any attr(s) whose value is not the prescribed type
        for attr_name, attr_value in item.items():
            avt = [attr.AttributeType for attr in allwd_attrs if attr.ElementName == attr_name]
            if avt:
                avt_ok, av_rally = transformToRallyValue(attr_name, attr_value, avt.pop(0))
                if avt_ok:
                    xfmd_item[attr_name] = av_rally
                else:
                    mistyped_attr_values.add((attr_name, attr_value))
            else:
                burp = f'item attribute {attr_name} is not an attribute that can be set'

        # identify whether item is missing a required createable attr and value
        excluded_required_attrs = ('FlowState', 'ScheduleState', 'Project')
        attr_names = list(item.keys())
        for req_attr in reqd_attr_names:
            if req_attr in excluded_required_attrs:
                continue
            avt_ok = True if req_attr in attr_names else False
            if  not avt_ok :
                missing_reqd_attrs.add(req_attr)

        xformed_items.append(xfmd_item)

    status = 'OK' if not disallowed_attrs and not missing_reqd_attrs and not mistyped_attr_values else 'PROBLEM'
    probs = []
    if status != 'OK':   # while there may be multiple reasons, we'll only mention one category...
        if disallowed_attrs:
            status, probs = 'INVALIDS',disallowed_attrs
        elif missing_reqd_attrs:
            status, probs = 'MISSING', missing_reqd_attrs
        elif mistyped_attr_values:
            status, probs = 'MISTYPED', mistyped_attr_values
    return (status, probs, xformed_items)

###################################################################################################

def transformToRallyValue(attr_name, attr_value, avt):
    """
        Given the name of a Rally entity attribute, the proposed value for the attribute and
        the name of the Rally entity attribute type, determine if the provided attr_value
        is of that type or can be turned into a value of the correct type for Rally.
        Return a 2 tuple of status (OK or not OK) and the value in the correct type for Rally.
    """
    rally_value = attr_value
    avt_ok = None
    match avt:
        case 'STRING':
            avt_ok = isinstance(attr_value, str)
        case 'BOOLEAN':
            if isinstance(attr_value, bool):
                avt_ok = True
            elif isinstance(attr_value, str):
                if attr_value.lower() == 'true':
                    rally_value = True
                    avt_ok = True
                elif attr_value.lower() == 'false':
                    rally_value = False
                    avt_ok = True
                else:
                    avt_ok = False
        case 'TEXT':
            avt_ok = isinstance(attr_value, str)
        case 'INTEGER':
            mo = re.match(r'^\d+$', attr_value)
            avt_ok = True if mo else False
            if avt_ok:
                rally_value = int(attr_value)
        case 'QUANTITY':
            if isinstance(attr_value, float) or isinstance(attr_value, int):
                avt_ok = True
            elif isinstance(attr_value, str):
                moi = re.match(r'^\d+$', attr_value)  # does the string contain only digit chars?
                mof = re.match(r'^\d+\.\d+$',
                               attr_value)  # does the string contain what looks like a fractional number?
                if moi:
                    rally_value = int(attr_value)
                    avt_ok = True
                elif mof:
                    rally_value = float(attr_value)
                    avt_ok = True
                else:
                    avt_ok = False
        case 'DATE':
            dtonly = re.match(r'^\d\d-\d\d-\d\d(\d\d)?$')
            dtime = re.match(r'^\d\d-\d\d-\d\d(\d\d) \d\d:\d\d:\d\d%')
            if dtonly or dtime:
                avt_ok = True
            else:
                avt_ok = False
        case 'OBJECT':
            # does the attr_value look like:
            #  https://rally1.rallydev.com/slm/webservice/v2.0/blurg/34315
            #  or
            #  /blurg/3243214  or just blurg/343904
            # if so avt_ok = True  otherwise False
            full_ref_pattern = r'^https://rally1.rallydev.com/slm/webservice/v2.0/[a-z]+(/[a-z]+)?$'
            short_ref_pattern = r'/?[a-z]+(/[a-z]+)?$'
            if isinstance(attr_value, str):
                mofr = re.match(full_ref_pattern, attr_value)
                mosr = re.search(short_ref_pattern, attr_value)
                avt_ok = True if (mofr or mosr) else False
            else:
                avt_ok = False
        case _:
            avt_ok = False

    return avt_ok, rally_value

###################################################################################################

def batchPacker(entity_name, operation, items):
    """
        Given the name of a Rally entity (artifact or timebox or user/role) and the name of
        the intended operation (create or update) and a sequence of dicts with info
        that is to be realized in Rally items construct a JSON structure compatible
        with the Rally /batch endpoint
        The batch structure is depicted thusly:
        {
          "Batch": [
                    {
                     "Entry": {
                               "Path"  : "/testcaseresult/create",
                               "Method": "POST",
                               "Body"  : {
                                          "testcaseresult": {
                                              "Build":5,
                                              "Date":"2025-02-27T18:03:29Z",
                                              "Testcase": "/TestCase/12345678",
                                              "Verdict":"Pass"
                                             }
                                         }
                              }
                    },
                    {
                     "Entry": {
                               "Path"  : "/testcaseresult/create",
                               "Method": "POST",
                               "Body"  : {
                                          "testcaseresult": {
                                              "Build":5,
                                              "Date":"2025-02-27T19:11:27Z",
                                              "Testcase": "/TestCase/1234",
                                              "Verdict":"Fail"
                                             }
                                         }
                              }
                    }
                  ]
       }

       each item in the sequence gets transformed into a entity_spec dict keyed by the
       entityname with ElementName and value pairs. Then that dict result is "wrapped
       then that dict result is "wrapped" in a larger holding Entry dict whose keys are "Path", "Method" and "Body".
       The "Body" value is the entity_spec produced from the item. This process results in list of Entry dicts
       which in turn is "contained" in a larger dict whose solitary key is "Batch" having the value of the
       list of Entry dicts

    """
    entries = []
    for  item in items:
        if operation == 'create':
            path   = f'/{entity_name.lower()}/create'
            method = 'PUT'
        else:
            obj_id = item['ObjectID']
            path = f'/{entity_name.lower()}/{obj_id}'
            method = 'POST'
            del item['ObjectID'] # this doesn't need to be part of the body, it is needed for the path though
        item_body = {f"{entity_name.lower()}" : item}
        entry_dict = OrderedDict([("Path", path), ("Method", method), ("Body", item_body)])
        entry = { "Entry": entry_dict }
        entries.append(entry)

    batch_data = {"Batch" : entries}
    return batch_data

################################################################################################

def doBatchOperation(self, entity, items, operation):
    batch_endpoint = f'{self.service_url}/batch'
    security_token = self.obtainSecurityToken()
    # we explicitly specify the workspace and project ref oids in the query string on the URL
    wksp = self.getWorkspace()
    proj = self.getProject()
    query_string = f'key={security_token}&workspace=/{wksp.ref}&project=/{proj.ref}&fetch=FormattedID,Name'
    batch_url = f'{batch_endpoint}?{query_string}'
    payload = json.dumps(items)
    try:
        response = self.session.post(batch_url, data=payload)
    except Exception as exc:
        raise MultipleOperationError(str(exc))
    #print(response.status_code)
    if response.status_code != 200:
        return []

    #print(response.text)
    #pprint(brc, indent=2)
    # what could we get out of response?  could we get ObjectID and FormattedID of each created/updated item?
    # response looks like:
    # '{"BatchResult" : {"Errors" : [], "Warnings": [], "Results": [{"Object" : {}, "Errors": []}, {"Object"}, ...]}}'

    affected_items = []
    brc = json.loads(response.text)
    try:
        br = brc['BatchResult']
        batch_errors = br['Errors']
        results = br['Results']
        num_items_msg = f'results has {len(results)} objects in it'
        #print(num_items_msg)
        for globbie in results:
            item_errors = globbie['Errors']
            if item_errors:
                item_error = item_errors.pop(0)
            else:
                robj = globbie["Object"] # Rally Object
                item = {"_ref"        : robj["_ref"],
                        "ObjectID"    : robj["_ref"].split('/')[-1],
                        "FormattedID" : robj["FormattedID"],
                        "Name"        : robj["_refObjectName"]
                       }
                affected_items.append(item)
    except Exception as exc:
        print(str(exc))

    return affected_items

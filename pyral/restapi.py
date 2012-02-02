#!/opt/local/bin/python2.6

###################################################################################################
#
#  pyral.restapi - Python Rally REST API module
#          round 8 version with GET, PUT, POST and DELETE operations, support multiple instances
#          dependencies:
#               requests v0.8.2 or better
#
###################################################################################################

__version__ = (0, 8, 9)

import sys, os
import re
import types
import time
import urllib
import json
from operator import itemgetter

import requests   

# intra-package imports
from .config  import PROTOCOL, SERVER, WS_API_VERSION, WEB_SERVICE, RALLY_REST_HEADERS
from .config  import USER_NAME, PASSWORD 
from .config  import JSON_FORMAT, PAGESIZE, START_INDEX, MAX_ITEMS
from .config  import timestamp

###################################################################################################

CONJUNCTION_PATT = re.compile(' (AND|OR) ', re.I) # to allow 'and', 'or', 'AND', 'OR'

# 
# define a module global that should be set up/known before a few more module imports
#
_rallyCache = {}  # keyed by a context tuple (server, user, password, workspace, project)
                  # value is a dict with at least:
                  # a key of 'rally'    whose value there is a Rally instance  and
                  # a key of 'hydrator' whose value there is an EntityHydrator instance

#
# Yo! another module global here...
#
_allowedValueAlias = {}  # a dict keyed by entity name
                         # Project|Release|Iteration : { OID: Name value, ... }
                         # User & Owner are conspicuously not covered...

warning = sys.stderr.write

###################################################################################################

class RallyRESTAPIError(Exception): pass

#
# define a couple of entry point functions for use by other pkg modules and import the modules
#
def hydrateAnInstance(context, item, existingInstance=None):
    global _rallyCache
    rallyContext = _rallyCache.get(context, None)
    if not rallyContext:
        # throwing an Exception is probably the correct thing to do
        return None
    hydrator = rallyContext.get('hydrator', None)
    if not hydrator:
        hydrator = EntityHydrator(context, hydration="full")
        rallyContext['hydrator'] = hydrator
    return hydrator.hydrateInstance(item, existingInstance=existingInstance)

def getResourceByOID(context, entity, oid, **kwargs):
    """
        Retrieves a reference in _rallyCache to a Rally instance and uses that to 
        call its internal _getResourceByOID method
        Returns a RallyRESTResponse instance 
        that has status_code, headers and content attributes.
    """
##
##    print "getResourceByOID called:"
##    print "   context: %s" % context
##    print "    entity: %s" % entity
##    print "       oid: %s" % oid
##    print "    kwargs: %s" % kwargs
##    sys.stdout.flush()
##
##    if entity == 'context':
##        raise Exception("getResourceByOID called to get resource for entity of 'context'")
##
    global _rallyCache
    rallyContext = _rallyCache.get(context, None)
    if not rallyContext:
        # raising an Exception is the only thing we can do, don't see any prospect of recovery...
        raise RallyRESTAPIError('Unable to find Rally instance for context: %s' % context)
##
##        print "_rallyCache.keys:"
##        for key in _rallyCache.keys():
##            print "    -->%s<--" % key
##        print ""
##        print " apparently no key to match: -->%s<--" % context
##        print " context is a %s" % type(context)
    rally = rallyContext.get('rally')
    resp = rally._getResourceByOID(context, entity, oid, **kwargs)
    if 'unwrap' not in kwargs or not kwargs.get('unwrap', False):
        return resp
    response = RallyRESTResponse(rally.session, context, "%s.x" % entity, resp, "full", 1)
    return response

#  these imports have to take place after the prior class and function defs 
from .rallyresp import RallyRESTResponse, ErrorResponse
from .hydrate   import EntityHydrator
from .context   import RallyContext, RallyContextHelper

__all__ = ["Rally", "getResourceByOID", "hydrateAnInstance"]


def _createShellInstance(context, entity_name, item_name, item_ref):
    oid = item_ref[:-3].split('/').pop()
    item = {'_type' : entity_name,
            '_ref'  : item_ref, 
            'Name'  : item_name, 
            'ObjectID': oid, 
            'ref'   : '%s/%s' % (entity_name.lower(), oid)
           }
    hydrator = EntityHydrator(context, hydration="shell")
    return hydrator.hydrateInstance(item)
        

##################################################################################################

class Rally(object):
    """
        An instance of this class provides the instance holder the ability to 
        interact with Rally via the Rally REST WSAPI.
        The holder can create, query (read), update and delete Rally entities 
        (but only selected appropriate entities).
        In addition, there are several convenience methods (for users, workspaces and projects)
        that allow the holder to quickly get a picture of their Rally operating environment.
    """
    def __init__(self, server=SERVER, user=USER_NAME, password=PASSWORD, 
                       version=WS_API_VERSION, warn=True, **kwargs):
        self.server    = server
        self.user      = user
        self.password  = password
        self.version   = version
        self._inflated = False
        self.service_url = "%s://%s/%s" % (PROTOCOL, self.server, WEB_SERVICE % self.version)
        self._use_workspace_default = True
        self._use_project_default   = True
        self.hydration   = "full"
        self._log        = False
        self._logDest    = None
        self._logAttrGet = False
        self._warn       = warn
        config = {}
        if kwargs and 'debug' in kwargs and kwargs.get('debug', False):
            config['verbose'] = sys.stdout

        proxy_dict = {} 
        if 'HTTP_PROXY' in os.environ:
            proxy_dict['http_proxy'] = os.environ['HTTP_PROXY']
        if 'HTTPS_PROXY' in os.environ:
            proxy_dict['https_proxy'] = os.environ['HTTPS_PROXY']
        self.session = requests.session(headers=RALLY_REST_HEADERS, auth=(self.user, self.password), 
                                        timeout=10.0, proxies=proxy_dict, config=config)
        self.contextHelper = RallyContextHelper(self, server, user, password)
        self.contextHelper.check(self.server)

        global _rallyCache
        if self.contextHelper.currentContext() not in _rallyCache:
            _rallyCache[self.contextHelper.currentContext()] = {'rally' : self}

        if self.contextHelper.defaultContext not in _rallyCache:
            _rallyCache[self.contextHelper.defaultContext]   = {'rally' : self}

        __adjust_cache = False

        if 'workspace' in kwargs and kwargs['workspace'] != self.contextHelper.currentContext().workspace \
           and kwargs['workspace'] != 'default':
            if self.contextHelper.isAccessibleWorkspaceName(kwargs['workspace']):
                self.contextHelper.setWorkspace(kwargs['workspace'])
                self._use_workspace_default = False
                __adjust_cache = True
            else:
                 warning("WARNING: Unable to use your workspace specification, that value is not listed in your subscription\n")
                  
        if 'project' in kwargs and kwargs['project'] != self.contextHelper.currentContext().project \
           and kwargs['project'] != 'default':
            accessibleProjects = [name for name, ref in self.contextHelper.getAccessibleProjects(workspace='current')]
##
##            print "accessible projects: %s" % ", ".join(accessibleProjects)
##
            if kwargs['project'] in accessibleProjects:
                self.contextHelper.setProject(kwargs['project'])
                self._use_project_default = False
                __adjust_cache = True
            else:
                issue = ("Unable to use your project specification of '%s', " 
                         "that value is not associated with current workspace setting of: '%s'" )
                raise Exception, issue % (kwargs['project'], self.contextHelper.currentContext().workspace)

        if 'project' not in kwargs:
            #
            # It's possible that the invoker has specified a workspace but no project 
            # and the default project isn't in the workspace that was specified.
            # In that case reset the current and default project to first project in 
            # the list of projects for the current workspace.
            #
            cdp = self.contextHelper.getProject()          # cdp  alias for current_default_project
            ndp = self.contextHelper.resetDefaultProject() # ndp  alias for new_default_project
            if ndp != cdp:  # have to test both the name and ref values!!
                __adjust_cache = True
                cdp_name, cdp_ref = cdp
                ndp_name, ndp_ref = ndp
                # but we'll only issue a warning if the project names are different
                if self.warningsEnabled() and ndp_name != cdp_name:
                    prob = "WARNING: Default project changed to '%s' (%s).\n" + \
                           "         Your normal default project: '%s' is not valid for\n" +\
                           "         the current workspace setting of: '%s'\n"
                    short_proj_ref = "/".join(ndp_ref.split('/')[-2:])[:-3]
                    wksp_name, wksp_ref = self.contextHelper.getWorkspace()
                    warning(prob % (ndp_name, short_proj_ref, cdp_name, wksp_name))

        if __adjust_cache:
            _rallyCache[self.contextHelper.currentContext()] = {'rally' : self}
##
##        print "successfully intitialized a new Rally ifc ..."
##

    def _wpCacheStatus(self):
        """
            intended to be only for unit testing...
              values could be None, True, False, 'minimal', 'narrow', 'wide'
        """
        return self.contextHelper._inflated


    def serviceURL(self):
        """
            Crutch to allow the RallyContextHelper to pass this along in the initialization
            of a RallyContext instance.
        """
        return self.service_url


    def enableLogging(self, dest=sys.stdout, attrget=False, append=False):
        """
            Use this to enable logging. dest can set to the name of a file or an open file/stream (writable). 
            If attrget is set to true, all Rally REST requests that are executed to obtain attribute informatin
            will also be logged. Be careful with that as the volume can get quite large.
            The append parm controls whether any existing file will be appended to or overwritten.
        """
        self._log = True
        if hasattr(dest, 'write'):
            self._logDest = dest
        elif type(dest) == types.StringType:
            try:
                mode = 'w'
                if append:
                    mode = 'a'
                self._logDest = open(dest, mode)
            except IOError, ex:
                self._log = False
                self._logDest = None
        else:
            self._log = False
            # emit a warning that logging is disabled due to a faulty dest arg
            warning('WARNING: Logging dest arg cannot be written to, proceeding with logging disabled.\n')
        if self._log:     
            scopeNote = '%s Following entries record Rally REST API interaction via %s for user: %s' % \
                        (timestamp(), self.service_url, self.user)
            self._logDest.write('%s\n' % scopeNote)
            self._logDest.flush()
            if attrget:
                self._logAttrGet = True


    def disableLogging(self):
        """
            Disable logging. 
        """
        if self._log:
            self._log = False
            self._logAttrGet = False
            if self._logDest and self._logDest not in (sys.stdout, sys.stderr):
                try:
                    self._logDest.flush()
                    self._logDest.close()
                except IOError, ex:
                    # emit a warning that the logging destination was unable to be closed
                    pass
                self._logDest = None

    def enableWarnings(self):
        self._warn = True

    def disableWarnings(self):
        self._warn = False

    def warningsEnabled(self):
        return self._warn == True

    def subscriptionName(self):
        """
            Returns the name of the subscription in the currently active context.
        """
        return self.contextHelper.currentContext().subscription()

    def setWorkspace(self, workspaceName):
        """
            Given a workspaceName, set that as the currentWorkspace and use the ref for 
            that workspace in subsequent interactions with Rally.
        """
        if not self.contextHelper.isAccessibleWorkspaceName(workspaceName):
            raise Exception('Specified workspace not valid for your credentials')
        self.contextHelper.setWorkspace(workspaceName)

    def getWorkspace(self):
        """
            Returns a minimally hydrated Workspace instance with the Name and ref
            of the workspace in the currently active context.
        """
        context = self.contextHelper.currentContext()
        wksp_name, wksp_ref = self.contextHelper.getWorkspace()
        return _createShellInstance(context, 'Workspace', wksp_name, wksp_ref)

    def getWorkspaces(self):
        """
            Return a list of minimally hydrated Workspace instances
            that are available to the registered user in the currently active context.

            Return a list of (workspace.Name, workspace._ref) tuples
            that are available to the registered user in the currently active context.
        """
        context = self.contextHelper.currentContext()
        wkspcs = self.contextHelper.getAccessibleWorkspaces()
        workspaces = [_createShellInstance(context, 'Workspace', wksp_name, wksp_ref)
                      for wksp_name, wksp_ref in sorted(wkspcs)
                     ]
        return workspaces


    def setProject(self, projectName):
        """
            Given a projectName, set that as the current project and use the ref for 
            that project in subsequent interractions with Rally.
        """
        eligible_projects = [proj for proj,ref in self.contextHelper.getAccessibleProjects(workspace='current')]
        if projectName not in eligible_projects:
            raise Exception('Specified project not valid for your current workspace or credentials')
        self.contextHelper.setProject(projectName)

    def getProject(self):
        """
            Returns a minimally hydrated Project instance with the Name and ref
            of the project in the currently active context.
        """
        context = self.contextHelper.currentContext()
        proj_name, proj_ref = self.contextHelper.getProject()
        return _createShellInstance(context, 'Project', proj_name, proj_ref)


    def getProjects(self, workspace='default'):
        """
            Return a list of minimally hydrated Project instances
            that are available to the registered user in the currently active context.
        """
        wksp_target = workspace if workspace else 'current'
        projs = self.contextHelper.getAccessibleProjects(workspace=wksp_target)
        context = self.contextHelper.currentContext()
        projects = [_createShellInstance(context, 'Project', proj_name, proj_ref)
                      for proj_name, proj_ref in sorted(projs)
                   ]
        return projects


    def getUserInfo(self, oid=None, username=None, name=None):
        """
            A convenience method to collect specific user related information.
            Caller must provide at least one keyword arg and non-None / non-empty value
            to identify the user target on which to obtain information.
            The name     keyword arg is associated with the User.DisplayName attribute
            The username keyword arg is associated with the User.UserName attribute
            If provided, the oid keyword argument is used, even if other keyword args are 
            provided. Similarly, if the username keyword arg is provided it is used
            even if the name keyword argument is provided.
            User
                DisplayName
                UserName
                Disabled
                EmailAddress
                FirstName
                MiddleName
                LastName
                OnpremLdapUsername
                ShortDisplayName
                Role
                TeamMemberships (from projects)
                LastPasswordUpdateDate
                UserPermissions - from UserPermission items associated with this User

            UserProfile
                DefaultWorkspace
                DefaultProject
                TimeZone
                DateFormat
                DateTimeFormat
                EmailNotificationEnabled
                SessionTimeoutSeconds
                SessionTimeoutWarning

            UserPermission
                Name  - name of the User Permission
                Role

            Returns either a single User instance or a list of User instances                
                
        """
        context  = self.contextHelper.currentContext()
        item, response = None, None
        if oid:
            item = self._itemQuery('User', oid)
        elif username:
            response = self.get('User', fetch=True, query='UserName = "%s"' % username)
        elif name:
            response = self.get('User', fetch=True, query='DisplayName = "%s"' % name)
        else:
            raise RallyRESTAPIError("No specification provided to obtain User information")

        if item: 
            return item
        if response: 
            return [user for user in response]
        return None


    def getAllUsers(self, workspace=None, full=False):
        """
            Given that actually getting full information about all users in the workspace
            via the Rally WSAPI is somewhat opaque, this method offers a one-stop convenient
            means of obtaining usable information about users in the named workspace.
            If no workspace is specified, then the current context's workspace is used.

            Return a list of User instances (fully hydrated for scalar attributes)
            whose ref and collection attributes will be lazy eval'ed upon access.
        """
        saved_workspace_name, saved_workspace_ref = self.contextHelper.getWorkspace()
        if not workspace:
            workspace = saved_workspace_name
        self.setWorkspace(workspace)

        context, augments = self.contextHelper.identifyContext(workspace=workspace)
        workspace_ref = self.contextHelper.currentWorkspaceRef()

        resource = 'users.js?fetch=true&query=&pagesize=200&start=1&workspace=%s' % workspace_ref
        full_resource_url = '%s/%s' % (self.service_url, resource)

        response = self.session.get(full_resource_url)
        if response.status_code != 200:
            return []
        #TODO: what if anything should be done with full=True that isn't done now?
        response = RallyRESTResponse(self.session, context, resource, response, "full", 0)

        self.setWorkspace(saved_workspace_name)
        return [user_rec for user_rec in response]


    def _officialRallyEntityName(self, supplied_name):
        if supplied_name in ['Story', 'UserStory', 'User Story']:
            official_name = 'HierarchicalRequirement'
        else:
            official_name = supplied_name
        return official_name


    def _getResourceByOID(self, context, entity, oid, **kwargs):
        """
            The _ref URL (containing the entity name and OID) can be used unchanged but the format 
            of the response is slightly different from that returned when the resource URL is 
            constructed per spec (by this class's get method).  The _ref URL response can be 
            termed "un-wrapped" in that there's no boilerplate involved, just the JSON object.
            Returns a raw response instance (with status_code, headers and content attributes).
        """
##
##        print "in _getResourceByOID, OID specific resource ...", entity, oid
##        sys.stdout.flush()
##
        resource = '%s/%s' % (entity, oid)
        if not resource.endswith('.js'):
            resource += '.js'
        if '_disableAugments' not in kwargs:
            contextDict = context.asDict()
##
##            print "_getResourceByOID, current contextDict: %s" % repr(contextDict)
##            sys.stdout.flush()
##
            
            context, augments = self.contextHelper.identifyContext(**contextDict)
            if augments:
                resource += ("?" + "&".join(augments))
##
##            print "_getResourceByOID, modified contextDict: %s" % repr(context.asDict())
##            sys.stdout.flush()
##


        full_resource_url = "%s/%s" % (self.service_url, resource)
        if self._logAttrGet:
            self._logDest.write('%s GET %s\n' % (timestamp(), resource))
            self._logDest.flush()
##
##        print "issuing GET for resource: %s" % full_resource_url
##        sys.stdout.flush()
##
        try:
            raw_response = self.session.get(full_resource_url)
        except Exception, exc:
            exctype, value, tb = sys.exc_info()
            warning('%s: %s\n' % (exctype, value)) 
            sys.exit(9)
        return raw_response


    def _itemQuery(self, entityName, oid, workspace=None, project=None):
        """
            Internal method to retrieve a specific instance of an entity identified by the OID.
        """
##
##        print "Rally._itemQuery('%s', %s, workspace=%s, project=%s)" % (entityName, oid, workspace, project)
##
        resource = '%s/%s' % (entityName, oid)
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
        if self._log:
            self._logDest.write('%s GET %s\n' % (timestamp(), resource))
            self._logDest.flush()
        response = self._getResourceByOID(context, entityName, oid)
        if self._log:
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, resource))
            self._logDest.flush()
        if not response or response.status_code != 200:
            problem = "Unreferenceable %s OID: %s" % (entityName, oid)
            raise RallyRESTAPIError('%s %s' % (response.status_code, problem))

        response = RallyRESTResponse(self.session, context, '%s.x' % entityName, response, "full", 1)
        item = response.next()
        return item    # return back an instance representing the item


    def get(self, entity, fetch=False, query=None, order=None, **kwargs):
        """
            A REST approach has the world seen as resources with the big 4 ops available on them
            (GET, PUT, POST, DELETE). There are other ops but we don't care about them here.
            Each resource _should_ have a unique URI that is used to identify the resource.
            The GET operation is used to specify that we want a representation of that resource.
            For Rally, in order to construct a URI, we need the name of the entity, the attributes
            of the entity (and attributes on any child/parent entity related to the named entity),
            the query (selection criteria) and the order in which the results should be returned.

            The fetch argument (boolean or a comma separated list of attributes) indicates whether 
            we get complete representations of objects back or whether we get "shell" objects with 
            refs to be able to retrieve the full info at some later time.

            An optional instance=True keyword argument will result in returning an instantiated 
            Rally Entity if and only if the resultCount of the get is exactly equal to 1.
            Otherwise, a RallyRESTResponse instance is returned.

            All optional keyword args:
                fetch=True/False or "List,Of,Attributes,We,Are,Interested,In"
                query='FieldName = "some value"' or ['fld1 = 19', 'fld27 != "Shamu"', etc.]
                instance=False/True
                pagesize=n
                start=n
                limit=n
                projectScopeUp=True/False
                projectScopeDown=True/False
        """
        # TODO: this method too long, break into small setup, 2 or 3 subcalls and some wrapup
        # set some useful defaults...
        pagesize   = PAGESIZE
        startIndex = START_INDEX
        limit      = MAX_ITEMS

        if kwargs and 'pagesize' in kwargs:
            pagesize = kwargs['pagesize']

        if kwargs and 'start' in kwargs:
            try:
                usi = int(kwargs['start'])  # usi - user supplied start index
                if 0 < usi < MAX_ITEMS:     # start index must be greater than 0 and less than max
                    startIndex = usi
            except ValueError, e: 
                pass

        if kwargs and 'limit' in kwargs:
            try:
                ulimit = int(kwargs['limit'])  # in case someone specifies something like limit=gazillionish
                limit = min(ulimit, MAX_ITEMS)
            except:
                pass

        if fetch == True:
            fetch = 'true'
            self.hydration = "full"
        elif fetch == False:
            fetch = 'false'
            self.hydration = "shell"
        elif type(fetch) == types.StringType and fetch.lower() != 'false':
            self.hydration = "full"
        elif type(fetch) in [types.ListType, types.TupleType]:
            fetch = ",".join(fetch)
            self.hydration = "full"

        entity = self._officialRallyEntityName(entity)
        resource = RallyUrlBuilder(entity)
        resource.qualify(fetch, query, order, pagesize, startIndex)

        if '_disableAugments' in kwargs:
            context = RallyContext(self.server, self.user, self.password, self.service_url)
        else:
            context, augments = self.contextHelper.identifyContext(**kwargs)
            workspace_ref = self.contextHelper.currentWorkspaceRef()
            project_ref   = self.contextHelper.currentProjectRef()
            if workspace_ref:
                resource.augmentWorkspace(augments, workspace_ref, self._use_workspace_default)
                if project_ref:
                    resource.augmentProject(augments, project_ref, self._use_project_default)
                    resource.augmentScoping(augments)
        resource = resource.build()  # can also use resource = resource.build(pretty=True)
        full_resource_url = "%s/%s" % (self.service_url, resource)

        # TODO: see if much of above can be pushed into another method

        if self._log: 
            self._logDest.write('%s GET %s\n' % (timestamp(), resource))
            self._logDest.flush()

        response = None  # in case an exception gets raised in the session.get call ...
        try:
            # a response has status_code, content and data attributes
            # the data attribute is a dict that has a single entry for the key 'QueryResult' 
            # or 'OperationResult' whose value is in turn a dict with values of 
            # 'Errors', 'Warnings', 'Results'
            response = self.session.get(full_resource_url)
        except Exception, exc:
            if response:
##
##               print response.status_code
##
                ret_code, content = response.status_code, response.content
            else:
                ret_code, content = 404, str(exc)
            if self._log:
                self._logDest.write('%s %s\n' % (timestamp(), ret_code))
                self._logDest.flush()
            errorResponse = ErrorResponse(ret_code, content)
            response = RallyRESTResponse(self.session, context, resource, errorResponse, self.hydration, 0)
            return response
##
##        print "response.status_code is %s" % response.status_code
##
        if response.status_code != 200:
            if self._log:
                code, verbiage = response.status_code, response.content[:56]
                self._logDest.write('%s %s %s ...\n' % (timestamp(), code, verbiage))
                self._logDest.flush()
##
##            print response
##
            #if response.status_code == 404:
            #    problem = "%s Service unavailable from %s, check for proper hostname" % (response.status_code, self.service_url)
            #    raise Exception(problem)
            errorResponse = ErrorResponse(response.status_code, response.content)
            response = RallyRESTResponse(self.session, context, resource, errorResponse, self.hydration, 0)
            return response

        response = RallyRESTResponse(self.session, context, resource, response, self.hydration, limit)
        if self._log:
            if response.status_code == 200:
                desc = '%s TotalResultCount %s' % (entity, response.resultCount)
            else:
                desc = response.errors[0]
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, desc))
            self._logDest.flush()
        if kwargs and 'instance' in kwargs and kwargs['instance'] == True and response.resultCount == 1:
            return response.next()
        return response

    find = get # offer interface approximately matching Ruby Rally REST API, App SDK Javascript RallyDataSource


    def put(self, entityName, itemData, workspace=None, project=None, **kwargs):
        """
            Return the newly created target entity item
        """
        entityName = self._officialRallyEntityName(entityName)
        resource = "%s/create.js" % entityName.lower()
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("&" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
        item = {entityName: itemData}
        payload = json.dumps(item)
        if self._log:
            self._logDest.write('%s PUT %s\n%27.27s %s\n' % (timestamp(), resource, " ", payload))
            self._logDest.flush()
        response = self.session.put(full_resource_url, data=payload, headers=RALLY_REST_HEADERS)
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.status_code != 200:
            desc = response.errors[0]
            if self._log:
                self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, desc))
                self._logDest.flush()
            raise RallyRESTAPIError('%s %s' % (response.status_code, desc))

        result = response.content
        item = result[u'CreateResult'][u'Object']
        ref = str(item[u'_ref'])
        item_oid = int(ref.split('/')[-1][:-3])
        desc = "created %s OID: %s" % (entityName, item_oid)
        if self._log:
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, desc))
            self._logDest.flush()

        # now issue a request to get the entity item (mostly so we can get the FormattedID)
        # and return it
        item = self._itemQuery(entityName, item_oid, workspace=workspace, project=project)
        return item
        
    create = put  # a more intuitive alias for the operation


    def post(self, entityName, itemData, workspace=None, project=None, **kwargs):
        entityName = self._officialRallyEntityName(entityName)

        oid = itemData.get('ObjectID', None)
        if not oid:
            formattedID = itemData.get('FormattedID', None)
            if not formattedID:
                raise RallyRESTAPIError('An identifying field (Object or FormattedID) must be specified')
            fmtIdQuery = 'FormattedID = "%s"' % formattedID
            response = self.get(entityName, fetch="ObjectID", query=fmtIdQuery, 
                                workspace=workspace, project=project)
            if response.status_code != 200:
                raise RallyRESTAPIError('Target %s %s could not be located' % (entityName, formattedID))
                
            target = response.next()
            oid = target.ObjectID
##
##            print "target OID: %s" % oid
##
            itemData['ObjectID'] = oid

        resource = '%s/%s.js' % (entityName.lower(), oid) 
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("&" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
##
##        print "resource: %s" % resource
##
        item = {entityName: itemData}
        payload = json.dumps(item)
        if self._log:
            self._logDest.write('%s POST %s\n%27.27s %s\n' % (timestamp(), resource, " ", item))
            self._logDest.flush()
        response = self.session.post(full_resource_url, data=payload, headers=RALLY_REST_HEADERS)
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.status_code != 200:
            raise RallyRESTAPIError('Unable to update the %s' % entityName)

        # now issue a request to get the entity item (mostly so we can get the FormattedID)
        # and return it
        item = self._itemQuery(entityName, oid, workspace=workspace, project=project)
        return item

    update = post  # a more intuitive alias for the operation


    def delete(self, entityName, itemIdent, workspace=None, project=None, **kwargs):
        entityName = self._officialRallyEntityName(entityName)
        # guess at whether itemIdent is an ObjectID or FormattedID via 
        # regex matching (all digits or 1-2 upcase chars + digits)
        objectID = itemIdent  # at first assume itemIdent is the ObjectID
        if re.match('^[A-Z]{1,2}\d+$', itemIdent):
            fmtIdQuery = 'FormattedID = "%s"' % itemIdent
            response = self.get(entityName, fetch="ObjectID", query=fmtIdQuery, 
                                workspace=workspace, project=project)
            if response.status_code != 200:
                raise RallyRESTAPIError('Target %s %s could not be located' % (entityName, itemIdent))
                
            target = response.next()
            objectID = target.ObjectID
##
##            if kwargs.get('debug', False):
##               print "DEBUG: target OID -> %s" % objectID
##
        resource = "%s/%s.js" % (entityName.lower(), objectID)
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
        if self._log:
            self._logDest.write('%s DELETE %s\n' % (timestamp(), resource))
        response = self.session.delete(full_resource_url, headers=RALLY_REST_HEADERS)
        if response and response.status_code != 200:
            if self._log:
                self._logDest.write('%s %s %s ...\n' % \
                       (timestamp(), response.status_code, response.content[:56]))
                self._logDest.flush()
##
##            if kwargs.get('debug', False):
##                print response
##
            errorResponse = ErrorResponse(response.status_code, response.content)
            response = RallyRESTResponse(self.session, context, resource, errorResponse, self.hydration, 0)
            problem = "ERRORS: %s\nWARNINGS: %s\n" % ("\n".join(response.errors), 
                                                      "\n".join(response.warnings))
            raise RallyRESTAPIError(problem)

##
##        print response.content
##
        response = RallyRESTResponse(self.session, context, resource, response, "shell", 0)
        if response.errors:
            status = False
            desc = response.errors[0]
        else:
            status = True
            desc = '%s deleted' % entityName
        if self._log:
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, desc))
            self._logDest.flush()

        return status


    def allowedValueAlias(self, entity, refUrl):
        """
            use the _allowedValueAlias as a cache. A cache hit results from 
            having an entity key in _allowedValueAlias AND and entry for the OID 
            contained in the refUrl, the return is the OID and the alias value.
            If there is no cache hit for the entity, issue a GET against
            self.service_url/<entity>.js?fetch=ObjectID,Name (or UserName,DisplayName)
        """
        urlFields = refUrl.split('/')
        oid = urlFields.pop()
        result = (oid, "--UNKNOWN OID--")
        actualEntity = urlFields.pop().lower()  # this may be different from entity, eg.
                                                # entity=SubmittedBy, actualEntity=User
        if actualEntity == 'user':    # special case processing for user follows...
            if actualEntity not in _allowedValueAlias:
                _allowedValueAlias[actualEntity] = {}
            cache = _allowedValueAlias[actualEntity]
            if oid in cache:
                result = (oid, cache[oid])
            else:
                item = self._itemQuery(actualEntity, oid)   # query against 'User' for item
                cache[oid] = (item.DisplayName, item.UserName)
                result = (oid, (item.DisplayName, item.UserName))
        else:   # normal case, entity == actualEntity (or at least no functional difference)
            hydrationSetting = self.hydration
            self.hydrate = "shell"

            if entity not in _allowedValueAlias:
                _allowedValueAlias[entity] = {}
            cache = _allowedValueAlias[entity]
            if oid in cache:
               result = (oid, cache[oid])
            else:
                fields = "ObjectID,Name"
                response = self.get(entity, fetch=fields, pagesize=200) # query for all items in entity
                for item in response:
                    cache[item.oid] = item.Name
                if oid in cache:
                    result = (oid, cache[oid])

            self.hydration = hydrationSetting

        return result


    def getAllowedValues(self, entityName, attributeName, **kwargs):
        """
            Given an entityName and and attributeName (assumed to be valid for the entityName)
            issue a request to obtain a list of allowed values for the attribute.
        """
        # get rid of any pesky spaces in the attributeName
        attrName = attributeName.replace(' ', '')
        resource = '%s/%s/allowedValues.js' % (entityName, attrName)
        context, augments = self.contextHelper.identifyContext(**kwargs)
        if augments:
            resource += ("?" + "&".join(augments))
        full_resource_url = "%s/%s" % (self.service_url, resource)
        if self._log:
            self._logDest.write('%s GET %s\n' % (timestamp(), resource))
            self._logDest.flush()
        try:
            response = self.session.get(full_resource_url, headers=RALLY_REST_HEADERS)
        except Exception, exc:
            exception_type, value, traceback = sys.exc_info()
            warning('%s: %s\n' % (exception_type, value)) 
            sys.exit(9)

        if self._log:
            self._logDest.write('%s %s %s\n' % (timestamp(), response.status_code, resource))
            self._logDest.flush()
        if not response or response.status_code != 200:
            problem = "AllowedValues unobtainable for %s.%s" % (entityName, attrName)
            raise RallyRESTAPIError('%s %s' % (response.status_code, problem))

        try:
            allowed_values_dict = json.loads(response.content)
            return allowed_values_dict
        except Exception, msg:
            print "Unable to decode the json.loads target"
            print msg
            return None

##################################################################################################

class RallyUrlBuilder(object):
    """
        An instance of this class is used to collect information needed to construct a
        valid URL that can be issued in a REST Request to Rally.
        The sequence of use is to obtain a RallyUrlBuilder for a named entity, 
        provide qualifying criteria, augments, scoping criteria and any provision 
        for a pretty response, and then call build to return the resulting resource URL.
        An instance can be re-used (for the same entity) by simply re-calling the 
        specification methods with differing values and then re-calling the build method.
    """
    parts = ['fetch', 'query', 'order', 
             'workspace', 'project', 'projectScopeUp', 'projectScopeDown', 
             'pagesize', 'start', 'pretty'
            ]

    def __init__(self, entity):
        self.entity = entity

    def qualify(self, fetch, query, order, pagesize, startIndex):
        self.fetch = fetch
        self.query = query
        self.order = order
        self.pagesize   = pagesize
        self.startIndex = startIndex
        self.workspace  = None
        self.project    = None
        self.scopeUp    = None
        self.scopeDown  = None
        self.pretty     = False
            

    def build(self, pretty=None):
        if pretty:
            self.pretty = True
        
        resource = "%s%s?" % (self.entity, JSON_FORMAT)

        qualifiers = ['fetch=%s' % self.fetch]
        if self.query:
            encodedQuery = self._prepQuery(self.query)
            qualifiers.append('%s=(%s)' % ('query', encodedQuery if encodedQuery else ""))
        if self.order:
            qualifiers.append("order=%s" % urllib.quote(self.order))
        if self.workspace:
            qualifiers.append(self.workspace)
        if self.project:
            qualifiers.append(self.project)
        if self.scopeUp:
            qualifiers.append(self.scopeUp)
        if self.scopeDown:
            qualifiers.append(self.scopeDown)

        qualifiers.append('pagesize=%s' % self.pagesize)
        qualifiers.append('start=%s'    % self.startIndex)

        if self.pretty:
            qualifiers.append('pretty=true')

        resource += ("&" + "&".join(qualifiers))
        return resource


    def _prepQuery(self, query):
        if not query:
            return None

        def _encode(condition):
            """
                if cond has pattern of 'thing relation value', then urllib.quote it and return it
                if cond has pattern of '(thing relation value)', then urllib.quote content inside parens
                  then pass that result enclosed in parens back to the caller
            """
            if condition[0] == '(' and condition[-1] == ')':
                return '(%s)' % urllib.quote(condition[1:-1])
            else:
                return urllib.quote(condition)

        if type(query) in [types.StringType, types.UnicodeType]:
            if ' AND ' not in query and ' OR ' not in query and ' and ' not in query and ' or ' not in query:
                return urllib.quote(query)
            else:  # do a regex split using ' AND|OR ' then urllib.quote the individual conditions
                CONJUNCTIONS = ['and', 'or', 'AND', 'OR']
                parts = CONJUNCTION_PATT.split(query)
                parts = [p if p in CONJUNCTIONS else _encode(p) for p in parts]
                return "%20".join(parts)
        elif type(query) in [types.ListType, types.TupleType]:
            # by fiat (and until requested by a paying customer), we assume the conditions are AND'ed
            parts = ['(%s)' % _encode(condition) for condition in query] 
            return "%20AND%20".join(parts)
        elif type(query) == types.DictType:  # wow! look at this wildly unfounded assumption about what to do!
            parts = []
            for field, value in query.items():
                # have to enclose string value in double quotes, otherwise turn whatever the value is into a string
                tval = '"%s"' % value if type(value) == types.StringType else '%s' % value
                parts.append('(%s)' % urllib.quote('%s = %s' % (field, tval)))
            return "%20AND%20".join(parts)

        return None


    def augmentWorkspace(self, augments, workspace_ref, use_default):
        wksp_augment = [aug for aug in augments if aug.startswith('workspace=')]
        if wksp_augment:
            self.workspace = wksp_augment[0]
        if not use_default:
            self.workspace = "workspace=%s" % workspace_ref


    def augmentProject(self, augments, project_ref,  use_default):
        proj_augment = [aug for aug in augments if aug.startswith('project=')]
        if proj_augment:
            self.project = proj_augment[0]
        if not use_default:
            self.project = "project=%s" % project_ref

    def augmentScoping(self, augments):
        scopeUp   = [aug for aug in augments if aug.startswith('projectScopeUp=')]
        if scopeUp:
            self.scopeUp = scopeUp[0]
        scopeDown = [aug for aug in augments if aug.startswith('projectScopeDown=')]
        if scopeDown:
            self.scopeDown = scopeDown[0]

    def beautifyResponse(self):
        self.pretty = True

##################################################################################################

class RallyQueryFormatter(object):
    CONJUNCTIONS = ['and', 'AND', 'or', 'OR']
    CONJUNCTION_PATT = re.compile('\s+(AND|OR)\s+', re.I | re.M)

    @staticmethod
    def parenGroups(condition):
        """
            Keep in mind that Rally WSAPI only supports a binary condition of (x) op (y)
            as in "(foo) and (bar)"
            or     (foo) and ((bar) and (egg))  
            Note that Rally doesn't handle (x and y and z) directly.
            Look at the condition to see if there are any parens other than begin and end 
            if the only parens are at begin and end, strip them and subject the condition to our
            clause grouper and binary condition confabulator. 
            Otherwise, we'll naively assume the caller knows what they are doing, ie., they are 
            aware of the binary condition requirement.
        """
        # if the caller has a simple query in the form "(something = a_value)"
        # then return the query as is (after stripping off the surrounding parens)
        if     condition.count('(')  == 1   \
           and condition.count(')')  == 1   \
           and condition.strip()[0]  == '(' \
           and condition.strip()[-1] == ')':
            return condition.strip()[1:-1]
       
        # if caller has more than one opening paren, summarily return the query 
        # essentially untouched.  The assumption is that the caller has correctly
        # done the parenthisized grouping to end up in a binary form
        if condition.count('(') > 1:
            return condition.strip()

        parts = RallyQueryFormatter.CONJUNCTION_PATT.split(condition.strip())
        
        # if no CONJUNCTION is in parts, use the condition as is (simple case)
        conjunctions = [p for p in parts if p in RallyQueryFormatter.CONJUNCTIONS]
        if not conjunctions:
            return condition.strip()

        binary_condition = parts.pop()
        while parts:
            item = parts.pop()
            if item in RallyQueryFormatter.CONJUNCTIONS:
                conj = item
                binary_condition = "%s (%s)" % (conj, binary_condition)
            else:
                cond = item
                binary_condition = "(%s) %s" % (cond, binary_condition)

        return binary_condition

##################################################################################################

#!/opt/local/bin/python2.6

###################################################################################################
#
#  pyral.restapi - Python Rally REST API module
#          round 9 version with GET, PUT, POST and DELETE operations, support multiple instances
#             adding support for Attachments to Artifact
#          notable dependencies:
#               requests v0.9.3 recommended (0.10.x no longer works for Python 2.5)
#
###################################################################################################

__version__ = (0, 9, 2)

import sys, os
import re
import types
import time
import urllib
import json
import string
import base64

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
# another module global for TypeDefinition info
#  it's intended to be able to access a TypeDefinition.ref , .ElementName, and .Name attrs only
#
_type_definition_cache = {} # keyed by a type of context info and type definition ElementName
                            # value is a minimally hydrated TypeDefinition instance

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
##
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
from .entity    import validRallyType

__all__ = ["Rally", "getResourceByOID", "hydrateAnInstance", "RallyUrlBuilder"]


def _createShellInstance(context, entity_name, item_name, item_ref):
    if item_ref.endswith('.js'):
        oid = item_ref[:-3].split('/').pop()
    else:
        oid = item_ref.split('/').pop()
    item = {
            'ObjectID' : oid, 
            'Name'     : item_name, 
            '_type'    : entity_name,
            '_ref'     : item_ref, 
            'ref'      : '%s/%s' % (entity_name.lower(), oid)
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
    ARTIFACT_TYPE = { 'S' : 'Story', 
                     'US' : 'Story', 
                     'DE' : 'Defect',
                     'DS' : 'DefectSuite',
                     'TA' : 'Task',
                     'TC' : 'TestCase',
                     'TS' : 'TestSet',
                     'PI' : 'PortfolioItem'
                    }
    FORMATTED_ID_PATTERN = re.compile(r'^[A-Z]{1,2}\d+$')
                                      #S|US|DE|DS|TA|TC|TS|PI
    MAX_ATTACHMENT_SIZE = 5000000  # approx 5MB 


    def __init__(self, server=SERVER, user=USER_NAME, password=PASSWORD, 
                       version=WS_API_VERSION, warn=True, **kwargs):
        self.server    = server
        self.user      = user
        self.password  = password
        self.version   = version
        self._inflated = False
        self.service_url = "%s://%s/%s" % (PROTOCOL, self.server, WEB_SERVICE % self.version)
        self.hydration   = "full"
        self._log        = False
        self._logDest    = None
        self._logAttrGet = False
        self._warn       = warn
        config = {}
        if kwargs and 'debug' in kwargs and kwargs.get('debug', False):
            config['verbose'] = sys.stdout

        credentials = requests.auth.HTTPBasicAuth(self.user, self.password)
        proxy_dict = {} 
        https_proxy = os.environ.get('HTTPS_PROXY', None) or os.environ.get('https_proxy', None)
        if https_proxy and https_proxy not in ["", None]:
            proxy_dict['https'] = https_proxy
        
        verify_ssl_cert = True
        if kwargs and 'verify_ssl_cert' in kwargs:
            vsc = kwargs.get('verify_ssl_cert')
            if vsc in [False, True]:
                verify_ssl_cert = vsc

        self.session = requests.session(headers=RALLY_REST_HEADERS, auth=credentials,
                                        timeout=10.0, proxies=proxy_dict, 
                                        verify=verify_ssl_cert, config=config)
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
                __adjust_cache = True
            else:
                 warning("WARNING: Unable to use your workspace specification, that value is not listed in your subscription\n")
                  
        if 'project' in kwargs and kwargs['project'] != self.contextHelper.currentContext().project \
           and kwargs['project'] != 'default':
            accessibleProjects = [name for name, ref in self.contextHelper.getAccessibleProjects(workspace='current')]

            if kwargs['project'] in accessibleProjects:
                self.contextHelper.setProject(kwargs['project'])
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
##
##        print self.contextHelper.currentContext()
##

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
        wkspcs  = self.contextHelper.getAccessibleWorkspaces()
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


    def getProject(self, name=None):
        """
            Returns a minimally hydrated Project instance with the Name and ref
            of the project in the currently active context if the name keyword arg
            is not supplied or the Name and ref of the project identified by the name
            as long as the name identifies a valid project in the currently selected workspace.
            Returns None if a name parameter is supplied that does not identify a valid project
            in the currently selected workspace.
        """
        context = self.contextHelper.currentContext()
        if not name:
            proj_name, proj_ref = self.contextHelper.getProject()
            return _createShellInstance(context, 'Project', proj_name, proj_ref)
        projs = self.contextHelper.getAccessibleProjects(workspace='current')
        hits = [(proj,ref) for proj,ref in projs if str(proj) == str(name)]
        if not hits:
            return None
        tp = projs[0]
        tp_ref = tp[1]
        return _createShellInstance(context, 'Project', name, tp_ref)
        

    def getProjects(self, workspace=None):
        """
            Return a list of minimally hydrated Project instances
            that are available to the registered user in the currently active context.
        """
        wksp_target = workspace or 'current'
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


    def getAllUsers(self, workspace=None):
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
        response = RallyRESTResponse(self.session, context, resource, response, "full", 0)

        self.setWorkspace(saved_workspace_name)
        return [user_rec for user_rec in response]


    def _officialRallyEntityName(self, supplied_name):
        if supplied_name in ['Story', 'UserStory', 'User Story']:
            supplied_name = 'HierarchicalRequirement'

        # here's where we'd make an inquiry into entity to see if the supplied_name
        # is a Rally entity on which CRUD ops are permissible.
        # An Exception is raised if not.
        # If supplied_name resolves in some way to a valid Rally entity,
        # this returns either a simple name or a TypePath string (like PortfolioItem/Feature)
        official_name = validRallyType(self, supplied_name)
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
            return None
##
##        print raw_response: %s" % raw_response
##        sys.stdout.flush()
##
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
##
##            print "   workspace_ref: %s"   % workspace_ref
##            print "     project_ref:   %s" %   project_ref
##
            if workspace_ref:   # TODO: would we ever _not_ have a workspace_ref?
                if 'workspace' not in kwargs or ('workspace' in kwargs and kwargs['workspace'] is not None):
                    resource.augmentWorkspace(augments, workspace_ref)
                    if project_ref:
                        if 'project' not in kwargs or ('project' in kwargs and kwargs['project'] is not None):
                            resource.augmentProject(augments, project_ref)
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
##                print response.status_code
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


    def put(self, entityName, itemData, workspace='current', project='current', **kwargs):
        """
            Given a Rally entityName, a dict with data that the newly created entity should contain,
            issue the REST call and return the newly created target entity item.
        """
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)

        resource = "%s/create.js" % entityName.lower()
        context, augments = self.contextHelper.identifyContext(workspace=workspace, project=project)
        if augments:
            resource += ("?" + "&".join(augments))
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


    def post(self, entityName, itemData, workspace='current', project='current', **kwargs):
        """
            Given a Rally entityName, a dict with data that the entity should be updated with,
            issue the REST call and return a representation of updated target entity item.
        """
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

        entityName = self._officialRallyEntityName(entityName)

        oid = itemData.get('ObjectID', None)
        if not oid:
            formattedID = itemData.get('FormattedID', None)
            if not formattedID:
                raise RallyRESTAPIError('An identifying field (Object or FormattedID) must be specified')
            fmtIdQuery = 'FormattedID = "%s"' % formattedID
            response = self.get(entityName, fetch="ObjectID", query=fmtIdQuery, 
                                workspace=workspace, project=project)
            if response.status_code != 200 or response.resultCount == 0:
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
            resource += ("?" + "&".join(augments))
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


    def delete(self, entityName, itemIdent, workspace='current', project='current', **kwargs):
        """
            Given a Rally entityName, an identification of a specific Rally instnace of that 
            entity (in either OID or FormattedID format), issue the REST DELETE call and 
            return an indication of whether the delete operation was successful.
        """
        # see if we need to transform workspace / project values of 'current' to actual
        if workspace == 'current':
            workspace = self.getWorkspace().Name  # just need the Name here
        if project == 'current':
            project = self.getProject().Name  # just need the Name here

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
##                print response.status_code, response.headers, response.content
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

    def typedef(self, target_type):
        """
            Given the name of a target Rally type definition return an instance 
            of a TypeDefinition class matching the target.  Cache the TypeDefinition
            for the context so that repeated calls to the same target_type only result
            in one call to Rally.
        """
        ctx  = self.contextHelper.currentContext()
        td_key = (ctx.server, ctx.subs_name, ctx.workspace, ctx.project, target_type)
        if td_key not in _type_definition_cache:
            td = self.get('TypeDefinition', fetch='ElementName,Name,Parent,TypePath',
                                            query='ElementName = "%s"' % target_type,
                                            instance=True)
            if not td:
                raise Exception, "Invalid Rally entity name: %s" % target_type
            _type_definition_cache[td_key] = td
        return _type_definition_cache[td_key]

    def getState(self, entity, state_name):
        """
            State is now (Sep 2012) a Rally type (aka entity) not a String.
            In order to somewhere insulate pyral package users from the increased complexity 
            of that approach, this is a convenience method that given a target entity (like
            Defect, PortfolioItem/<subtype>, etc.) and a state name, an inquiry to the Rally
            system is executed and the matching entity is returned.
        """
        criteria = [ 'TypeDef.Name = "%s"' % entity,
                     'Name = "%s"'         % state_name
                   ]

        state = self.get('State', fetch=True, query=criteria, project=None, instance=True)
        return state

    def getStates(self, entity):
        """
        """
        response = self.get('State', query='TypeDef.Name = "%s"' % entity, project=None)
        return [item for item in response]

    def allowedValueAlias(self, entity, refUrl):
        """
            Use the _allowedValueAlias as a cache. A cache hit results from 
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


    def addAttachment(self, artifact, filename, mime_type='text/plain'):
        """
            Given an artifact (actual or FormattedID for an artifact), validate
            that it exists and then attempt to add an Attachment with the name and
            contents of filename into Rally and associate that Attachment 
            with the Artifact.
            Upon the successful creation of the Attachment and linkage to the artifact,
            return an instance of the succesfully added Attachment.
            Exceptions are raised for other error conditions, such as the filename
            identified by the filename parm not existing, or not being a file, or the 
            attachment file exceeding the maximum allowed size, or failure
            to create the AttachmentContent or Attachment.
           
        """
        # determine if artifact exists, if not short-circuit False
        # determine if attachment already exists for filename (with same size and content)
        #   if so, and already attached to artifact, short-circuit True
        #   if so, but not attached to artifact, save attachment
        #   if not, create the AttachmentContent with filename content, 
        #           create the Attachment with basename for filename and ref the AttachmentContent 
        #              and supply the ref for the artifact in the Artifact field for Attachment
        #          
        if not os.path.exists(filename):
            raise Exception('Named attachment filename: %s not found' % filename)
        if not os.path.isfile(filename):
            raise Exception('Named attachment filename: %s is not a regular file' % filename)

        attachment_file_name = os.path.basename(filename)
        attachment_file_size = os.path.getsize(filename)
        if attachment_file_size > self.MAX_ATTACHMENT_SIZE:
            raise Exception('Attachment file size too large, unable to attach to Rally Artifact')
            
        art_type, artifact = self._realizeArtifact(artifact)
        if not art_type:
            return False

        current_attachments = [att for att in artifact.Attachments]

        response = self.get('Attachment', fetch=True, query='Name = "%s"' % attachment_file_name)
        if response.resultCount:
            attachment = response.next()
            already_attached = [att for att in current_attachments if att.oid == attachment.oid]
            if already_attached:
                return already_attached[0]

        contents = ''
        with open(filename, 'r') as af:
            contents = base64.encodestring(af.read())
            
        # create an AttachmentContent item
        ac = self.create('AttachmentContent', {"Content" : contents}, project=None)
        if not ac:
            raise RallyRESTAPIError('Unable to create AttachmentContent for %s' % attachment_file_name)

        
        attachment_info = { "Name"        :  attachment_file_name,
                            "Content"     :  ac.ref,       # ref to AttachmentContent
                            "ContentType" :  mime_type,    
                            "Size"        :  attachment_file_size, # must be size before encoding!!
                            "User"        :  'user/%s' % self.contextHelper.user_oid,
                           #"Artifact"    :  artifact.ref  # (Artifact is an 'optional' field)
                          }
        # While it's actually possible to have an Attachment not linked to an Artifact,
        # in most cases, it'll be far more useful to have the linkage to an Artifact than not.
        if artifact:  
            attachment_info["Artifact"] = artifact.ref

        # and finally, create the Attachment
        attachment = self.create('Attachment', attachment_info, project=None)
        if not attachment:
            raise RallyRESTAPIError('Unable to create Attachment for %s' % attachment_file_name)

        return attachment


    def addAttachments(self, artifact, attachments):
        """
            Attachments must be a list of dicts, with each dict having key-value
            pairs for Name, MimeType (or mime_type or content_type or ContentType), Content
        """
        candidates = []
        attached   = []
        for attachment in attachments:
            att_name = attachment.get('Name', None)
            if not att_name:
                continue
            ct_item =     attachment.get('mime_type',    None) or attachment.get('MimeType',    None) \
                      or  attachment.get('content_type', None) or attachment.get('ContentType', None)
            if not ct_item:
                print "Bypassing attachment for %s, no mime_type/ContentType setting..." % att_name
                continue
            candidates.append(att_name)
            upd_artifact = self.addAttachment(artifact, att_name, mime_type=ct_item)
            if upd_artifact:
                attached.append(att_name)
        return len(attached) == len(candidates)


    def getAttachment(self, artifact, filename):
        """
            Given a real artifact instance or the FormattedID of an existing artifact,
            obtain the attachment named by filename.  If there is such an attachment,
            return an Attachment instance with hydration for  Name, Size, ContentType, Content, 
            CreationDate and the User that supplied the attachment.
            If no such attachment is present, return None
        """
        art_type, artifact = self._realizeArtifact(artifact)
        if not art_type:
            return False

        current_attachments = [att for att in artifact.Attachments]
        hits = [att for att in current_attachments if att.Name == filename]
        if not hits:
            return None
        att = hits.pop(0)
        if not att._hydrated:
            getattr(att, 'Description')  # forces the hydration to occur

        # For reasons that are unclear, a "normal" pyral GET on 'AttachmentContent' comes 
        # back as empty even if the specific OID for an AttachmentContent item exists.
        # The target URL of the GET has to be constructed in a particular manner.
        # Fortunately, our _getResourceByOID method fills this need.  
        # But, we have to turn the raw response into a RallyRESTResponse ourselves here.

        context, augments = self.contextHelper.identifyContext()
        resp = self._getResourceByOID(context, 'AttachmentContent', att.Content.oid, project=None)
        if resp.status_code not in [200, 201, 202]:
            return None

        response = RallyRESTResponse(self.session, context, "AttachmentContent.x", resp, "full", 1)
        if response.errors or response.resultCount != 1:
            return None
        att_content = response.next()
        att.Content = base64.decodestring(att_content.Content)  # maybe further txfm to Unicode ?
        return att


    def getAttachmentNames(self, artifact):
        """
            For the given Artifact, return the names (filenames) of the Attachments
        """
        names = []
        if artifact.Attachments:
            names = [att.Name for att in artifact.Attachments]
        return names
        

    def getAttachments(self, artifact):
        """
            For the given Artifact, return a list of Attachment records.
            Each Attachment record will look like a Rally WSAPI Attachment with
            the additional Content attribute that will contain the decoded AttachmentContent.
        """
        attachment_names = self.getAttachmentNames(artifact)
        attachments = [self.getAttachment(artifact, attachment_name) for attachment_name in attachment_names]
        attachments = [att for att in attachments if att is not None]
        return attachments


    def __disabled__deleteAttachment(self, artifact, filename):
        """
            Unfortunately, at this time (WSAPI 1.34+) while AttachmentContent items can be deleted,
            Attachment items cannot.  So, exposing this method would offer very limited utility.
        """
        return False

        art_type, artifact = self._realizeArtifact(artifact)
        if not art_type:
            return False

        current_attachments = [att for att in artifact.Attachments]
        hits = [att for att in current_attachments if att.Name == filename]
        if not hits:
            return False

        # get the target Attachment and the associated AttachmentContent item
        attachment = hits.pop(0)
        print attachment.details()
        if attachment.Content and attachment.Content.oid:
            success = self.delete('AttachmentContent', attachment.Content.oid, project=None)
##
##            print "deletion attempt on AttachmentContent %s succeeded? %s" % (attachment.Content.oid, success)
##
            if not success:
                print "Panic!  unable to delete AttachmentContent item for %s" % attachment.Name
                return False

#        # Squeamishness about the drawbacks of deleting certain entities in Rally has
#        # sloshed into the Attachment realm, so can't actually do a delete of an Attachment.
#### 2012-09-24  re-attempt to delete an Attachment with Rally WSAPI 1.37
####             attempt failed, no Exception raised, but Attachment not deleted...
####
#        #deleted = self.delete('Attachment', attachment.oid, project=None)
#
#        # But, we can still just not include the targeted Attachment here from 
#### 2012-09-20  in fact, this is now dysfunctional also as of WSAPI 1.37 backward incompatible changes
#        # being included in the list of Attachments for our target artifact
#        remaining_attachments = [att for att in current_attachments if att.ref != attachment.ref]
#        att_refs = [dict(_ref=str(att.ref)) for att in remaining_attachments]
#        artifact_info = { 'ObjectID'    : artifact.ObjectID,
#                          'Attachments' : att_refs,
#                        }
#        updated = self.update(art_type, artifact_info, project=None)
#        if updated:
#            return updated
#        else: 
#            return False


    def _realizeArtifact(self, artifact):
        """
            Helper method to identify the artifact type and to retrieve it if the 
            artifact value is a FormattedID. If the artifact is already an instance
            of a Rally entity, then all that needs to be done is deduce the art_type
            from the class name.  If the artifact argument given is neither of those 
            two conditions, return back a 2 tuple of (False, None).
            Once you have an Rally instance of the artifact, return back a 
            2 tuple of (art_type, artifact)
        """
        art_type = False
        if 'pyral.entity.' in str(type(artifact)):
            # we've got the artifact already...
            art_type = artifact.__class__.__name__
        elif self.FORMATTED_ID_PATTERN.match(artifact): 
            # artifact is a potential FormattedID value
            prefix = artifact[:2]
            if prefix[1] in string.digits:
                prefix = prefix[0]
            art_type = self.ARTIFACT_TYPE[prefix]
            response = self.get(art_type, fetch=True, query='FormattedID = %s' % artifact)
            if response.resultCount == 1:
                artifact = response.next()
            else:
                art_type = False
        else: # artifact isn't anything we can deal with here...
            pass

        return art_type, artifact
        

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
            qualifiers.append('%s=%s' % ('query', encodedQuery if encodedQuery else ""))
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

        resource += "&".join(qualifiers)
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
            if condition[0] != '(' and condition[-1] != ')':
                return '(%s)' % urllib.quote(condition)
            else:
                return urllib.quote(condition)

        if type(query) in [types.StringType, types.UnicodeType]:
            # if the query as provided is already surrounded by paren chars, return it 
            # with the guts urllib.quote'ed
            if query[0] == "(" and query[-1] == ")":
                # restore any interior parens from the %28 / %29 encodings"
                return "(%s)" % urllib.quote(query[1:-1]).replace('%28', '(').replace('%29', ')')

            if ' AND ' not in query and ' OR ' not in query and ' and ' not in query and ' or ' not in query:
                return "(%s)" % urllib.quote(query)

            else:  # do a regex split using ' AND|OR ' then urllib.quote the individual conditions
                CONJUNCTIONS = ['and', 'or', 'AND', 'OR']
                parts = CONJUNCTION_PATT.split(query)
                parts = [p if p in CONJUNCTIONS else _encode(p) for p in parts]
                return "(%s)" % "%20".join(parts)
        elif type(query) in [types.ListType, types.TupleType]:
            # by fiat (and until requested by a paying customer), we assume the conditions are AND'ed
            parts = [_encode(condition) for condition in query] 
            return "(%s)" % "%20AND%20".join(parts)
        elif type(query) == types.DictType:  # wow! look at this wildly unfounded assumption about what to do!
            parts = []
            for field, value in query.items():
                # have to enclose string value in double quotes, otherwise turn whatever the value is into a string
                tval = '"%s"' % value if type(value) == types.StringType else '%s' % value
                parts.append('(%s)' % urllib.quote('%s = %s' % (field, tval)))
            anded = "%20AND%20".join(parts)
            if len(parts) > 1:
                return "(%s)" % anded
            else:
                return anded

        return None

    def augmentWorkspace(self, augments, workspace_ref):
        wksp_augment = [aug for aug in augments if aug.startswith('workspace=')]
        self.workspace = "workspace=%s" % workspace_ref
        if wksp_augment:
            self.workspace = wksp_augment[0]

    def augmentProject(self, augments, project_ref):
        proj_augment = [aug for aug in augments if aug.startswith('project=')]
        self.project = "project=%s" % project_ref
        if proj_augment:
            self.project = proj_augment[0]

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

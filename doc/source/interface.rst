
Primary *pyral* classes and functions
=====================================

For the most part, you'll only be utilizing two main entry points to the **pyral** package.

The first is the **rallySettings** convenience function that you'll use to obtain target
and credential values.
The second is the **Rally** class, from which you'll obtain an instance and then treat that
as a direct link to the Rally SaaS.  An instance of the Rally class has the basic four CRUD
operations as well as several convenience methods to obtain information about workspaces, 
projects, users and Rally type/value metadata.

You'll also be using the results of queries issued to Rally that are returned as instances 
of the **RallyRESTResponse** class.  Instances of this class allow easy dot ('.') notation
access to attributes of the representation of the Rally entity, whether the attribute is a
simple value or a reference to another Rally entity.

rallySettings
=============

This function takes into account your environment and arguments provided to this function
to arrive at and return information necessary to establish a useful *connection* to the 
Rally server.

The process consists of a priority chain where some reasonable default information is
established first and then overridden with subsequent steps in the chain (if they exist).
At then end of the priority chain values for server, user, password, workspace, project are
returned to the caller.

The priority chain consists of these steps:
    * establish baseline values from values defined in the module containing the rallySettings
    * override with any environment variables present from this list:
        - RALLY_SERVER
        - RALLY_VERSION
        - RALLY_USER
        - RALLY_PASSWORD
        - RALLY_WORKSPACE
        - RALLY_PROJECT
    * if present, use information from a rally-<version>.cfg file in the current directory,
      where <version> matches the Rally WSAPI version defined in the pyral.config module.
      Currently, that version is defined as 1.29.
    * if present, use the contents of a file named in the RALLY_CONFIG environment variable.
    * if present, use the contents of a config named on the command line via the --config-<filename>
      option
    * if present, use the values of individual credential/target settings provided as command line
      options via the --<option>=<value>.
       
The specific syntax available for these levels is detailed below.
    
    **Files**

        The general syntax is:
            - CAP_NAME  = value
        Valid entries are:
            - SERVER    = <RallyServer>
            - VERSION   = <RallyWebServicesVersion>
            - USER      = <validUserName>
            - PASSWORD  = <validPassword>
            - WORKSPACE = <validWorkspaceName>
            - PROJECT   = <validProjectName>

    **Command line options**

         --rallyConfig=<configFileName>

        or --config=<configFileName>

        or --conf=<configFileName>

        or --cfg=<configFileName>

        --rallyServer=<serverName>

        --rallyVersion=<ws_version>

        --rallyUser=<validRallyUserName>

        --rallyPassword=<validRallyPassword>

        --workspace=<validWorkspaceName>

        --project=<validProjectName>

This mechanism provides the ability to centrally locate a configuration file that can
be used by many members of a team where server, workspace, project are common to all members
and each individual can have their own appropriately secured config file with their credentials.
Using this mechanism can save tedious and error-prone entry of target information and credentials
on the command line or having credential information in clear text in unsecured files.

Example use::

    % export RALLY_SERVER="rally1.rallydev.com"
    % export RALLY_USER="crazedwiley@acmeproducts.com"

    % ls -l current.cfg

      -rw-------  1 wiley  eng  173 Oct 14 07:02 current.cfg

    % cat current.cfg

      USER = wiley@acme.com
      WORKSPACE = General Products Umbrella
      PROJECT = Dairy Farm Automation

    % cat basic.py
    
    import sys
    from rally import rallySettings

    options = [opt for opt in sys.argv[1:] if opt.startswith('--')]
    server, user, password, workspace, project = rallySettings(options)
    print " ".join(['|%|' % opt for opt in [server, user, password, workspace, project]]


    % python basic.py --config=current --rallyPassword='*****' --rallyProject="Livestock Mgmt"

    |rally1.rallydev.com| |wiley@acme.com| |*****| |General Products Umbrella| |Livestock Mgmt|

Note that for convenience purposes a configuration file name may be fully specified 
or you may elect to not specify the '.cfg' suffix.


Rally
=====

    The Rally class is the central focus of the **pyral** package.  Instantation of this class
    with appropriate and valid target/credential information then provides a means of 
    interacting with the Rally server.

    To instantiate a Rally object, you'll need to provide these arguments:
        * server
        * user
        * password

    either in this specific order or as keyword arguments.

    You can optionally specify the following as keyword arguments.
        * version
        * workspace
        * project
        * version  (specify the Rally WSAPI version, default is 1.29)
        * warn     (True or False, default is True) 
                    Controls whether a warning is issued if no project is specified
                    and the default project for the user is not in the workspace specified.  
                    Under those conditions, the project is changed to the first project
                    (alphabetic ordering) in the list of projects for specified workspace.

.. py:class:: Rally (server, user, password, version=1.29, workspace=None, project=None, warn=True)

Examples::

    rally = Rally('rally1.rallydev.com', 'chester@corral.com', 'bAbYF@cerZ')

    rally = Rally(server='rally1.rallydev.com', user='mchunko', password='mySEk^et')

    rally = Rally(server, user, password, workspace='Division #1 Products', project='ABC')

    rally = Rally(server, user, password, workspace='Brontoville', warn=False)



Core REST methods and CRUD aliases
----------------------------------

.. method:: put (entityName, itemData, workspace=None, project=None)

        This method allows for the creation of a single Rally entity for the given entityName.
        The data is supplied in a dict and must include settings for all required fields.
        An attempt to create an entity record for which the operational credentials do not
        include the privileges to create Rally entity entries will result in a RallyRESTException 
        being generated.

        Returns a representation of the item as an instance of a class named for the entity.

.. method:: create

        alias for put


.. method:: get (entityName, fetch=False | True | comma_separated_list_of_fields, query=None, order=None, **kwargs)

        This method allows for the retrieval of records for the given entityName.
        A fetch value of False results in a "shell" record returned with only basic
        ref attributes having values.  If the fetch value is True, a fully hydrated
        record for each qualifying entity is returned. If the fetch value is a string
        with a list of comma separated attribute names, those name attributes will be
        members of each returned entity record.

        keyword arguments:
            - fetch = True/False or "List,Of,Attributes,We,Are,Interested,In"
            - query = 'FieldName = "some value"' or ['fld1 = 10', 'fld2 != "Shamu"', etc.]
            - instance = True/False (defalts to False)
            - pagesize = n  (defaults to 200)
            - start = n  (defaults to 1)
            - limit = n  (defaults to no limit)
            - workspace = workspace_name (defaults to current workspace selected)
            - project = project_name (defaults to current project selected)
            - projectScopeUp = True/False (defaults to False)
            - projectScopeDown True/False (defaults to False)

        Returns a RallyRESTResponse object that has errors and warnings attributes that
        should be checked before any further operations on the object are attempted.
        The Response object supports the iteration protocol so that the results of the
        get can be iterated over via either ``for rec in response:`` or ``response.next()``.

        If the instance keyword value is True, then an instance of a Rally entity
        will be returned instead of a RallyRESTResponse.  This can be useful when 
        retrieving an item you know exists and is uniquely identified by your query argument.

.. note::

        If you use a simple query, eg., 'SomeField = "Abc"' then _you_ don't need
        to use parens (although the Rally REST API does...).  If you specify the conditions 
        as in the list variation (see the second example in the query keyword explanation above),
        then the conditions are AND'ed together in a form suitable for consumption by the 
        Rally REST API.

        **Caution**: If there are any paren characters in a query string, then the 
        toolkit takes a hands-off policy and lets you take the responsibility for specifying
        the query in a form suitable for the Rally REST WSAPI. (See the Help page for 
        for the Rally REST WSAPI in the Rally web-based product).

        Use the instance keyword with **caution**, as an exception will be generated
        if the query produces no qualifying results.
        If the query produces more than one qualifying result, you'll only get 
        get the first result with no means to obtain any further qualifying items.
            

.. method:: find   

         alias for get

.. method:: post (entityName, itemData, workspace=None, project=None)

        This method allows for updating a single Rally entity record with the data
        contained in the itemData dict.  The itemData dict may *not* attempt to change 
        the ObjectID value of the entity as the value for the ObjectID is used to identify
        the Rally entity to update.  An attempt to update an entity record for
        which the operational credentials do not include the privileges to update will
        result in a RallyRESTException being generated.

        Returns a representation of the item as an instance of a class named for the entity.

.. method:: update

         alias for post

.. method:: delete (entityName, itemIdent, workspace=None, project=None)
        
        This method allows for deleting a single Rally entity record whose ObjectID
        (or FormattedID) must be present in the itemIdent parameter.  
        An attempt to delete an entity record for which the operational credentials
        do not include the privileges to delete will result in the generation 
        of a RallyRESTException.

        Returns a boolean indication of the disposition of the attempt to delete the item.

pyral.Rally instance convenience methods
----------------------------------------

.. method:: enableLogging (dest=sys.stdout, attrget=False, append=False)

    Use this to enable logging. *dest* can set to the name of a file or an open file/stream (writable). 
    If *attrget* is set to True, all Rally REST requests that are executed to obtain attribute 
    information will also be logged. Be careful with that as the volume can get quite large.
    The *append* parameter controls whether any existing file will be appended to or overwritten.


.. method:: disableLogging()
    
    Disables logging to whatever destination has been previously set up.


.. method:: subscriptionName()

    Returns the name of the subscription for the credentials used to establish 
    the connection with Rally.


.. method:: setWorkspace(workspaceName)
    
    Given a workspaceName, set that as the current workspace and use the ref for that
    workspace in subsequent interactions with Rally.
      

.. method:: getWorkspace()

    Returns an instance of a Workspace entity with information about the workspace 
    in the currently active context.


.. method:: getWorkspaces()

    Return a list of Workspace instances that are available for
    the credentials used to establish the connection with Rally.
    

.. method:: setProject(projectName)

    Given a projectName, set that as the current project and use the ref for 
    that project in subsequent interractions with Rally.


.. method:: getProject(projectName)

    Returns an instance of a Project entity with information about the project 
    in the currently active context.


.. method:: getProjects(workspace='default')

    Return a list of Project instances that are available for the workspace context
    identified by the workspace keyword argument.


.. method:: getUserInfo(oid=None, username=None, name=None)

    A convenience method to collect specific user related information.
    
    Caller must provide at least one keyword arg and non-None / non-empty value
    to identify the user target on which to obtain information.
    The *name*     keyword arg is associated with the User.DisplayName attribute.
    The *username* keyword arg is associated with the User.UserName attribute.
    If provided, the *oid* keyword argument is used, even if other keyword args are 
    provided. Similarly, if the *username* keyword arg is provided it is used
    even if the *name* keyword argument is provided.

    Returns either a single instance of a User entity when the oid keyword argument
    matches a User in the system, or a list of User entity items when the username
    or name keywords are given and are matched by at least one User in the system.
    Returns None if no match for keyword argument is found in the system.


.. method:: getAllUsers()

    This method offers a convenient one-stop means of obtaining usable information 
    about all users in the named workspace.
    If no workspace is specified, then the current context's workspace is used.

    Return a list of User instances (fully hydrated for scalar attributes)
    whose ref and collection attributes will be lazy eval'ed upon access.


.. method:: getAllowedValues(entityName, attributeName [,workspace=None])

    Given an entityName and and attributeName (assumed to be valid for the entityName)
    issue a request to obtain a list of allowed values for the attribute.


RallyRESTResponse
=================

A RallyRESTResponse instance is returned from a call to get (find) and several of the
convenience methods.  A instance has the following useful state attributes:

    - resource    = partial URL identifying the resource for the HTTP Request
    - status_code = numeric code for the HTTP Response
    - headers     = HTTP headers returned
    - content     = a dict produced by JSON'ifying the HTTP response body
    - errors      = a list of strings with any Error information
    - warnings    = a list of strings with any Warning information
    - startIndex  = natural number index (ie., 1 to _X_)
    - pageSize    = chunk size returned
    - resultCount = total number of items in the set meeting the selection criteria

In addition and usually more importantly, a RallyRESTResponse instance can be used as
an iterator over the results.

There are two common means of exercising the iterative nature of the reponse.
Use a for loop to obtain each item (you can use this in a list comprehension also)
or use the *next* method to obtain the next item in the qualifying result set. 

Examples::

   # regular for loop

   response = rally.get('Defect', query=..., ...)
   for item in response: print item

   # in a list comprehension

   response = rally.get('UserStory', query=..., ...)
   story_titles = [story.Name for story in response]

   # using the next method

   response = rally.get('Task', query=..., ...)
   task1 = response.next()


.. py:class:: RallyRESTResponse()

.. method:: next()

    Returns the next item from the set of qualifying items.  
    This method handles any further requests to the server if the next qualifying item
    is not in the current page of results returned from Rally.
    If all qualifying items have been returned via this method, this method 
    generates a StopIteration exception.


Item Attributes
===============

    Item instances returned from iterating on a RallyRESTResponse object are 
    representations of Rally items.  The attributes of each item are accessible via
    the standard dot (.) notation.  The names are identical to those documented in the 
    `Rally WS API`_.

.. _Rally WS API: https://rally.rallydev.com/slm/doc/webservice 

    Generally, every concrete instance in the Rally system will have a Name attribute.
    You can use the **attributes()** method on an instance to obtain the names of all of the 
    attributes available on your specific instance.

    So, to obtain the name of a TestCase if you have a TestCase instance, you 
    use testcase.Name, to obtain the formatted ID of a story, use story.FormattedID.

    There are two special attributes, *oid* and *ref* that are convenient meta-attributes 
    provided with every instance. The *oid* attribute is an alias for ObjectID and the *ref*
    attribute is the portion of the _ref attribute containing the entity name and ObjectID value.
    The ref attribute is suitable for use whenever you want/need to specify the value of
    a reference field.

    Attributes that are classified as references (as opposed to a simple string or integer value)
    can be accessed and attributes on the referenced item can be obtained.
    A UserStory (alias for HierarchicalRequirement) can have a parent story.  To obtain
    the parent's FormattedID attribute value, you'd specify thusly: story.Parent.FormattedID. 

    An attribute can also be a collection. For example, Tasks associated with a UserStory.
    To access these tasks, you'd iterate over them as in:
 
::

    response = rally.get('UserStory', fetch=True, query='State != "Closed"')
    if not response.errors:
        for story in response:
            for task in story.Tasks:
                print task.oid, task.Name, task.ActualHours

    


Primary *pyral* classes and functions
=====================================

For the most part, you'll only be utilizing two main entry points to the **pyral** package.

The first is the **rallySettings** convenience function that you'll use to obtain target
and credential values. If you are using 1.1.x or beyond, you may want to alternatively use the 
**rallyWorkset** convenience function to obtain target and credential values if you intend
to use a Rally API Key for credentials.
The second is the **Rally** class, from which you'll obtain an instance and then treat that
as a direct link to the Rally SaaS.  An instance of the Rally class has the basic four CRUD
operations as well as several convenience methods to obtain information about workspaces, 
projects, users and Rally type/value metadata.

You'll also be using the results of queries issued to Rally that are returned as instances 
of the **RallyRESTResponse** class.  Instances of this class allow easy dot ('.') notation
access to attributes of the representation of the Rally entity, whether the attribute is a
simple value or a reference to another Rally entity.

rallyWorkset
============

New in 1.1.0.

This function takes into account your environment and arguments provided to this function
to arrive at and return information necessary to establish a useful *connection* to the 
Rally server.  This convenience function differs from **rallySettings** by also including
the Rally API Key in the set of values considered and returned.

The process consists of a priority chain where some reasonable default information is
established first and then overridden with subsequent steps in the chain (if they exist).
After following the priority chain, values for server, user, password, apikey, workspace, 
project are returned to the caller.

The priority chain consists of these steps:
    * establish baseline values from values defined in the module containing the rallyWorkset
    * override with any environment variables present from this list:
        - RALLY_SERVER
        - RALLY_USER
        - RALLY_PASSWORD
        - APIKEY
        - RALLY_WORKSPACE
        - RALLY_PROJECT
        - RALLY_PING
    * if present, use information from a rally-<version>.cfg file in the current directory,
      where <version> matches the Rally WSAPI version defined in the pyral.config module.
      Currently, that version is defined as v2.0.
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
            - USER      = <validUserName>
            - PASSWORD  = <validPassword>
            - APIKEY    = <validAPIKey>
            - WORKSPACE = <validWorkspaceName>
            - PROJECT   = <validProjectName>
            - RALLY_PING = True | False

    **Command line options**

         --rallyConfig=<configFileName>

        or --config=<configFileName>

        or --conf=<configFileName>

        or --cfg=<configFileName>

        --rallyServer=<serverName>

        --rallyUser=<validRallyUserName>

        --rallyPassword=<validRallyPassword>

        --apikey=<validRallyAPIKeyValue>

        --workspace=<validWorkspaceName>

        --project=<validProjectName>
     
        --ping=True|False|true|false|yes|no|1|0

This mechanism provides the ability to centrally locate a configuration file that can
be used by many members of a team where server, workspace, project are common to all members
and each individual can have their own appropriately secured config file with their credentials.
Using this mechanism can save tedious and error-prone entry of target information and credentials
on the command line or having credential information in clear text in unsecured files.

The use of a Rally API Key value for identification/authentication is new in pyral 1.1.x. 
If used, you do not need to provide a username / password combination.
In order to use this, you must first obtain a valid API Key value from the Rally Application
Manager (API Keys) that you can access from https://rally1.rallydev.com/login.
Once obtained, you should treat the key with the same level of protection as you would 
any user/password information; once presented to Rally via the Rally Web Services API, 
a connection has all the rights associated with the user whose key was presented.
Consult the Rally help documentation for further information.

Example use::

    % export RALLY_SERVER="rally1.rallydev.com"
    % export RALLY_USER="crazedwiley@acmeproducts.com"

    % ls -l current.cfg

      -rw-------  1 wiley  eng  173 Jul 14 07:02 current.cfg

    % cat current.cfg

      USER = wiley@acme.com
      WORKSPACE = General Products Umbrella
      PROJECT = Dairy Farm Automation

    % cat basic.py
    
    import sys
    from rally import rallyWorkset

    options = [opt for opt in sys.argv[1:] if opt.startswith('--')]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    print " ".join(['|%|' % opt for opt in [server, user, password, apikey, workspace, project]]


    % python basic.py --config=current --rallyProject="Livestock Mgmt" --ping=no

    |rally1.rallydev.com| |wiley@acme.com| |*****| |*****| |General Products Umbrella| |Livestock Mgmt|

Note that for convenience purposes a configuration file name may be fully specified 
or you may elect to not specify the '.cfg' suffix.

Returns a tuple of (server, username, password, apikey, workspace, project)


rallySettings
=============

This is deprecated as of v1.2.0. The preferred function is **rallyWorkset** which will have
ongoing support.  The **rallySettings** function will be removed in v2.0.0.

This function takes into account your environment and arguments provided to this function
to arrive at and return information necessary to establish a useful *connection* to the 
Rally server.

The process consists of a priority chain where some reasonable default information is
established first and then overridden with subsequent steps in the chain (if they exist).
After following the priority chain, values for server, user, password, workspace, project
are returned to the caller.

The priority chain consists of these steps:
    * establish baseline values from values defined in the module containing the rallySettings
    * override with any environment variables present from this list:
        - RALLY_SERVER
        - RALLY_USER
        - RALLY_PASSWORD
        - RALLY_WORKSPACE
        - RALLY_PROJECT
    * if present, use information from a rally-<version>.cfg file in the current directory,
      where <version> matches the Rally WSAPI version defined in the pyral.config module.
      Currently, that version is defined as v2.0.
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
            - USER      = <validUserName>
            - PASSWORD  = <validPassword>
            - APIKEY    = <validAPIKey>
            - WORKSPACE = <validWorkspaceName>
            - PROJECT   = <validProjectName>

    **Command line options**

         --rallyConfig=<configFileName>

        or --config=<configFileName>

        or --conf=<configFileName>

        or --cfg=<configFileName>

        --rallyServer=<serverName>

        --rallyUser=<validRallyUserName>

        --rallyPassword=<validRallyPassword>

        --apikey=<validRallyAPIKeyValue>

        --workspace=<validWorkspaceName>

        --project=<validProjectName>

This mechanism provides the ability to centrally locate a configuration file that can
be used by many members of a team where server, workspace, project are common to all members
and each individual can have their own appropriately secured config file with their credentials.
Using this mechanism can save tedious and error-prone entry of target information and credentials
on the command line or having credential information in clear text in unsecured files.

The use of a Rally API Key value for identification/authentication is new in pyral 1.1.x. 
If used, you do not need to provide a username / password combination.
In order to use this, you must first obtain a valid API Key value from the Rally Application
Manager (API Keys) that you can access from https://rally1.rallydev.com/login.
Once obtained, you should treat the key with the same level of protection as you would 
any user/password information; once presented to Rally via the Rally Web Services API, 
a connection has all the rights associated with the user whose key was presented.
Consult the Rally help documentation for further information.

Example use::

    % export RALLY_SERVER="rally1.rallydev.com"
    % export RALLY_USER="crazedwiley@acmeproducts.com"

    % ls -l current.cfg

      -rw-------  1 wiley  eng  173 Jul 14 07:02 current.cfg

    % cat current.cfg

      USER = wiley@acme.com
      WORKSPACE = General Products Umbrella
      PROJECT = Dairy Farm Automation

    % cat basic.py
    
    import sys
    from rally import rallyWorkset

    options = [opt for opt in sys.argv[1:] if opt.startswith('--')]
    server, user, password, apikey, workspace, project = rallyWorkset(options)
    print " ".join(['|%|' % opt for opt in [server, user, password, apikey, workspace, project]]


    % python basic.py --config=current --rallyProject="Livestock Mgmt"

    |rally1.rallydev.com| |wiley@acme.com| |*****| |*****| |General Products Umbrella| |Livestock Mgmt|

Note that for convenience purposes a configuration file name may be fully specified 
or you may elect to not specify the '.cfg' suffix.

Returns a tuple of (server, username, password, apikey, workspace, project)


Rally
=====

    The Rally class is the central focus of the **pyral** package.  Instantiation of this class
    with appropriate and valid target/credential information then provides a means of 
    interacting with the Rally server.

To instantiate a Rally object, you'll need to provide these arguments:
        * **server**    usually rally1.rallydev.com unless you are using an OnPrem version
        * **user**      AgileCentral UserName
        * **password**  AgileCentral password for the given user

    either in this specific order or as keyword arguments.

    You must either have default **workspace** and **project** values set up for your account

    OR 

    you must provide **workspace** and **project** values that are valid and accessible for your account.

    You can optionally specify the following as keyword arguments:
        * apikey      (alternate credential specification)
        * workspace   (name of the AgileCentral workspace)
        * project     (name of the AgileCentral project)
        * verify_ssl_cert  (True or False, default is True)
        * warn     (True or False, default is True) 
                    Controls whether a warning is issued if no project is specified
                    and the default project for the user is not in the workspace specified.  
                    Under those conditions, the project is changed to the first project
                    (alphabetic ordering) in the list of projects for the specified workspace.
        * server_ping     (True or False, default in v1.2.0 is True)
                   Specifies whether a ping attempt will be made to confirm network connectivity
                   to the Rally server prior to making a Rally WSAPI REST request.
                   Organizations may have disabled the ability to make ICMP requests so the ping
                   attempt may fail even though there is network connectivity to the Rally server.
                   For this reason, the use of the ping=True option is discouraged going forward.
                   The next minor point release of pyral (v1.3.0) will have the default value 
                   for this option inverted to be False.  
                   The the ping operation itself will be dropped in the next major release (2.0.0).
        * isolated_workspace  (True or False, default in v1.2.0 is False)
                   Specifies that the Rally instance will only be used for interacting with 
                   a single workspace (either the user's default workspace or the named workspace).
                   Using isolated_workspace=True provides performance benefits for a subscription
                   with many workspaces, but it also means you cannot change the workspace you 
                   are working within a single instance of a Rally class, nor can you provide
                   a workspace keyword argument to the get, create, update or delete methods that
                   differs from the workspace identified at instantiation time.
                   For subscriptions with a small to moderate number of workspaces (up to a few dozen),
                   the performance savings will be relatively minor when using isolated_workspace=True
                   vs. isolated_workspace=False.  However, for subscriptions with a large number of
                   workspaces, using isolated_workspace=False results in a request to AgileCentral
                   for each workspace, which can result in a noticeable lag before the instantiation
                   statement returns a ready-for-use Rally instance.

    If you use an apikey value, any user name and password you provide is not considered, the connection
    attempt will only use the apikey.
    Consult the Rally Help documentation for Rally Application Manager for information
    on how to generate an API Key and how to reset or delete an API Key.

.. note::

        If your Subscription administrator has set up your Rally Subscription as "SSO only", then to use
        **pyral**, you must have your account added to the whitelist in Rally so that you can use either
        BasicAuth (username and password) or the API Key to authenticate to Rally.

.. note::

        As of the 1.2.2 release, **pyral** offers a means of precisely identifying a Project whose name appears in multiple locations within the forest of Projects with a Workspace.  For example, your organization may have several "base" level Projects with sub-trees of Projects.  In this scenario, you might have multiple Projects named 'AgileTeam-X' or 'SalesPrep'.  By using a Project path component separator of '  // ' (<space><slash><slash><space>) you can specify the unambiguous and unique path to the specific Project of interest.  Example:  Omnibus // Metallic // Conductive // Copper // Wire . 
        You only have to use this syntax to specify a particular Project if you have multiple instances of that Project that have the same name.  There is no provision for supporting the scenario where a Project of the same name exists in the same structural location. 


.. py:class:: Rally (server, user=None, password=None, apikey=None, workspace=None, project=None, warn=True, server_ping=True)

Examples::

    rally = Rally('rally1.rallydev.com', 'chester@corral.com', 'bAbYF@cerZ')

    rally = Rally(server='rally1.rallydev.com', user='mchunko', password='mySEk^et')

    rally = Rally(server, user, password, workspace='Division #1 Products', project='ABC')

    rally = Rally(server, user, password, workspace='Brontoville', verify_ssl_cert=False, warn=False)

    rally = Rally(server, apikey="_some-more-numbers", workspace='RockLobster', project='Fence Posts')

    rally = Rally('rally1.rallydev.com', 'chester@corral.com', 'bAbYF@cerZ', server_ping=False)



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


.. method:: get (entityName, fetch=False | True | comma_separated_list_of_fields, query=None, order=None, \*\*kwargs)

        This method allows for the retrieval of records for the given entityName.
        A fetch value of False results in a "shell" record returned with only basic
        ref attributes having values.  If the fetch value is True, a fully hydrated
        record for each qualifying entity is returned. If the fetch value is a string
        with a list of comma separated attribute names, those name attributes will be
        members of each returned entity record.

        keyword arguments:
            - fetch = True/False or "List,Of,Attributes,We,Are,Interested,In"
            - query = 'FieldName = "some value"' or ['EstimatedHours = 10', 'MiddleName != "Shamu"', 'Name contains "foogelhorn pop-tarts"',  etc.]
            - instance = True/False (defaults to False)
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
        ``get`` can be iterated over via either ``for rec in response:`` or ``response.next()``.

        If the instance keyword value is True, then an instance of a Rally entity
        will be returned instead of a RallyRESTResponse.  This can be useful when 
        retrieving an item you know exists and is uniquely identified by your query argument.

        The query keyword argument can consist of a String, a List of Strings as *<name> <relation> <value>*
        conditions
        or as a Dictionary where the key-value pairs have an implicit equality relationship and
        all the resulting conditions are AND'ed together.

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

        If you need to have any OR'ing of conditions, you'll have to construct the entire
        query yourself in the form of a single String with paren characters in the correct
        locations to make the query syntactically conformant with the Rally REST WSAPI.
        Example: query=((Name contains "ABC") OR ((Priority = "1-Critical") AND (Severity != "3-Minor")))
        Yes, it's kind of a pain in the ...

        Using the characters of '**~**' or '**&**' or '**|**' or a backslash '**\\**' 
        within a query expression (eg. 'Name contains "|"') are problematic with the use of this
        toolkit.  A REST request will be issued, but even if there are actual qualifying 
        items that you could observe by using the Rally web GUI, the Rally WSAPI response will 
        not have the correct count or content of the qualifying items.  Other workarounds are
        recommended to deal with this; one way is to post-process the results of a less
        restrictive criteria to filter or qualify the results to your specific criteria.

        Use the instance keyword with **caution**, as an exception will be generated
        if the query produces no qualifying results.
        If the query produces more than one qualifying result, you'll only get 
        get the first result with no means to obtain any further qualifying items.
            

.. method:: find   

         alias for get

.. method:: post (entityName, itemData, workspace=None, project=None)

        This method allows for updating a single Rally entity record with the data
        contained in the itemData dict.  The itemData dict *must* include a 
        key-value pair for either the ObjectID or when applicable, the FormattedID,
        that will uniquely identify the entity to be updated.
        The itemData dict may *not* attempt to change the ObjectID value of the 
        entity as the value for the ObjectID is used to identify
        the Rally entity to update.  An attempt to update an entity record for
        which the operational credentials do not include the privileges to update 
        will result in a RallyRESTException being generated.

        Returns a representation of the updated item as an instance of a class named for the entity.

.. method:: update

         alias for post

.. method:: delete (entityName, itemIdent, workspace=None, project=None)
        
        This method allows for deleting a single Rally entity record whose ObjectID
        (or FormattedID) must be present in the itemIdent parameter.  
        An attempt to delete an entity record for which the operational credentials
        do not include the privileges to delete will result in the generation 
        of a RallyRESTException.

        Returns a boolean indication of the disposition of the attempt to delete the item.

.. method:: search(keywords, \*\*kwargs)

     Given a list of keywords or a string with space separated words, issue
     the relevant Rally WSAPI search request to find artifacts within the search
     scope that have any of the keywords in any of the artifact's text fields.

     NOTE: The search functionality must be turned on for your subscription to use this method.

     keyword arguments:
         - projectScopeUp = true/false (defaults to false)
         - projectScopeDown = true/false (defaults to false)
         - pagesize = n  (defaults to 200)
         - start = n  (defaults to 1)
         - limit = n  (defaults to no limit)

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


.. method:: getProject(name=None)

    Returns a minimally hydrated Project entity instance with the Name and ref
    of the project in the currently active context if the name keyword arg
    is not supplied or the Name and ref of the project identified by the value of 
    the name parameter as long as the name identifies a valid project in the currently 
    selected workspace.
    Returns None if a name parameter is supplied that does not identify a valid project
    in the currently selected workspace.


.. method:: getProjects(workspace=None)

    Return a list of Project instances that are available for the workspace context
    identified by the workspace keyword argument. If no workspace keyword argument 
    is supplied (or is supplied as None), then the workspace context is that 
    of the currently selected workspace.


.. method:: getUserInfo(oid=None, username=None, name=None)

    A convenience method to collect the information associated with a specific user.
    
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
    Returns None if there is no match in the Rally subscription/workspace for
    the keyword argument used to identify the user target.

.. method:: getAllUsers(workspace=None)

    This method offers a convenient one-stop means of obtaining usable information 
    about all users in the named workspace.
    If no workspace is specified, then the current context's workspace is used.
    NOTE: Unless you are using credentials associated with a SubscriptionAdministrator
    or WorkspaceAdministrator, you will not be able to access a user's UserProfile
    other than yourself.

    Return a list of User instances (fully hydrated for scalar attributes)
    whose ref and collection attributes will be lazy eval'ed upon access.

.. method:: typedef(entityName)
    
    This method returns a TypeDefinition instance for the given entityName.
    The is handy for occasions where you need identify a specific entity
    for something like 'Feature' or 'Theme' when creating or updating a
    PortfolioItem subclass.  Intended usage is to use the return *.ref* attribute.
    For example, within an info dict, "PortfolioItemType" : rally.typedef('Feature').ref .

.. method:: getCollection(collection_url)

    Given a collection_url of the form:

       http(s)://<server>(:<port>)/slm/webservice/v2.0/<entity>/OID/<attribute>

    issue a request for the url and return back a list of hydrated instances 
    for each item in the collection.
    

.. method:: getState(entityName, stateName)
    
    As of Rally WSAPI 1.37 (Sep 2012), the State attribute is no longer a String value for 
    many entities, it is itself an entity (aka Rally Type). To be able to create (or update) 
    an Artifact's State attribute, you must provide a reference (_ref or ref) in the information 
    dictionary used to populate the Artifact's attributes.  This method provides an
    easy means of obtaining the appropriate entity for the particular entity and state Name
    you want.  Typically the usage would be along the lines of this example:

::

       info = { ...., "State" : rally.getState('Feature', 'Discovering').ref, ... })

.. warning:: 

        This method only works with PortfolioItem subclasses at this time.  (Theme, Strategy, Initiative, Feature)


.. method:: getStates(entityName)
    
    Given an entityName, returns a list of State instances populated with information
    about each state value permitted for the entityName.

.. method:: getAllowedValues(entityName, attributeName [,workspace=None])

    Given an entityName and and attributeName (assumed to be valid for the entityName)
    issue a request to obtain a list of allowed values for the attribute.

.. method:: addAttachment(artifact, filename, mime_type='text/plain')

    Given an artifact (actual or FormattedID for an artifact), validate that
    it exists and then attempt to add an Attachment with the name and
    contents of filename into Rally and associate that Attachment with the
    Artifact.
    Returns the Attachment item.

.. method:: addAttachments(artifact, attachments)

    Given an artifact (either actual or FormattedID) and a list of dicts with
    each dict having keys and values for name (or Name), mime_type (or MimeType) and
    content_type (or ContentType), add an Attachment corresponding to each dict in 
    the attachments list and associate it with the referenced Artifact.

.. method:: getAttachment(artifact, filename)

    Given a real artifact instance or the FormattedID of an existing artifact,
    obtain the attachment named by filename.  If there is such an attachment,
    return an Attachment instance with hydration for  Name, Size, ContentType, Content,
    CreationDate and the User that supplied the attachment.
    If no such attachment is present, return None

.. method:: getAttachmentNames(artifact)

    Given a real artifact instance that is hydrated for at least the Attachments attribute,
    return the names (filenames) of the Attachments associated with the artifact.

.. method:: getAttachments(artifact)

    Given a real artifact instance, return a list of Attachment records.
    Each Attachment record will look like a Rally WSAPI Attachment with
    the additional Content attribute that will contain the decoded AttachmentContent.

.. method:: rankAbove(reference_artifact, target_artifact)

    Rank the target_artifact above the reference_artifact.

.. method:: rankBelow(reference_artifact, target_artifact)

    Rank the target_artifact below the reference_artifact.

.. method:: rankTop(target_artifact)

    Rank the target_artifact at the top of the list of ranked Artifacts 
    that the target_artifact exists in.

.. method:: rankBottom(target_artifact)

    Rank the target_artifact at the bottom of the list of ranked Artifacts 
    that the target_artifact exists in.
    
pyral.Rally experimental convenience methods
--------------------------------------------

.. method:: addCollectionItems(target_item, collection_items)
    
    Given a target_item and a homogenous list of items whose type appears as a One to Many relationship
    in the target item, add the collection_items to the corresponding attribute in the target_item.

::

       ...
       milestones = [milestone_1, milestone_2, milestone_3]
       story = rally.get('story', 'US123') 
       rally.addCollectionItems(story, milestones)

.. warning:: 

        This method only works when the collection attribute on the target_item is Modifiable.
        Consult the AgileCentral WSAPI documentation for the target_item attributes to see whether
        the attribute of interest has a notation of 'Collection Modifiable  yes'.  If there is no 
        'Colletion Modifiable' notation or the value for that is 'no', then use of this method 
        should not be attempted.
        At this time, the AgileCentral WSAPI schema endpoint does not include information about 
        'Collection Modifiable' for any of the attributes, you'll have to consult the documentation.

.. method:: dropCollectionItems(target_item, collection_items)

    Given a target_item and a homogenous list of items whose type appears as a One to Many relationship
    in the target item, delete the collection_items to the corresponding attribute in the target_item 
    from the current collection contents for the target_item.

.. warning:: 

        See note above for the 'addCollectionItems' method.  The restrictions there are also applicable 
        to this method.


RallyRESTResponse
=================

A RallyRESTResponse instance is returned from a call to ``get`` (find) and several of the
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

.. _Rally WS API: https://rally1.rallydev.com/slm/doc/webservice 

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


.. method:: details()

    This convenience method is available on all *WorkspaceDomain*
    subclass instances and provides an organized and easy to read multiline string
    with the content of the instance.

Example::

    response = rally.get('UserStory', fetch=True, query='FormattedID = S321')
    story1 = response.next()
    print story1.details()

    HierarchicalRequirement
        oid               : 12345678
        ref               : hierarchicalrequirement/12345678
        ObjectID          : 12345678
        _ref              : https://rallydev.rallydev.com/slm/webservice/v2.0/hierarchicalrequirement/412345678
        _CreatedAt        : today at 3:14 am
        _hydrated         : True
        Name              : Filbert nuts should be added to all energy bars
        Subscription      : Subscription.ref   (OID  400060  Name: Company 1)
        Workspace         : Workspace.ref      (OID  722746  Name: Prime Cuts Workspace)
        FormattedID       : S321

        AcceptedDate      : None
        AccountingProjec  : None
        AccountingTask    : None
        AffectedCustomer  : 
        Attachments       : []
        Blocked           : False
        Blocker           : None
        Capitalizable     : None
        Changesets        : []
        Children          : []
        CreationDate      : 2016-07-12T09:14:35.852Z
        DefectStatus      : NONE
        Defects           : []
        Description       : As a health conscious PO, I want better nutritional content in all bars
        Discussion        : []
        IdeaURL           : <pyral.entity.CustomField object at 0x101931290>
        IdeaVotes         : None
        InProgressDate    : 2016-07-12T09:14:36.098Z
        Iteration         : Iteration.ref               (OID  1242381  Name Iteration 5 (Summer))
        KanbanState       : Accepted
        LastUpdateDate    : 2016-07-12T09:14:36.237Z
        ...
    

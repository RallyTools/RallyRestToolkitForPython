pyral - A Python toolkit for the Rally REST API
===============================================


The `pyral <http://github.com/RallyTools/RallyRestToolkitForPython>`_ package enables you to push, pull
and otherwise wrangle the data in your Rally subscription using the popular
and productive Python language.
The ``pyral`` package provides a smooth and easy to use veneer on top
of the Rally REST Web Services API using JSON.

As of July 2015, the Rally Software Development company was acquired by CA Technologies.
The Rally product itself has been rebranded as 'Agile Central'.  Over time, the documentation
will transition from using the term 'Rally' to using 'Agile Central'.


.. contents::

Getting started
---------------

Rally has created a Python package that you can quickly leverage to interact with the data in your 
subscription via the REST web services API.  You can create, read, update, and delete the common 
artifacts and other entities via the Python toolkit for Rally.

Download
````````

Files are available at the `download page`_ .

.. _download page: http://pypi.python.org/pypi/pyral

The git repository is available at https://github.com/RallyTools/RallyRestToolkitForPython


Installation
````````````

Obtain the requests_ package and install it according to that package's directions.
As of requests-2.0.0, there is support for HTTPS over HTTP proxy via the CONNECT request.
Use of requests-2.x or better is recommended for use with pyral.
The requests_ package can be found via the Python Package Index site (http://pypi/python.org/index).
The most recent release of pyral (1.2.2) has been tested using requests 2.8.1.

Obtain and install the six_ module (available from PyPI at https://pypi.python.org/pypi/six)


Unpack the ``pyral`` distribution file (zip or tar.gz) and then install the pyral_ package. 

:: 

    python setup.py install


Use whatever setup options you need for your particular Python environment.


Sanity Check
````````````

Fire up a command line Python interpreter.  Attempt to import the 
relevant packages.

:: 

   $ python
   Python 3.5.1 [other Python interpreter info elided ...]
   >> import requests
   >> import pyral
   >> pyral.__version__
   (1, 2, 2)



30 second highlight
```````````````````

Since Python is a very flexible and extensible language, we were able to make access to the object model 
extremely simple. For example, if you have a a UserStory instance returned by a ``pyral`` operation 
assigned to the name **story**, the following code iterates over the tasks.

::

    for task in story.Tasks:
       print task.Name

There is no need to make a separate call to fetch all the tasks for the story.
When you follow domain model attributes in the Python code, the Python toolkit for 
Rally REST API machinery automatically loads in the necessary objects for you.


Full Documentation
``````````````````

The complete documentation for the Python toolkit for Rally REST API 
is in the doc/build/html subdirectory in the repository.  
The rendered version of this is also available at 
http://pyral.readthedocs.io/en/latest/


Sample code
-----------

Common setup code ::

  import sys
  from pyral import Rally, rallyWorkset
  options = [arg for arg in sys.argv[1:] if arg.startswith('--')]
  args    = [arg for arg in sys.argv[1:] if arg not in options] 
  server, user, password, apikey, workspace, project = rallyWorkset(options)
  rally = Rally(server, user, password, apikey=apikey, workspace=workspace, project=project)
  rally.enableLogging('mypyral.log')

Show a TestCase identified by the **FormattedID** value.
  Copy the above boilerplate and the following code fragment and save it in a file named gettc.py

::

    query_criteria = 'FormattedID = "%s"' % args[0]
    response = rally.get('TestCase', fetch=True, query=query_criteria)
    if response.errors:
        sys.stdout.write("\n".join(errors))
        sys.exit(1)
    for testCase in response:  # there should only be one qualifying TestCase  
        print "%s %s %s %s" % (testCase.Name, testCase.Type,  
                               testCase.DefectStatus, testCase.LastVerdict)
 
- Run it by providing the FormattedID value of your targeted TestCase as a command line argument

    python gettc.py TC1184 

Get a list of workspaces and projects for your subscription
  Copy the above boilerplate and the following code fragment and save it in a file called wksprj.py 

::

   workspaces = rally.getWorkspaces()
   for wksp in workspaces:
       print "%s %s" % (wksp.oid, wksp.Name)
       projects = rally.getProjects(workspace=wksp.Name)
       for proj in projects:
           print "    %12.12s  %s" % (proj.oid, proj.Name)

- Run the script

    python wksprj.py 

Get a list of all users in a specific workspace
  Copy the above boilerplate and the following code fragment and save it in a file called allusers.py 

::

   all_users = rally.getAllUsers() 
       for user in all_users:
           tz   = user.UserProfile.TimeZone or 'default' 
           role = user.Role or '-No Role-'  
           values = (int(user.oid), user.Name, user.UserName, role, tz) 
           print("%12.12d %-24.24s %-30.30s %-12.12s" % values)

- Run the script

    python allusers.py --rallyWorkspace="Product Engineering"

Create a new Defect
  Copy the above boilerplate and the following code fragment and save it in a file called crdefect.py 

::

    proj = rally.getProject()

    # get the first (and hopefully only) user whose DisplayName is 'Sally Submitter' 
    user = rally.getUserInfo(name='Sally Submitter').pop(0) 

    defect_data = { "Project" : proj.ref, "SubmittedBy" : user.ref, 
                    "Name" : name, "Severity" : severity, "Priority" : priority,
                    "State" : "Open", "ScheduleState" : "Defined", 
                    "Description" : description }
    try:
        defect = rally.create('Defect', defect_data)
    except Exception, details:
        sys.stderr.write('ERROR: %s \n' % details)
        sys.exit(1)
    print "Defect created, ObjectID: %s  FormattedID: %s" % (defect.oid, defect.FormattedID)
  
- Run the script

    python crdefect.py <Name> <severity> <priority> <description>

  making sure to provide valid severity and priority values for your workspace


Update an existing Defect
  Copy the above boilerplate and the following code fragment and save it in a file called updefect.py . 

::

    defectID, customer, target_date, notes = args[:4] 
    # target_date must be in ISO-8601 format "YYYY-MM-DDThh:mm:ssZ"

    defect_data = { "FormattedID" : defectID, 
                    "Customer"    : customer, 
                    "TargetDate"  : target_date, 
                    "Notes"       : notes 
                  } 
   try:
       defect = rally.update('Defect', defect_data)
   except Exception, details: 
       sys.stderr.write('ERROR: %s \n' % details) 
       sys.exit(1)

   print "Defect %s updated" % defect.FormattedID

- Run the script

    python updefect.py <Defect FormattedID> <customer> <target_date> <notes text...>



Config Options
--------------

The ``pyral`` package uses a priority
chain of files, environment variables and command line arguments to set the 
configuration context when an instance of the Rally class is created.
See the complete documentation for detailed information on this mechanism.
Here's a brief description of how you can specify a configuration when you 
create an instance of the Rally class.  


*Configuration file settings*

====================================== =========================================
  Config file item                     Description
====================================== =========================================
  SERVER                               Rally server (example rally1.rallydev.com)
  USER                                 Rally subscription UserName value
  PASSWORD                             password for the Rally subscription UserName
  APIKEY                               Rally API Key value
  WORKSPACE                            Rally Workspace
  PROJECT                              Rally Project
====================================== =========================================

The item names in config files **are** case sensitive.

*Command line options*

====================================== =========================================
   Command line option                    Description
====================================== =========================================
  --rallyConfig=<config_file_name>      name of the file with settings for pyral
  --config=<config_file_name>           ditto
  --conf=<config_file_name>             ditto
  --cfg=<config_file_name>              ditto
  --rallyUser=<foo>                     your Rally UserName
  --rallyPassword=<bar>                 password associated with the Rally UserName
  --apikey=<APIKey>                     valid Rally API Key value
  --rallyWorkspace=<bar>                Workspace in Rally you want to interact with
  --rallyProject=<bar>                  Project in Rally you want to interact with
  --ping                                boolean, ping Rally server before connection attempt?
====================================== =========================================


Prerequisites
-------------

 * Python 2.6 or 2.7 (2.7 is preferred) OR
 * Python 3.5 (this package not tested with earlier versions of Python 3.x)
 * The requests_ package, 2.0.0 or better (2.0.0 finally includes support for https proxy),
   requests 2.8.1 is recommended.
 * The six_ package.

.. _requests: http://github.com/kennethreitz/requests
.. _six: https://bitbucket/gutworth/six

Versions
--------

   **1.2.2**
       Allow for disambiguating Project amongst name duplications by means of using fully qualified path.
       Incorporated suggestion on preserving case name of custom PortfolioItem sub-item.
       Fixed discrepancy of docs versus code on default pagesize, now is actually 200 everywhere.
       Fix location of download package in GitHub repo.

   **1.2.1**
       Added mention that the six package is required.
       Fixed context setup for proper handling when a user has no default workspace/project settings.
       Corrected handling of allowedValues for attributes when the single allowedValue is a boolean value.
       Added an allowedValues.py example script.

   **1.2.0**
       Support for Python 3.5.x
       Begin deprecation sequence for pinging the Rally server before the connection attempt, 
       initially with this version, allow option on instantiation to bypass ping.
       Added ability to rankAbove, rankBelow, rankToTop, rankToBottom for an Artifact.
       Fixed defect where user has no default workspace or project.

       addAttachment now correctly handles binary file, attachment size limit increased to 50MB to match Agile Central limit.
       Exception generated when running getAllUsers when credentials are for non Subscription/Workspace Administrator has been fixed.
       Added ability to work with a single Workspace, which has beneficial performance effect for Subscriptions with a large number of Workspaces.
       Modified internal attribute handling to limit calls to get attribute's allowed values to qualifying attribute types.
       Added examples/updtag.py script.


   1.1.1 
       Modified entity.py to allow it to pass back PortfolioItem sub type instances.
       Modified rallyresp.py defect referencing non-existing req_type instance var by changing 
       reference to request_type. 
       Modified restapi.py to use user, dropped auth_user.
       Modified restapi.py to be more defensive when user has no associated UserProfile.
       Modified context.py to account for use of Cygwin in Pinger code.
       Modified restapi.py to handle encoding of attachment content to match Rally expectations.
       Modified restapi.py/entity.py to handle querying of SchedulableArtifact instances.
       Modified restapi.py to handle querying and hydrating of PortfolioItem instances more completely.
       Modified restapi.py/entity.py to provide rudimentary support for querying of RecycleBin entries.
       Modified restapi.py and added search_utils.py to provide a search method for pyral Rally instances.
       Modified rallyresp.py to better handle some boundary conditions when response body item counts 
       differ from what is stated in the TotalResultCount.
       Modified context.py to account for scenario where user's default workspace has no projects.
       Modified restapi.py/getProject to return correct project.

   1.1.0 
       Introduction of support to use Rally API Key and rallyWorkset (supercedes rallySettings). 
       Two relatively minor defects fixed dealing with internalizing environment
       vars for initialization and in retrieving Rally entity attribute allowed values.

   1.0.1
       Patch to address defect with Rally WSAPI v2.0 projects collection endpoint
       providing conflicting information.

   1.0.0
       Default WSAPI version in config is v2.0. This version is not compatible 
       with Rally WSAPI version 1.x.  
       Adjusted the RallyUrlBuilder (via RallyQueryFormatter) to be more resilient
       with respect to many more "special" characters (non-alphanumeric).
       Retrieving the meta data uses the v2.0 schema endpoint.
       No longer support a version keyword argument when obtaining a Rally instance.

   0.9.4
       Adjusted Rally __init__ to accommodate using requests 0.x, 1.x, 2.x versions.
       Factored out query building and fixed constructing multi condition queries.
       Added internal convenience method to handle a list of refs to turn them into a
       list of single key (_ref) hashes.
       Added UserIterationCapacity to known entities.
       Upped default WSAPI version in config to 1.43.
       Support using of https_proxy / HTTPS_PROXY environment variables.
       Refactored getAllUsers to include UserProfile information with fewer queries.

   0.9.3
       Fixed Pinger class to use correct ping options on Linux and Windows.
       Updated exception catching and exception raising to Python 2.6/2.7 syntax.            

   0.9.2
       Fixed getProject to take optional project name argument.
       Added HTTP header item in config.py to set Content-Type to 'application/json'.
       Added recognition of verify_ssl_cert=True/False as keyword argment to
       Rally constructor.  Explicit specification results in passing a
       verify=True/False to the underlying requests package. This can be
       useful when dealing with an expired SSL certificate.
       Upped default WSAPI version in config.py to 1.37 to support dyna-types
       (specifically PortfolioItem and sub-types).
       Modified addAttachment to conform with non-backward compatible change in Rally WSAPI 
       involving how an attachment is related to an artifact.
       Fixed defect in calculating an Attachment file size (use pre-encoded rather than post-encoded size).

       This release is intended as the final beta before a 1.0 release.

   0.9.1
       Upped default WSAPI version in config.py to 1.30
       All entities that are subclasses of WorkspaceDomainObject now have a details method
       that show the attribute values in an easy to read multiline format.
       Dropped attempted discrimination of server value to determine if it is a name or an IPv4 address.
       No longer look for http_proxy in environment, only https_proxy.
       Introduced convenience methods dealing with attachments.
       Corrected resource URL construction for the major ops (GET, PUT, POST, DEL)
       when project=None specified (useful for Workspace spanning activities).

   0.8.12
       Fixed premature exercise of iterator in initial response
    
   0.8.11
       Fixed inappropriate error message when initial connect attempt timed out. 
       Message had stated that the target server did not speak the Rally WSAPI.  
       Improved context handling with respect to workspace and project settings.
    
   0.8.10
       Attempted to bolster proxy handling.  
       Limited success as there is an outstanding issue in requests (urllib3) not 
       implementing CONNECT for https over http.

   0.8.9
       initial attempt at providing proxy support

   0.8.8  
       added warn=True/False to Rally instantiation

   0.8.7
       Initial release on developer.rallydev.com


TODO
----
* Investigate permanent location for web-access to rendered documentation
* Dynamically construct the Rally schema hierarchy economically.


License
-------

BSD3-style license. Copyright (c) 2015-2016 CA Technologies, 2010-2015 Rally Software Development.

See the LICENSE file provided with the source distribution for full details.

Author
------

* Kip Lehman  <klehman@rallydev.com>

Additional Credits
------------------

* GitHub_ for repository hosting services.
* ReadTheDocs_ for documentation hosting services.

.. _GitHub: http://github.com/
.. _ReadTheDocs: http://readthedocs.org/


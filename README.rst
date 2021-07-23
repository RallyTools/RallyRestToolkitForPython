pyral - A Python toolkit for the Rally REST API
===============================================

The `pyral <http://github.com/RallyTools/RallyRestToolkitForPython>`_ package enables you to push, pull
and otherwise wrangle the data in your Rally subscription using the popular
and productive Python language.
The ``pyral`` package provides a smooth and easy to use veneer on top
of the Rally REST Web Services API using JSON.

This package is once again branded as a 'Rally' toolkit.
The era of "Agile Central" branding is over, we'll not speak of it again.


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

If you want to pull down the latest release from standard Python package repository
(pypi.python.org) and install the package, the easiest way is to use
pip, the Python package installation utility.::

    pip install pyral

Alternatively, if you've got the tar.gz or zip distribution on hand, as long as you've
satisfied the dependency requirements on the six and requests packages, you can use
the setup mechanism.
Obtain the requests_ package and install it according to that package's directions.
As of requests-2.0.0, there is support for HTTPS over HTTP proxy via the CONNECT request.
Use of requests-2.x or better is recommended for use with pyral.
The requests_ package can be found via the Python Package Index site (http://pypi/python.org/index).
The most recent release of pyral (1.5.2) has been tested using requests 2.22.0.

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
   Python 3.8.5 [other Python interpreter info elided ...]
   >> import requests
   >> import pyral
   >> pyral.__version__
   (1, 5, 2)



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

Create a new Defect
  Copy the above boilerplate and the following code fragment and save it in a file called crdefect.py 

::

    proj = rally.getProject()

    # get the first (and hopefully only) user whose DisplayName is 'Sartorious Submitter' 
    user = rally.getUserInfo(name='Sartorius Submitter').pop(0) 

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

The ``pyral`` package uses a priority chain of files, 
environment variables and command line arguments to set the 
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
====================================== =========================================


Prerequisites
-------------

 * Python 3.6, 3.7, 3.8 or 3.9 (this package not tested with earlier versions of Python 3.x)
 * The requests_ package, 2.0.0 or better (2.0.0 finally includes support for https proxy),
   requests 2.22.0 or more recent is recommended.
 * The six_ package.

.. _requests: http://github.com/kennethreitz/requests
.. _six: https://bitbucket.org/gutworth/six

Versions
--------

   **1.5.2**
       Fixed query builder so that multi-condition queries thet include subset or range conditions 
       are constructed correctly.
       Dropped all code related to ping functionality.

   **1.5.1**
       Fixed query builder to accommodate subset criteria (in | !in) and range criteria (between | !between).
       Dropped mention of Python 3.5 as a supported version in PKG-INFO.
       Added mention of Python 3.9 as a supported version in PKG-INFO.
       Excised all mentions of AgileCentral in the docs, replaced by 'Rally'.

   **1.5.0**
       Dropped all support for Python 2.7 constructs.
       Validated support for Python 3.7 and 3.8.
       Fixed defect where attachments were not returned from getAttachments method.
       Fixed defect where the creation or update of a custom PortfolioItem sub-type did not return a
       valid pyral instance of the sub-type.
       Fixed defect in returning correct number of items when the start index is specified as an integer.
       Fixed defect where a feature item could not be added to a Milestones collection
       Fixed defect in query construction (and results) when a target attribute value contains a '&' character.

   **1.4.2**
       Fixed defect in returning RallyRESTResponse when pagesize set to 1

   **1.4.1**
       Support for TestFolderStatus attribute in TestFolder.
       Fixed defect in addCollectionItems

   **1.4.0**
       Support for PullRequest entity object (subclassed from Connection).

   **1.3.2**
       Allow for initial connection using a workspace name containing chars that need to be urlencoded.

   **1.3.1**
       Adjusted getAllowedValues so that custom fields with an allowedValues endpoint get resolved.
       Disqualifed a group of standard attributes whose allowedValue is of type COLLECTION when retrieving 
       allowed values in SchemaItem.complete(). This is primarily relevant only to attributes defined as
       Drop Down List or Multi Value Drop Down List.
       Fixed mechanism of supplying headers dict to Rally instantiation so that the X-RallyIntegration* 
       headers get overwritten with supplied headers (for name, vendor, version) to better identify the 
       origin of the integration.
       Updated official name to reference Agile Central in setup.py, mention threads keyword arg in the
       get method in the the interface.rst file.

   **1.3.0**
       Introduced automatic multi-threading for Rally.get operation to speed up retrieval of large
       result sets.  Implemented step two of the Pinger deprecation plan, ping=False is the new default.
       Increased default page size to 500.  Maximum useful page size limit is 2000 but 1000 seems
       to be the sweet spot for multithreading requests.
       Fixed Rally.getAllUsers so that non subscription admin accounts can see the user list.
       Updated recommendation for version of requests package.

   **1.2.4**
       Fixed handling of projectScopeUp and projectScopeDown keyword arguments for get operation.
       Fixed Peristable's __getattr__ method to more properly handle getting the salient item
       out of a response to a getResourceByOID request when the item retrieved is a PortfolioItem sub-type.
       Fixed defect in SchemaItemAttribute where self._allowed_values_resolved was not always set.
       Fixed defect in RallyRestResponse in __repr__ method where on a response that has no qualifying items
       an attempt is made to get the Results out of the returned response without going through the QueryResult key.

   **1.2.3**
       Fixed restapi.py Rally.getAllowedValues method to accommodate custom fields
       Allow attribute payload for put and post to have a list of pyral.Entity instances
       as values for an attribute that is of type COLLECTION.

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


   see the VERSIONS file for information pertaining to older releases


TODO
----
* Dynamically construct the Rally schema class hierarchy economically.


License
-------

BSD3-style license. Copyright (c) 2018-2021 Broadcom, Inc., 2015-2018 CA Technologies, 2010-2015 Rally Software Development.

See the LICENSE file provided with the source distribution for full details.


Warranty
--------
None. See the LICENSE file for full text regarding this issue.


Support
-------

The use of this package is on an *as-is* basis and there is no official support offered by Broadcom.
The author of this module periodically checks the GitHub repository issues for this package in the
interests of providing defect fixes and small feature enhancements as time permits, but is not obligated to
respond or take action.
Posts to Stack Overflow (http://stackoverflow.com/questions/ask?tags=rally) are another avenue to engage
others who have some exposure to ``pyral`` and might be able to offer useful information.


Author
------

* Kip Lehman  <kip.lehman@broadcom.com>


Additional Credits
------------------

* GitHub_ for repository hosting services.
* ReadTheDocs_ for documentation hosting services.

.. _GitHub: http://github.com/
.. _ReadTheDocs: http://readthedocs.org/


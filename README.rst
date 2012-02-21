pyral - A Python toolkit for the Rally REST API
===============================================


The `pyral <http://github.com/Rallydev/pyral>`_ package enables you to push, pull
and otherwise wrangle the data in your Rally subscription using the popular
and productive Python language.
The ``pyral`` package provides a smooth and easy to use veneer on top
of the Rally REST Web Services API using the JSON flavored variant.

.. contents::

Getting started
---------------

Rally has created a Python package that you can quickly leverage to interact with the data in your 
subscription via the REST web services API.  You can create, read, update, and delete the common 
artifacts and other entities via the Rally REST toolkit for Python.

Download
````````

Files are available at the `download page`_ .

.. _download page: http://pypi.python.org/pypi/pyral

The git repository is available at http://github.com/Rallydev/pyral


Installation
````````````

Obtain the requests_ package and install it according to that package's directions.

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
   Python 2.6.5 [other Python interpreter info elided ...]
   >> import requests
   >> import pyral
   >> pyral.__version__
   (0, 8, 9)



30 second highlight
```````````````````

Since Python is a very flexible and extensible language, we were able to make access to the object model 
extremely simple. For example, if you have a a UserStory instance returned by a ``pyral`` operation 
assigned to the name **story**, the following code iterates over the tasks.

::

    for task in story.Tasks:
       print task.Name

There is no need to make a separate call to fetch all the tasks for the story.
When you follow domain model attributes in the Python code, the Python toolkit for the 
Rally REST API machinery automatically loads in the necessary objects for you.


Full Documentation
``````````````````

The complete documentation for the Python toolkit for the Rally REST API is in the doc/build/html 
subdirectory in the repository.  The rendered version of this is also available at
http://readthedocs.org/docs/pyral.


Sample code
-----------

Common setup code ::

  import sys
  from pyral import Rally, rallySettings
  options = [arg for arg in sys.argv[1:] if arg.startswith('--')]
  args    = [arg for arg in sys.argv[1:] if arg not in options] 
  server, user, password, workspace, project = rallySettings(options)
  rally = Rally(server, user, password, workspace=workspace, project=project)
  rally.enableLogging('mypyral.log')

Show a TestCase identified by the **FormattedID** value.
  Copy the above boilerplate and the following code fragment and save it in a file named gettc.py

::

    query_criteria = 'FormattedID = "%s"' % args[0]
    response = rally.get('TestCase', fetch=True, query=query_criteria)
    if response.errors:
        sys.stdout.write("\n".join(errors))
        sys.exit(1)
    for testcase in response:  # there should only be one qualifying TestCase  
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
  WORKSPACE                            Rally Workspace
  PROJECT                              Rally Project
  VERSION                              Rally REST Web Services API version
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
  --rallyWorkspace=<bar>                Workspace in Rally you want to interact with
  --rallyProject=<bar>                  Project in Rally you want to interact with
  --rallyVersion=<bar>                  Rally REST Web Services API version
====================================== =========================================


Prerequisites
-------------

 * Python 2.6 or 2.7
 * The most excellent requests_ package, 0.8.2 or better

.. _requests: http://github.com/kennethreitz/requests

TODO
----

* Python 3.2 + support

* Create (better) documentation

* Expand the repertoire of example scripts

* Refactor the source code to make use decorators in pyral.restapi, 
  dynamically construct the Rally schema hierarchy economically.


License
-------

BSD3-style license. Copyright (c) 2010-2012 Rally Software Development.

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


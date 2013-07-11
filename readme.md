## License

Copyright (c) 2002-2013 Rally Software Development Corp. All Rights Reserved. Your use of this Software is governed by the terms and conditions of the applicable Subscription Agreement between your company and Rally Software Development Corp.

## Warranty

The Rally REST API for .NET is available on an as-is basis. 

## Support

Rally Software does not actively maintain this toolkit.  If you have a question or problem, we recommend posting it to Stack Overflow: http://stackoverflow.com/questions/ask?tags=rally 

## Introduction

The Python toolkit for the Rally REST API enables you to push, pull and otherwise wrangle the data in your 
Rally subscription using the popular and productive Python language.   
The toolkit provides a smooth and easy to use veneer on top of the Rally REST Web Services API.

Topics contained in Python toolkit for Rally REST API:

*   [Getting started](#start)
*   [Validating Python setup](#validate)
*   [Using Python with a proxy or firewall](#proxy)
*   [Configuration values setup](#config)
*   [Sample code](#sample)

<a name="start"></a>

## Getting started

<p>Rally has created a Python package that you can quickly leverage to interact with the data in your 
subscription via the REST web services API. 
You can create, read, update, and delete the common artifacts and other entities via the Python toolkit for Rally REST API.

The complete documentation for the Python toolkit for Rally REST API can be viewed at 
[Read the Docs (for pyral)](http://readthedocs.org/docs/pyral/en/latest).  The source and build for the documentation is in the doc/build/html subdirectory in the distribution.  The information in this document provides the necessary installation instructions and covers some of the highlights of  using the toolkit.

Since Python is a very flexible and extensible language, we were able to make access to the object model 
extremely simple. For example, if you have a a UserStory instance returned by a pyral operation assigned to 
the name `story`, the following code iterates over the tasks.

`
for task in story.Tasks:
    print task.Name
`

There is no need to make a separate call to fetch all the tasks for the story. When you follow domain model values in the Python code, 
the Python toolkit for Rally REST API machinery automatically loads in the necessary objects for you.

To start using the toolkit, you must first install Python.
The toolkit package has been developed and tested with version 2.6 of Python.
Click on the link for the [Python 2.6.6 installer for Windows](http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi).
This version of the Python toolkit for Rally REST API makes use of Kenneth Reitz's excellent [requests](http://pypi.python.org/pypi/requests/0.9.3) package.  
The `requests` package in turn requires the use of the [certifi](http://pypi.python.org/pypi/certifi/0.0.8) package.  At this time you'll need to use version 0.9.3 of the `requests` package.  Although there are later versions of `requests`, the pyral package has not been tested with those versions and we do not support any version of pyral that doesn't use the `requests-0.9.3 / certifi-0.0.8` package combination.
Use any of the standard means of Python module/package installation, whether it be distutils, easy_install, 
pip or distribute to install the `requests` package.

Then install the Python toolkit for Rally REST API package by unpacking the distribution zipfile or tarball and
executing `python setup.py install` (using whatever other options you need for your local environment)
.

<a name="validate"></a>

## Validating Python setup

If you are experiencing any issues when using the Python toolkit for Rally REST API, here are some items to try/verify:

1.  Does your machine recognize the python command?

<p>Type "python -v" from the command line to verify.If this returns nothing (and you know you installed Python on your machine), then set your environmentpath to include Python.
    *   Windows users: [Review this article from Microsoft.](http://www.microsoft.com/resources/documentation/windows/xp/all/proddocs/en-us/environment_variables.mspx?mfr=true)*   Unix users: [Review this article.](https://kb.iu.edu/data/acar.html)

    <li>What version of Python are you using?

    Type "python -v" from the command line to verify the version of Python you are running.This version of the Python toolkit for Rally REST API was developed and tested with Python 2.6, and has been occasionally tested with Python 2.7.No prognostications regarding correct operation are offered regarding Python 2.5 or 3.2.

2.  Can you import the requests package?

Run python in a terminal window (console window) by executing python on the command line.
   Python 2.6.6 (&lt;build version and date verbiage&gt;)
       Type "help", "copyright", "credits" or "license" for more information
       &gt;&gt;&gt; `import requests`
       &gt;&gt;&gt;
       If you observe an exception, and you have successfully installed the `requests` package,
   adjust your PYTHONPATH environment variable to include the directory/folder where the package was deposited.

3.  Can you import the pyral package?

Run python in a terminal window (console window) by executing python on the command line.
   Python 2.6.6 (&lt;build version and date verbiage&gt;)
       Type "help", "copyright", "credits" or "license" for more information
       &gt;&gt;&gt; `import pyral`
       &gt;&gt;&gt;
       If you observe an exception, and you have successfully installed the `pyral` package,
   adjust your PYTHONPATH environment variable to include the directory/folder where the package was deposited.

4.  Do you use a proxy to connect to Rally?

<div style="border: 2px gray dashed; background-color: #FFDDFF; width: 100%; padding: 10px;">At this point in time, the requests package machinery does not correctly support HTTPS over HTTP which is exactly what a proxy must do to connect to Rally since all URLs are HTTPS based.  The maintainers of the the requests package are aware of this situation and there are code fixes for the underlying dependency (urllib3) that are currently being evaluated for inclusion.   When the requests package incorporates the code to support proxy correctly, we'll alter the description here to address the simple step you'd have to take (setting an environment variable) for pyral to work in a proxied environment.</div>

<!--

If so, you will need to setup your Python environment for a proxy.   See this below for instructions on setting this up.

<!--
<a name="proxy"></a>

## Using Python with a proxy or firewall

<p>To have Python packages, scripts, etc. access the internet with a proxy in Windows:

1.  Go to System Properties - Advanced - Environment Variables.
2.  Create the following environment variables: **HTTP_PROXY** and **HTTPS_PROXY**.
3.  The value for each variable is generally the same:

    `http://ipaddress:port/`
<p>For Linux/MacOSX, set the **HTTP_PROXY** and **HTTPS_PROXY** environment variables and export them.

<div id="nav">Note: You will need to restart Windows and Python to see the new environment variable.</div>
-->

<a name="config"></a>

## Configuration values setup

<p>
 The pyral module provides several ways of specifying Rally access information 
  (the full description is in the docs).  One convenient and easy means of doing this
  is to use a configuration file with this information embeded in a file named with a '.cfg' suffix.
  Simply use a text editor and place the following information in a file 
     (using values appropriate for you):

`
     SERVER    = rally1.rallydev.com  
     USER      = your_Rally_user_name@your_company.com
     PASSWORD  = your_Rally_password
     WORKSPACE = Your Rally Workspace 
     PROJECT   = Your Rally Project 
`

 The WORKSPACE and PROJECT entries are optional, if you don't specify them, pyral uses your default Workspace and / or Project.
The SERVER value should be specified according to your intended Rally instance, which might be trial.rallydev.com, community.rallydev.com or another server if you are using an on-premise version of Rally.

### Using a config file on invocation of a program using pyral

  To use a config file as mentioned above when running a program using pyral, use the 
      --conf=<config_file_name> argument syntax on the command line

  Note that you do not need to specify the '.cfg' suffix portion of your configuration file name.
  Also, pyral offers some fairly lenient syntax when specifying the --conf part. 
  You can also use --config=... or --cfg=... or --rallyConfig=... in addition to the --conf=... syntax.

  Within your Python script using pyral, you'll need to import rallySettings and have some code such as
  the contents of the Common setup code in the Sample Code section immediately below this section.

  Here's an example of the calling sequence that uses the contents of a config file named sample.conf:

`
    python test_prog.py --conf=sample
`

<a name="sample"></a>

## Sample Code

<p>Included below are five code samples for using the Python toolkit preceded by the common boilerplate you'll use for setup:

### Common setup code 

`
  import sys
  from pyral import Rally, rallySettings
  options = [arg for arg in sys.argv[1:] if arg.startswith('--')]
  args    = [arg for arg in sys.argv[1:] if arg not in options] 
  server, user, password, workspace, project = rallySettings(options)
  rally = Rally(server, user, password, workspace=workspace, project=project)
  rally.enableLogging('mypyral.log')
`

### Show a TestCase identified by the _FormattedID_

    Copy the above boilerplate and the following code fragment and save it in a file called gettc.py .  

`
 query_criteria = 'FormattedID = "%s"' % args[0]
 response = rally.get('TestCase', fetch=True, query=query_criteria)
 if response.errors:
     sys.stdout.write("\n".join(errors))
     sys.exit(1)
 for testCase in response:  # there should only be one qualifying TestCase  
     print "%s %s %s %s" % (testCase.Name, testCase.Type,  
                            testCase.DefectStatus, testCase.LastVerdict)
`

         Run it by providing the FormattedID value of your targeted TestCase as a command line argument, ie., python gettc.py TC1184 

### Get a list of workspaces and projects for your subscription

       Copy the above boilerplate and the following code fragment and save it in a file called wksprj.py .

`
 workspaces = rally.getWorkspaces()
 for wksp in workspaces:
     print "%s %s" % (wksp.oid, wksp.Name)
     projects = rally.getProjects(workspace=wksp.Name)
     for proj in projects:
         print "    %12.12s  %s" % (proj.oid, proj.Name)
`

  Run the script, ie., python wksprj.py 

### Get a list of all users in a specific workspace

       Copy the above boilerplate and the following code fragment and save it in a file called allusers.py .  

`
 all_users = rally.getAllUsers() 
 for user in all_users:
     tz    = user.UserProfile.TimeZone or 'default' 
     role = user.Role or '-No Role-'  
     values = (int(user.oid), user.Name, user.UserName, role, tz) 
     print("%12.12d %-24.24s %-30.30s %-12.12s %s" % values)
`

         Run the script, ie., python allusers.py 

### Create a new Defect

       Copy the above boilerplate and the following code fragment and save it in a file called crdefect.py .  

`
 name, severity, priority, description = args[:4]
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
`

        Run the script, ie.,
        python crdefect.py &lt;Name&gt; &lt;severity&gt; &lt;priority&gt; &lt;Description&gt;

         &nbsp;&nbsp; making sure to provide valid severity and priority values for your workspace. 

### Update a Defect

       Copy the above boilerplate and the following code fragment and save it in a file called updefect.py .  

`
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

 print "Defect updated"
`

    Run the script, ie.,
    python updefect.py &lt;Defect FormattedID&gt; &lt;customer&gt; &lt;target_date&gt; &lt;"notes text..."&gt; 

   

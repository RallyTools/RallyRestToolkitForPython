

Python toolkit for the Rally REST API
=====================================

Rally supports a REST API that enables you to retrieve representations of 
entities in Rally, create entities in Rally, update existing entities in Rally and
with proper permissions, delete entities in Rally.

Once you have the *pyral* package installed, all you need is a valid subscription 
to Rally, working credentials and the name of
the workspace and project you want to interact with and you're on your way!

For more information on obtaining a Rally subscription, visit the Rally_ website.

For more information on how workspaces and projects in Rally are set up and configured, consult 
the Rally documentation available via the 'Help' link from the Rally landing page 
displayed after your initial login.

.. _Rally: http://www.rallydev.com

Simple Use
==========

Here's a prototype of simple use of the **pyral** package.::

    import sys

    from pyral import Rally, rallySettings

    options = [opt for opt in sys.argv[1:] if opt.startswith('--')]

    rally = Rally(*rallySettings(options))
    rally.enableLogging('rally.simple-use.log')

    response = rally.get('Release', fetch="Project,Name,ReleaseStartDate,ReleaseDate",
                         order="ReleaseDate")

    for release in response:
        rlsStart = rls.ReleaseStartDate.split('T')[0]  # just need the date part
        rlsDate  = rls.ReleaseDate.split('T')[0]       # ditto
        print "%-6.6s  %-16.16s   %s  -->  %s" % \
              (rls.Project.Name, rls.Name, rlsStart, rlsDate)


Rally Data Model
================

All Rally entities belong to a hierarchical data model and every Rally entity ultimately
is a descendent of the PersistableObject class.  There are several branches in the data
model, and each branch has its own set of attributes differentiated according to the 
functional capabilities and information tracking needs that characterize the branch.
For more information on the Rally data model, consult the Rally documentation available 
via the 'Help' link from the Rally page displayed after the initial login.


Rally Entities and Artifacts
============================

In the Rally vernacular, a logical entity is  called a *type*.  Some examples of Rally
*types* are UserStory, Defect, Release, UserProfile.  There is a subset of 
*types* that are usually what a user of pyral will be interested in called *artifacts*.
An *artifact* is either a UserStory, Defect, Task, DefectSuite, TestSet or TestCaseResult.
The Python toolkig for the Rally REST API (pyral) is primarily oriented towards operations with artifacts.
But, it is not limited to those as it is very possible view/operate on other Rally 
entities such as Workspace, Project, UserProfile, Release, Iteration, TestFolder, Tag and
others.

Full CRUD capability
====================

The Python toolkit for the Rally REST API offers the full spectrum of CRUD capabilities that the 
credentials supplied for your subscription/workspace/project permit.  While the Rally
REST API itself doesn't support bulk operations, there are example usages of 
**pyral** that you can adapt to offer the end-user or scriptwriter the
capability of specifying ranges of identifiers of artifacts for querying/updating/deleting.

Rally Introspection
===================

The Python toolkit for the Rally REST API makes it easy to obtain the names of Rally types (entities)
and the attributes associated with each type.  You can also use pyral capabilities
to obtain the list of allowed values for Rally type attributes that have a pre-allocated
list of values.

Queries and Results
===================

The Rally REST API has two interesting characteristics that the Python toolkit for the Rally REST API insulates the scriptwriter from having to deal with.  The first is that the Rally REST API
has a maximum "pagesize" of 200 records to limit volume and prevent unwarranted hijacking of the
Rally SaaS servers.  But, having script writers deal with this directly to obtain further 
"pages" would be burdensome and out of character with the mainstream of Python interfaces
to SaaS services.  The Python toolkit for the Rally REST API (**pyral**) takes care 
of the paging transparently, allowing the scriptwriter to treat a result set as an iterator, 
merely looping through the results without any indication of any sequence of further 
requests on the Rally server.

The second characteristic is that the Rally REST API for some queries and results returns
not a scalar value but a reference to yet another entity in the Rally system.  A Project or
a Release are good examples of these.  Say your query specified the retrieval of some UserStories,
and you listed the Project as a field to return with these results.  From an end-user perspective,
seeing the project name as opposed to to an URL with an ObjectID value would be far more intuitive.  

The Python toolkit for the Rally REST API offers this sort of intuitive behavior by "chasing" the URL 
to obtain the more human friendly and intuitive information for display.  This sort of behavior is 
also present in so-called "lazy-evaluation" of entity attributes that may be containers as well
as references.  The scriptwriter merely has to refer to the attribute with the dot ('.') notation
and **pyral** takes care of the communication with the Rally server 
to obtain the value.  There are two significant advantages to this, one being lightening 
the load on the server with the reduction of data returned and the other being easy and 
intuitive attribute access syntax.


#!/usr/bin/env python

#############################################################################
#
# build_dist.py -- Build the pyral distribution package for shipment
#
#############################################################################

import sys, os
import types
import tarfile
import zipfile
import shutil
import re

PACKAGE_NAME = "pyral"
VERSION      = "1.3.1"

AUX_FILES  = ['MANIFEST.in', 
              'PKG-INFO', 
              'LICENSE', 
              'README.short', 
              'README.rst', 
              'setup.py', 
              'template.cfg', 
              'rallyfire.py'
             ]
EXAMPLES   = ['getitem.py', 
              'periscope.py', 
              'showdefects.py', 
              'crtask.py', 
              'uptask.py',
              'statecounts.py',
              'repoitems.py',
              'get_schema.py',
              'typedef.py',
              'allowedValues.py', 
              'wkspcounts.py',
              'builddefs.py',
              'creattach.py',
              'get_attachments.py',
              'get_milestones.py',
              'get_schedulable_artifacts.py',
              'add_tcrs.py',
              'defrevs.py',
              'updtag.py',
              'addtags.py'
             ]
DOC_FILES  = ['doc/Makefile',
              'doc/source/conf.py',
              'doc/source/index.rst',
              'doc/source/overview.rst',
              'doc/source/interface.rst',
              'doc/build/html/genindex.html',
              'doc/build/html/index.html',
              'doc/build/html/overview.html',
              'doc/build/html/interface.html',
              'doc/build/html/search.html',
              'doc/build/html/searchindex.js',
              'doc/build/html/objects.inv',
              'doc/build/html/_sources',
              'doc/build/html/_static',
             ]

#
# The TEST_FILES are **NOT** placed into the distribution packages
#
TEST_FILES = ['test/rally_targets.py', 
              'test/test_conn.py',
              'test/test_context.py',
              'test/test_convenience.py',
              'test/test_inflation.py',
              'test/test_field_access.py',
              'test/test_workspaces.py'
              'test/test_allowed_values.py',
              'test/test_wksprj_setting.py',
              'test/test_query.py',
              'test/test_big_query.py',
              'test/test_attachments.py',
              'test/test_ranking.py'
              'test/test_search.py',
             ]

################################################################################

def main(args):
    pkgcfg = package_meta('setup.py')
    #peek_in_to_pkg(pkgcfg)
    pkg_info = pkg_info_content(pkgcfg)
    pifi = save_pkg_info(".", 'PKG-INFO', pkg_info)

    tarball = make_tarball(PACKAGE_NAME, VERSION, AUX_FILES, EXAMPLES, DOC_FILES)
    print(tarball)

    zipped = make_zipfile(PACKAGE_NAME, VERSION, AUX_FILES, EXAMPLES, DOC_FILES)
    print(zipped)

    zf = zipfile.ZipFile(zipped, 'r')
    for info in zf.infolist():
        #print(info.filename, info.date_time, info.file_size, info.compress_size)
        if info.file_size:
            reduction_fraction = float(info.compress_size) / float(info.file_size)
        else:
            reduction_fraction = 0.0
        reduction_pct = int(reduction_fraction * 100)
        print("%-52.52s   %6d (%2d%%)" % (info.filename, info.compress_size, reduction_pct))

    # in order to get a wheel file built, the python used has to have available a setup.py
    # that exposes a bdist_wheel method, which in versions of python beyond 2.7, like 3.5., 3.6, etc
    # you'll need to have done a 'pip install wheel' which sets up the necessary infrastructure.
    os.system('python setup.py bdist_wheel')
    wheel_file = "%s-%s-py2.py3-none-any.whl" % (PACKAGE_NAME, VERSION)
    # the wheel_file gets written into the dist  subdir by default, no need for a copy...

    store_packages('dist',  [tarball])
    store_packages('dists', [tarball, zipped])

    doc_dir = 'doc/build/html'
    doc_files = [path.split('/')[-1] for path in DOC_FILES if path.startswith(doc_dir)]
    webdocs_zip = make_online_docs_zipfile(PACKAGE_NAME, VERSION, doc_dir, doc_files)
    webdocs_location = os.path.join(doc_dir, webdocs_zip)
    store_packages('dist', [webdocs_location])

################################################################################

def store_packages(subdir, files):
    for file in files:
        if os.path.exists(file):
            leaf_name = os.path.basename(file)
            shutil.copy(file, '%s/%s' % (subdir, leaf_name))
        else:
            problem = "No such file found: {0} to copy into {1}".format(file, subdir)
            sys.stderr.write(problem)

################################################################################

def package_meta(filename):

    if not os.path.exists(filename):
        raise Exception('No such file: %s' % filename)
    with open(filename, 'r') as pcf:
        content = pcf.read()
    chunk, setup = re.split('setup\(', content, maxsplit=1, flags=re.M)
    consties = [line for line in chunk.split("\n") 
                      if (len(line) > 0 and line[0] == " ") or re.search(r'^[A-Z]', line)]
    assignments = "\n".join(consties)

    #print(assignments)
    pkgcfg = types.ModuleType('pkgcfg')  # make a new empty module, internally.. no file created
    exec(assignments, pkgcfg.__dict__)   # now populate the module with our assignments
    sys.modules['pkgcfg'] = pkgcfg
    return pkgcfg

################################################################################

def indentified_text(source_body):
    """
        The source_body should be a single string with embedded newline chars.
        This function splits the string on the newline chars, yielding a list
        of strings.  The indentation should only be performed lines after the first
        line.  The first line shall have no indentation performed.
        Return the result as a single string.
    """
    lines = source_body.split("\n")
    indented = ['        %s' % line for ix, line in enumerate(lines) if ix > 0]
    indented.insert(0, lines[0])    
    return "\n".join(indented)


def pkg_info_content(pkgcfg):
    with open(pkgcfg.SHORT_DESCRIPTION, 'r') as sdf: 
        short_desc = indentified_text(sdf.read())
    meta_ver    =   'Metadata-Version: 1.1'
    name        =   'Name: %s'       % pkgcfg.PACKAGE
    version     =   'Version: %s'    % pkgcfg.VERSION 
    summary     =   'Summary: %s'    % pkgcfg.OFFICIAL_NAME
    homepage    =   'Home-page: %s'  % pkgcfg.GITHUB_SITE
    author      =   'Author: %s'     % pkgcfg.AUTHOR
    license     =   'License: %s'    % pkgcfg.LICENSE
    download    =   'Download-URL: %s' % pkgcfg.DOWNLOADABLE_ZIP
    desc        =   'Description: %s'  % short_desc
    keywords    =   'Keywords: %s'   % ",".join(pkgcfg.KEYWORDS)
    requires    =  ['Requires: %s'   % reqmt for reqmt in pkgcfg.REQUIRES]
    platform    =   'Platform: %s'   % pkgcfg.PLATFORM
    classifiers =  ['Classifier: %s' % item for item in pkgcfg.CLASSIFIERS]

    pki_items = [meta_ver, name, version, summary, homepage, author, license,
                 download, desc, keywords, 
                 "\n".join(requires), platform, "\n".join(classifiers)
                ]
    pkg_info = "\n".join(pki_items)
    return pkg_info
    

def save_pkg_info(directory, filename, pkg_info):
    full_path = os.path.join(directory, filename)
    with open(full_path, 'w') as pif:
        pif.write(pkg_info)
        pif.write("\n")
    return full_path

################################################################################

def make_tarball(pkg_name, pkg_version, base_files, example_files, doc_files):

    base_dir = '%s-%s' % (pkg_name, pkg_version)

    #tf_name  = '%s-%s.tar' % (pkg_name, pkg_version)
    tgz_name = '%s-%s.tar.gz' % (pkg_name, pkg_version)
    
    tf = tarfile.open(tgz_name, 'w:gz')
    for fn in base_files:
        tf.add(fn, '%s/%s' % (base_dir, fn))

    for fn in (pf for pf in os.listdir(pkg_name) if pf.endswith('.py')):
        pkg_file = '%s/%s' % (pkg_name, fn)
        tf.add(pkg_file, '%s/%s/%s' % (base_dir, pkg_name, fn))

    for fn in example_files:
        exf_path = 'examples/%s' % fn
        tf.add(exf_path, '%s/%s' % (base_dir, exf_path))

    for doc_item in doc_files:
        full_item_path = '%s/%s' % (base_dir, doc_item)
        tf.add(doc_item, full_item_path)

    tf.close()

    return tgz_name

################################################################################

def make_online_docs_zipfile(pkg_name, pkg_version, doc_dir, doc_files):
    zf_name = '%s-%s.docs.html.zip' % (pkg_name, pkg_version)
    cur_dir = os.getcwd()
    os.chdir(doc_dir)
    zf = zipfile.ZipFile(zf_name, 'w')
    for fn in doc_files:
        zf.write(fn, fn, zipfile.ZIP_DEFLATED)
    zf.close()

    ##  The following is what has been done before on the command line, when you
    ## get the recursion opt on the above logic you can drop the os.system call
    os.system("zip %s -r %s" % (zf_name, " ".join(doc_files)))
    ##

    os.chdir(cur_dir)
    return zf_name

################################################################################

def make_zipfile(pkg_name, pkg_version, base_files, example_files, doc_files):
    base_dir = '%s-%s' % (pkg_name, pkg_version)

    zf_name = '%s.zip' % base_dir

    zf = zipfile.ZipFile(zf_name, 'w')

    for fn in base_files:
        zf.write(fn, '%s/%s' % (base_dir, fn), zipfile.ZIP_DEFLATED)

    for fn in (pf for pf in os.listdir(pkg_name) if pf.endswith('.py')):
        pkg_file = '%s/%s' % (pkg_name, fn)
        zf.write(pkg_file, '%s/%s/%s' % (base_dir, pkg_name, fn), zipfile.ZIP_DEFLATED)

    for fn in example_files:
        exf_path = 'examples/%s' % fn
        zf.write(exf_path, '%s/%s' % (base_dir, exf_path), zipfile.ZIP_DEFLATED)

    for doc_item in doc_files:
        if os.path.isfile(doc_item):
            zf.write(doc_item, '%s/%s' % (base_dir, doc_item), zipfile.ZIP_DEFLATED)
        elif os.path.isdir(doc_item):
            sub_items = os.listdir(doc_item)
            for sub_item in sub_items:
                zf.write('%s/%s' % (doc_item, sub_item), '%s/%s/%s' % (base_dir, doc_item, sub_item), zipfile.ZIP_DEFLATED)
                
    zf.close()

    return zf_name

################################################################################
################################################################################

if __name__ == "__main__":
    main(sys.argv[1:])


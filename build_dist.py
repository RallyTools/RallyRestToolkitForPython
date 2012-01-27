#!/opt/local/bin/python2.6

#############################################################################
#
# build_dist.py -- Build the pyral distribution package for shipment
#
#############################################################################

import sys, os
import tarfile
import zipfile

PACKAGE_NAME = "pyral"
VERSION      = "0.8.8"

AUX_FILES  = ['MANIFEST.in', 
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
              'uptask.py'
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
TEST_FILES = ['test/test_conn.py',
              'test/test_query.py',
              'test/test_inflation.py',
              'test/test_convenience.py',
             ]

################################################################################

def main(args):
    tarball = make_tarball(PACKAGE_NAME, VERSION, AUX_FILES, EXAMPLES, DOC_FILES)
    print tarball

    zipped = make_zipfile(PACKAGE_NAME, VERSION, AUX_FILES, EXAMPLES, DOC_FILES)
    print zipped

    zf = zipfile.ZipFile(zipped, 'r')
    for info in zf.infolist():
        #print info.filename, info.date_time, info.file_size, info.compress_size
        reduction_fraction = float(info.compress_size) / float(info.file_size)
        reduction_pct = int(reduction_fraction * 100)
        print "%-52.52s   %6d (%2d%%)" % (info.filename, info.compress_size, reduction_pct)

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



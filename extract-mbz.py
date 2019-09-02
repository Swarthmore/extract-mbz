#!/usr/bin/python
# COLGATE - DWheeler - WheelerDA @ GitHub
# 2014-07-18 - Initial release 0.5 Alpha minus
##
# 2018-01-31 - Updated to Python 3, Swarthmore College

###########################################################################
##                                                                       ##
# Moodle .mbz Extract Utility
##                                                                       ##
# python 3
##                                                                       ##
###########################################################################
##                                                                       ##
## NOTICE OF COPYRIGHT                                                   ##
##                                                                       ##
## This program is free software; you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation; either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details:                          ##
##                                                                       ##
##          http:##www.gnu.org/copyleft/gpl.html                         ##
##                                                                       ##
###########################################################################

import xml.etree.ElementTree as etree
import fnmatch
import shutil
import os
import re
import time
import time
import sys
from slugify import slugify
import zipfile
import tarfile
import io


def locate(pattern, root=os.curdir):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.'''

    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files, pattern):
            yield os.path.join(path, filename)


# Initialize and add header to log file
# Log file is created in-memory
# Return the StringIO object
def initializeLogfile():

    logfile = io.StringIO()

    logfile.write('Moodle Extract')
    logfile.write("Course: " + shortname + " (" + fullname + ")\n")
    logfile.write(" Format: " + format + "\n")
    logfile.write("Extract started: " + time.strftime('{%d-%m-%Y %H:%M:%S}') + "\n")
    logfile.write("------------------------\n")

    return logfile


# Given an mbz and a path within in the mbz file, return its content, based on the type of mbz file
def get_mbz_content(mbz, path):
    if mbz['type'] == 'tar':
        return mbz['content'].extractfile(path).read()
    else:
        return mbz['content'].read(path)


# Unique filename
# From http://code.activestate.com/recipes/577200-make-unique-file-name/
# By Denis Barmenkov <denis.barmenkov@gmail.com>
def add_unique_postfix(zipfile, new_filepath):

    if not new_filepath in zipfile.namelist():
        return new_filepath

    path, name = os.path.split(new_filepath)
    name, ext = os.path.splitext(name)

    make_fn = lambda i: os.path.join(path, '%s(%d)%s' % (name, i, ext))

    i = 1
    while i < 1000:
        uni_fn = make_fn(i)
        if not uni_fn in zipfile.namelist():
            return uni_fn
        i += 1

    return None


# Given a filename with extension, slugify the base part of the filename
def make_slugified_filename(filename):
    path, name = os.path.split(filename)
    name, ext = os.path.splitext(filename)
    return os.path.join(path, "%s%s" % (slugify(name), ext))


# Open the mbz file and access the contents
# Depending on the version of Moodle, the mbz file is either a zip file or a tar.gz file
def unzip_mbz_file(mbz_filepath):

    # mbz dict contains information about the mbz file
    mbz = dict();

    # Older version of mbz files are zip files
    # Newer versions are gzip tar files
    # Figure out what file type we have and access appropriately

    if zipfile.is_zipfile(mbz_filepath):
        mbz['type'] = 'zip'
        mbz['content'] = zipfile.ZipFile(mbz_filepath, 'r')
        mbz['filelist'] = mbz['content'].namelist()

    elif tarfile.is_tarfile(mbz_filepath):
        mbz['type'] = 'tar'
        mbz['content'] = tarfile.open(mbz_filepath)
        mbz['filelist'] = mbz['content'].getnames()

    else:
        print("Can't figure out what type of archive file this is")
        return -1

    return mbz




# Process Course Files
# Copy files from original mbz to folders within the new zip file
def process_course_files(mbz):

    files_xml = get_mbz_content(mbz, "files.xml")
    fileTree = etree.fromstring(files_xml)
    itemCount = 0

    print ("\nProcessing Course Files...") 
    mbz['logfile'].write("\n============\nCourse Files\n=============\n")

    for rsrc in fileTree:
        fhash = rsrc.find('contenthash').text
        fname = rsrc.find('filename').text
        fcontext = rsrc.find('component').text

        mbz['logfile'].write ( "{0} -- {1} -- {2}\n".format(fname, fhash, fcontext))
        hit = pattern.search(fname)

        if hit:
            itemCount += 1
            files = filter(lambda x: fhash in x, mbz['filelist'])
            mbz['logfile'].write("|FILES")

            for x in files:
                print(x)
                destination_in_zip = add_unique_postfix(zf, os.path.join(fcontext,fname))
                zf.writestr(destination_in_zip , get_mbz_content(mbz,x))
            else:
                mbz['logfile'].write("NO FILES|\n")


    print ("Extracted files = {0}".format(itemCount))
    mbz['logfile'].write ("\nExtracted files = {0}\n".format(itemCount))





# /Functions ###########################################################################
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
print("Extract Moodle content from mbz backup")

nArgs = len(sys.argv)

if nArgs < 2:
    print("usage: extract <path to Moodle backup mbz file> \n")
    sys.exit()

if sys.argv[1] == '?':
    print("help:")
    print("\tusage: extract <path to Moodle backup mbz file>")
    print("\n\tcurrent objects extracted: Files, URLs")
    print("\tcurrent file types extracted: pdf|png|gif|zip|rtf|sav|mp3|mht|por|xlsx?|docx?|pptx?\n")
    sys.exit()


mbz_filepath = str(sys.argv[1])

if not os.path.exists(mbz_filepath):
    print("\nERROR: " + mbz_filepath + " does not appear to exist\n")
    sys.exit()

mbz = unzip_mbz_file(mbz_filepath)

# Check to make sure necessary files exist in the mbz file
if (not 'moodle_backup.xml' in mbz['filelist']) or (not "course/course.xml" in mbz['filelist']):
    print("\"" + mbz_filepath + "\"" +
          " doesn't appear to be a valid mbz Moodle backup file")
    sys.exit()


pattern = re.compile(
    '^\s*(.+\.(?:pdf|png|gif|jpg|jpeg|zip|rtf|sav|mp3|mht|por|xlsx?|docx?|pptx?))\s*$', flags=re.IGNORECASE)

# Get Course Info

course_xml = ""
moodle_backup_xml = ""
if mbz['type'] == 'tar':
    course_xml = mbz['content'].extractfile("course/course.xml").read()
    moodle_backup_xml = mbz['content'].extractfile("moodle_backup.xml").read()
else:
    course_xml = mbz['content'].read("course/course.xml")
    moodle_backup_xml = mbz['content'].read("moodle_backup.xml")


courseTree = etree.fromstring(course_xml)
shortname = courseTree.find('shortname').text
fullname = courseTree.find('fullname').text
crn = courseTree.find('idnumber').text
format = courseTree.find('format').text

# destinationRoot      = os.path.join(unicode(mbz['fullpath_to_unzip_dir']), slugify(unicode(shortname)))

# The result of the program is a zip file containing the mbz content
# THe zip file will be built in memory, using StringIO
output_zip = io.BytesIO()
zf = zipfile.ZipFile(output_zip, "a")

# Copy HTML support files to extracted folder
script_dir = os.path.dirname(os.path.realpath(__file__))
# Add css file
zf.write(os.path.join(script_dir, "tachyons.css"), "tachyons.css")


# Get Moodle backup file info
backupTree = etree.fromstring(moodle_backup_xml)
activities = backupTree.find("information").find("contents").find("activities")

ts = time.time()

print("Extracting backup of " + shortname + " @ " + time.strftime('{%d-%m-%Y %H:%M:%S}'))

mbz['logfile'] = initializeLogfile()


# Begin HTML page
start_of_html = '''
<html>
    <head>
        <title>Moodle Backup Extract</title>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
        <link rel="stylesheet" type="text/css" href="tachyons.css">
    </head>
    <body class="pa3 sans-serif fw1">'''

html_index_page = io.StringIO()
html_index_page.write(start_of_html)
html_index_page.write("<h2 class=''>%s</h2><h4 class=''>%s</h4>" % (fullname, shortname))

html_header = '''
<head>
	<title>Moodle Backup Extract</title>
	<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
	<link rel="stylesheet" type="text/css" href="tachyons.css">
</head>'''

##########################
# Process each section

mbz['logfile'].write("\n============\nCourse Sections\n=============\n")

print("Processing course sections...")

itemCount = 0
files = etree.fromstring( get_mbz_content(mbz, 'files.xml'))         # Look in files area to get name of file

for s in backupTree.findall("./information/contents/sections")[0].findall("section"):

    section_title = s.find("title").text
    print("Now processing section id: %s (%s)" %
        (s.find("sectionid").text, section_title))

    # If the section title is just a number that is the same value as the item count, prepend a string
    if section_title == str(itemCount):
        if itemCount == 0:
            section_title = "Section Header"
        else:
            section_title = "Section %s" % section_title


    HTMLOutput = "<h2 class='ma1'>%s</h2>" % section_title


    # Open section file
    section_path = "%s/section.xml" % s.find("directory").text
    section_xml = get_mbz_content(mbz, section_path)
    section_file_root = etree.fromstring(section_xml)
    section_summary = section_file_root.find("summary").text
    if section_summary:
        section_summary = section_summary.replace("@@PLUGINFILE@@", "./course")
        HTMLOutput += "<p>%s</p>" % section_summary
    HTMLOutput += "<ul class='list ma1'>"


    if section_file_root.find("sequence").text:
        section_sequence = section_file_root.find("sequence").text.split(',')
    else:
        section_sequence = []

    # Folder path for section (if needed)
    section_file_dir = "section_%03d" % itemCount

    for item in section_sequence:
        # Look for this item in the Moodle backup file
        item_xpath = ".//*[moduleid='%s']" % item

        try:
            item_title = activities.find(item_xpath).find("title").text  # default
            modulename = activities.find(item_xpath).find("modulename").text
        except:
            continue

        print ("Found %s (item #: %s) titled %s" % (modulename, item, item_title))

        if modulename == "resource":
            # Get link to file

            inforef_path = 'activities/resource_%s/inforef.xml' % item
            inforef_xml = get_mbz_content(mbz, inforef_path)
            resourceTree = etree.fromstring(inforef_xml)
            file_listing = resourceTree.findall("fileref/file")

            for f in file_listing:

                file_id = f.find("id").text

                filename = files.find("file[@id='%s']/filename" % file_id).text

                if filename != "." and filename != "":

                    # Copy the file to a folder for this section
                    filename = make_slugified_filename(filename)
                    contenthash = files.find("file[@id='%s']/contenthash" % file_id).text

                    destination_in_zip = add_unique_postfix(zf, "%s/%s" % (section_file_dir, filename))
                    filepath_in_mbz = os.path.join("files", contenthash[:2], contenthash)

                    zf.writestr(destination_in_zip , get_mbz_content(mbz, filepath_in_mbz))

                    file_url = "./section_%03d/%s" % (itemCount, filename)
                    item_title = "<a href='%s'>%s</a>" % (file_url, item_title)



        elif modulename == "url":
            # Get url link
            url_xml = get_mbz_content(mbz, 'activities/url_%s/url.xml' % item)
            urlTree = etree.fromstring(url_xml)
            url = urlTree.find("url/externalurl").text
            print ("Url id %s" % url)

            item_title = "<a href='%s' target='_blank'>%s</a>" % (url, item_title)

        elif modulename == "page":
            page_title = activities.find(item_xpath).find("title").text  # default
            page_xml_file = activities.find(item_xpath).find("directory").text

            # Open page file
            page_xml = get_mbz_content(mbz, 'activities/page_%s/page.xml' % item)
            page_tree = etree.fromstring(page_xml)
            page_content = page_tree.find("page/content").text

            # Save page as a standalone HTML file
            # Replace any "/" characters with "-" characters to avoid confusion
            # with filepaths
            page_title = page_title.replace("/","-");
            pageFilename = make_slugified_filename("%s.html" % page_title)
            pageFilePath = add_unique_postfix(zf, "%s/%s" % (section_file_dir, pageFilename))

            with io.StringIO() as pagefile:
                pagefile.write("<html>%s<body><blockquote>" % html_header)
                pagefile.write("<h2>%s (%s)</h2>" % (fullname, shortname))
                pagefile.write("<h1>%s</h1>" % page_title)
                pagefile.write(page_content)

                zf.writestr(pageFilePath, pagefile.getvalue())

            page_url = "./section_%03d/%s" % (itemCount, pageFilename)
            item_title = "<a href='%s'>%s</a>" % (page_url, page_title)

        elif modulename == "folder":
            # Get folder info
            folder_title = activities.find(item_xpath).find("title").text
            folder_xml_file = activities.find(item_xpath).find("directory").text

            # Open folder info to get description
            folder_xml = get_mbz_content(mbz, '%s/folder.xml' % folder_xml_file)
            folder_tree = etree.fromstring(folder_xml)
            folder_desc = folder_tree.find("folder/intro").text

            # Open inforef file to get file list
            resource_xml = get_mbz_content(mbz, '%s/inforef.xml' % folder_xml_file)
            resourceTree = etree.fromstring(resource_xml)
            file_listing = resourceTree.findall("fileref/file")

            folder_html = "<div><ul>"
            for f in file_listing:
                file_id = f.find("id").text

                original_filename = files.find("file[@id='%s']/filename" % file_id).text

                if original_filename != "." and original_filename != "":

                    # Copy the file to a folder for this section
                    filename = make_slugified_filename(original_filename)
                    contenthash = files.find("file[@id='%s']/contenthash" % file_id).text

                    destination_in_zip = add_unique_postfix(zf, "%s/%s" % (section_file_dir, filename))
                    filepath_in_mbz = os.path.join("files", contenthash[:2], contenthash)
     
                    zf.writestr(destination_in_zip , get_mbz_content(mbz, filepath_in_mbz))

                    file_url = "./section_%03d/%s" % (itemCount, filename)
                    folder_html += "<li><a href='%s'>%s</a></li>" % (file_url, original_filename)

            folder_html += "</ul></div>"
            item_title = "%s (folder)%s" % (folder_title, folder_html)



        else:
            item_title += " (%s)" % modulename


        # item_path = activities.find(item_xpath).find("directory").text
        HTMLOutput += "<li class='ma2'>%s</li>" % item_title


    logOutput = section_title
    HTMLOutput += "</ul>"

    html_index_page.write(HTMLOutput)
    mbz['logfile'].write(logOutput)
    itemCount += 1

if itemCount == 0:
    html_index_page.write("<p>No sections found!</p>")
    print("No sections found!")

mbz['logfile'].write ("Extracted sections = {0}".format(itemCount))




# Handle all the course files
process_course_files(mbz)



# Complete index html file and write html and log files to zip file
html_index_page.write("<p class='f6'>Created from Moodle backup file \"%s\" on %s </p></body></html>" % (os.path.split(mbz_filepath)[1], time.strftime('%m-%d-%Y %H:%M:%S')))
zf.writestr("index.html", html_index_page.getvalue())
zf.writestr("logfile.txt", mbz['logfile'].getvalue())
html_index_page.close()
mbz['logfile'].close()


# Write out zip file
zf.close()
with open(os.path.join(script_dir, "%s.zip" % (make_slugified_filename(shortname)) ), "wb") as f:
    f.write(output_zip.getvalue())









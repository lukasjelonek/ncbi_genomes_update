#!/usr/bin/env python3
# Checks which genomes that are available on the ncbi ftp server are missing in a local sync.
# Intention: a regular rsync may download summary files that contain folders that are not available 
#            locally, e.g. if the summary was downloaded after the all directory. This script will 
#            check for missing files and download them
#
# workflow
#  * get latest assembly summary files
#  * identify locally missing assemblies
#  * generate a rsync-file with all missing entries
#  * download missing entries with rsync#
#
# The downloads will be done in a separate directory to avoid an inconsistent state in the local
# copy. After everything is available in the download-folder, it can be transferred to the live
# directory. Under the assumption that the summary files are the main entry point to the ncbi-genomes
# they must be transferred last to the live directory, to avoid inconsistencies.
#
# Caution: This is not a full ncbi genomes sync tool. It only handles ASSEMBLY_REPORTS and the all 
#          directory. The remaining directories should be synced via 

import sys
import os
import subprocess

remote_prefix = 'rsync://ftp.ncbi.nlm.nih.gov/genomes/'
local_prefix = '/vol/biodb/ncbi_genomes/'

target_directory = '/vol/biodb/ncbi_genomes/'
download_directory = '/tmp/ncbi_genomes/'

if not os.path.exists(download_directory):
  os.makedirs(download_directory)

def rsync(src, trg):
  subprocess.call(['rsync', '--copy-links', '--recursive', '--times', '--verbose', src, trg])

def localPath(ftp_url, local_prefix):
  return ftp_url.replace('ftp://ftp.ncbi.nlm.nih.gov/genomes/', local_prefix)

def relativePath(ftp_url):
  return ftp_url.replace('ftp://ftp.ncbi.nlm.nih.gov/genomes/', '')

def findMissing(index, local, handle_missing, handle_line = lambda l,i: None):
  count = 0
  with open(index) as f:
    for line in f:
      handle_line(line, count)
      count += 1
      if not line.startswith('#'):
        ftp_url = line.split('\t')[19]
        if not ftp_url == 'na':
          path = relativePath(ftp_url)
          local_path = local + path
          if not os.path.isdir(local_path):
            handle_missing(path)

# get remote index
# remote_prefix + "ASSEMBLY_REPORTS"
print("Downloading remote index files", file=sys.stderr, flush=True)
rsync(remote_prefix + "ASSEMBLY_REPORTS", download_directory)

# filter all index entries that are not present locally
progress_count = 10000
require_linebreak = False

rsync_list = open(download_directory + "rsync.list", "w")

def get_parent_paths(p):
  idx = p.find('/')
  paths = []
  while idx > 0:
    paths.append(p[0:idx])
    idx = p.find('/', idx+1)
  return paths

def add_to_rsync(p):
  global rsync_list
  for pp in get_parent_paths(p):
    print(pp, file=rsync_list)
  print(p, file=rsync_list)
  print(p + "/*", file=rsync_list)

def log_missing(p):
  global require_linebreak
  if require_linebreak:
    print(file=sys.stderr)
    require_linebreak = False
  print(p + " is missing", file=sys.stderr, flush=True)

def log_progress(line, index): 
  global require_linebreak
  if index % progress_count == 0:
    print(".", file=sys.stderr, end='', flush=True)
    require_linebreak = True

def handle_missing(p):
  log_missing(p)
  add_to_rsync(p)

assembly_summaries = [f for f in os.listdir(download_directory + 'ASSEMBLY_REPORTS') if f.startswith('assembly_summary')]

print("Assembly summaries: " + ",".join(assembly_summaries), file=sys.stderr, flush=True)

for f in assembly_summaries:
  print("Checking for missing local files " + f, file=sys.stderr, flush=True)
  findMissing(download_directory + "/ASSEMBLY_REPORTS/" + f, local_prefix, handle_missing, log_progress)
rsync_list.close()

# download new entries to download directory
call = ['rsync', '--copy-links', '--recursive','--progress', '--times', '--verbose', '--include-from=' + download_directory + 'rsync.list', '--exclude=*', remote_prefix + 'all', download_directory]
print(" ".join(call))
subprocess.call(call)

# move/copy everything from downloaded all directory to local directory
# rsync --copy-links --recursive --progress --times --verbose download_directory/all target_directory/all
# move/copy downloaded index files to local directory
# rsync --copy-links --recursive --progress --times --verbose download_directory/ASSEMBLY_REPORTS target_directory/ASSEMBLY_REPORTS

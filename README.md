# Sync missing entries in local ncbi genomes copy

Checks which genomes that are available on the ncbi ftp server are missing in a local sync.

### Intention

A regular rsync may download summary files that contain folders that are not
available locally, e.g. if the summary was downloaded after the all directory.
This script will check for missing files and download them

## Workflow

* get latest assembly summary files
* identify locally missing assemblies
* generate a rsync-file with all missing entries
* download missing entries with rsync
* you decide how the downloaded files will be merged into your local copy

## Consistency

The downloads will be done in a separate directory to avoid an inconsistent
state in the local copy. After everything is available in the download-folder,
it can be transferred to the live directory. Under the assumption that the
summary files are the main entry point to the ncbi-genomes they must be
transferred last to the live directory, to avoid inconsistencies.


### Caution

This is not a full ncbi genomes sync tool. It only handles ASSEMBLY_REPORTS and
the all directory. The remaining directories should be synced via 

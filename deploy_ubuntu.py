#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script fetches the latest build executable for Debian/Ubuntu from Jenkins
and installs it with necessary dependencies. It expects the following environment
variable be provided:
- JENKINS_JOB_URL : Jenkins job which builds the Debian package
- WORKSPACE : Jenkins workspace (set by jenkins itself)
- TRIBLER_PASSWORD : Local user password
"""

import json
import os
import sys
import time

import requests


def error(msg):
    """ Prints error and exits """
    print 'ERROR: %s' % msg
    sys.exit(1)


def fetch_executable_from_jenkins():
    """
    This method fetches the latest .deb from Jenkins.
    First, it checks the id of the latest build.
    Next, it fetches the artifacts from that build and
    saves the .deb to the workspace.
    """

    base_job_url = os.environ.get('JENKINS_JOB_URL')
    if not base_job_url:
        error('Jenkins job URL for the builder is not specified.')

    build_json = json.loads(requests.get('%s/api/json'
                                         % base_job_url).text)
    last_build = build_json['lastCompletedBuild']['number']
    print 'Last build ID: %d' % last_build

    job_url = '%s/%d' % (base_job_url, last_build)
    last_build_json = json.loads(requests.get('%s/api/json'
                                              % job_url).text)
    if not last_build_json['artifacts']:
        error('No artifacts found!')

    artifacts_deb = [artifact for artifact in
                     last_build_json['artifacts'] if '.deb'
                     in artifact['fileName']]
    artifact_url = '%s/artifact/%s' % (job_url,
                                       artifacts_deb[0]['relativePath'])
    file_name = artifacts_deb[0]['fileName']
    print 'Tribler installer url: %s' % artifact_url

    # Download the file
    file_path = os.path.join(os.environ.get('WORKSPACE'), file_name)
    download_response = requests.get(artifact_url, stream=True)
    download_response.raise_for_status()

    with open(file_path, 'wb') as handle:
        for block in download_response.iter_content(1024):
            handle.write(block)

    return file_path


if __name__ == '__main__':
    # Step 1: fetch the latest Tribler installer from Jenkins
    INSTALLER_PATH = fetch_executable_from_jenkins()

    # Step 2: Remove dpkg lock if exists
    TRIBLER_PASSWORD = os.environ.get('TRIBLER_PASSWORD')
    if os.path.exists("/var/lib/dpkg/lock"):
        DPKG_UNLOCK_SCRIPT = "echo %s| sudo -S rm /var/lib/dpkg/lock" % TRIBLER_PASSWORD
        os.system(DPKG_UNLOCK_SCRIPT)

    # One step installation
    INSTALLATION_SCRIPT = "echo %s| sudo -S apt install -y --allow-downgrades %s" % (TRIBLER_PASSWORD, INSTALLER_PATH)
    os.system(INSTALLATION_SCRIPT)

    print 'Installed Tribler...'
    time.sleep(5)

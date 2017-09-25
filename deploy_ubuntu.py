#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script installs and tests Tribler on a Ubuntu machine.
"""

import json
import os
import sys

import requests
import time


def error(msg):
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
    if len(last_build_json['artifacts']) == 0:
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

# Step 1: fetch the latest Tribler installer from Jenkins
installer_path = fetch_executable_from_jenkins()

# Step 2: Install Tribler and its dependencies
tribler_password = os.environ.get('TRIBLER_PASSWORD')
install_tribler_script = 'echo %s| sudo -S dpkg -i %s' \
    % (tribler_password, installer_path)
install_dependencies_script = 'echo %s| sudo -S apt-get install -f -y' \
    % tribler_password
os.system(install_tribler_script)
os.system(install_dependencies_script)

print 'Installed Tribler...'
time.sleep(5)


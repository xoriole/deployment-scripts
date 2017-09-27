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

# Step 1.1: Remove dpkg lock if exists
tribler_password = os.environ.get('TRIBLER_PASSWORD')
if os.path.exists("/var/lib/dpkg/lock"):
    dpkg_unlock_script = "echo %s| sudo -S rm /var/lib/dpkg/lock" % tribler_password
    os.system(dpkg_unlock_script)

# Step 2: Install Tribler system dependencies
system_dependencies = ["libav-tools", "libsodium18", "libx11-6", "python-apsw", "python-cherrypy3", "python-crypto",
                       "python-cryptography", "python-decorator", "python-feedparser", "python-leveldb",
                       "python-libtorrent", "python-matplotlib", "python-m2crypto", "python-netifaces", "python-pil",
                       "python-pyasn1", "python-twisted", "python2.7", "vlc", "python-chardet", "python-configobj",
                       "python-pyqt5", "python-pyqt5.qtsvg", "python-meliae"]
dependency_script = "echo %s| sudo -S apt-get install -y %s" % (tribler_password, " ".join(system_dependencies))
os.system(dependency_script)

# Step 3: Install pip modules
pip_modules = ["psutil"]
pip_script = "echo %s| sudo -S pip install %s" % (tribler_password, " ".join(pip_modules))
os.system(pip_script)

# Step 4: Install tribler.deb file
tribler_script = "echo %s| sudo -S dpkg -i %s" % (tribler_password, installer_path)
os.system(tribler_script)

# Step 5: Install any missing dependencies
missing_dependency_script = "echo %s| sudo -S apt-get install -f -y" % tribler_password
os.system(missing_dependency_script)

print 'Installed Tribler...'
time.sleep(5)


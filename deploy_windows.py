"""
This script installs and tests Tribler on a Windows machine.
"""
import json
import os
import sys

import requests
import time


def error(msg):
    print "ERROR: %s" % msg
    sys.exit(1)


def fetch_exe_from_jenkins():
    """
    This method fetches the latest .exe from Jenkins.
    First, it checks the id of the latest build.
    Next, it fetches the artifacts from that build and saves the .exe to the workspace.
    """
    build_json = json.loads(requests.get("https://jenkins.tribler.org/job/pers/job/Build-Tribler_Win64_devos50/api/json").text)
    last_build = build_json['lastCompletedBuild']['number']
    print "Last build ID: %d" % last_build

    job_url = 'https://jenkins.tribler.org/job/pers/job/Build-Tribler_Win64_devos50/%d' % last_build
    last_build_json = json.loads(requests.get("%s/api/json" % job_url).text)
    if len(last_build_json['artifacts']) == 0:
        error("No artifacts found!")

    artifact_url = "%s/artifact/%s" % (job_url, last_build_json['artifacts'][0]['relativePath'])
    file_name = last_build_json['artifacts'][0]['fileName']
    print "Tribler installer url: %s" % artifact_url

    # Download the file
    file_path = os.path.join(os.environ.get('WORKSPACE'), file_name)
    download_response = requests.get(artifact_url, stream=True)
    download_response.raise_for_status()

    with open(file_path, 'wb') as handle:
        for block in download_response.iter_content(1024):
            handle.write(block)

    return file_path


# Step 1: fetch the latest Tribler installer from Jenkins
installer_path = fetch_exe_from_jenkins()

# Step 2: run the installer
os.system("%s /S" % installer_path)

print "Installed Tribler..."

time.sleep(5)

# TODO run Tribler + check whether it's up and running

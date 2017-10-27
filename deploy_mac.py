"""
This script fetches the latest build executable for MacOSX from Jenkins.
It expects the following environment variable be provided:
- JENKINS_JOB_URL : Jenkins job which builds the Debian package
- WORKSPACE : Jenkins workspace (set by jenkins itself)
"""

import json
import os
import sys

import requests


def error(msg):
    """ Prints error and exits """
    print 'ERROR: %s' % msg
    sys.exit(1)


def fetch_executable_from_jenkins():
    """
    This method fetches the latest .dmg from Jenkins.
    First, it checks the id of the latest build.
    Next, it fetches the artifacts from that build and
    saves the .dmg to the workspace.
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
                     last_build_json['artifacts'] if '.dmg'
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
    CDR_PATH = os.path.join(os.environ.get('WORKSPACE'), "Tribler.cdr")
    APP_PATH = os.path.join(os.environ.get('WORKSPACE'), "Tribler.app")

    # Step 2: Mount the dmg file
    # Convert .dmg to cdr to bypass EULA
    CONVERT_COMMAND = "hdiutil convert %s -format UDTO -o %s" % (INSTALLER_PATH, CDR_PATH)
    print CONVERT_COMMAND
    os.system(CONVERT_COMMAND)

    ATTACH_COMMAND = "hdiutil attach %s" % CDR_PATH
    print ATTACH_COMMAND
    os.system(ATTACH_COMMAND)

    # Step 3: Copy the Tribler.app to workspace
    COPY_COMMAND = "cp -R /Volumes/Tribler/Tribler.app %s" % os.environ.get('WORKSPACE')
    print COPY_COMMAND
    os.system(COPY_COMMAND)

    # Step 4: Unmount Tribler volume
    DETACH_COMMAND = "hdiutil detach /Volumes/Tribler"
    print DETACH_COMMAND
    os.system(DETACH_COMMAND)

    print 'Deployment completed'

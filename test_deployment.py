#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script performs the following deployment tests for Tribler:
- Checks if Tribler is properly installed & necessary files exists
- Checks Tribler starts properly
- Check Tribler Core is running
- Checks .Tribler state directory is created
- Takes screenshots of the running state
- Kills Tribler at the end
"""

import json
import os
import signal
import subprocess
import sys
import time

import mss
import requests


def error(msg):
    """ Prints error and exits """
    print 'ERROR: %s' % msg
    sys.exit(-1)


# Assuming the defaults
DEFAULT_PORT = 8085
WORKSPACE_DIR = os.environ.get('WORKSPACE')
WORKSPACE_SCREENSHOT_DIR = os.path.join(WORKSPACE_DIR, 'screenshots')

if sys.platform == 'win32':
    TRIBLER_DIR = r"C:\Program Files\Tribler"
    TRIBLER_EXECUTABLE = r"C:\Program Files\Tribler\tribler.exe"
    TRIBLER_DOT_DIR = os.path.join(os.getenv('APPDATA'), '.Tribler')
    TRIBLER_PROCESS = 'tribler.exe'
elif sys.platform == 'linux2':
    TRIBLER_DIR = r"/usr/share/tribler"
    TRIBLER_EXECUTABLE = r"/usr/bin/tribler"
    TRIBLER_DOT_DIR = os.path.expanduser('~/.Tribler')
    TRIBLER_PROCESS = r"/usr/bin/tribler"


def get_tribler_pid():
    """ Returns the pid of running Tribler python process """
    if sys.platform == 'linux2':
        pids = []
        for proc in subprocess.check_output(['ps', '-ef']).splitlines():
            if 'python' in proc and 'run_tribler.py' in proc:
                pids += [int(proc.split()[1])]
        return pids
    elif sys.platform == 'win32':
        return [item.split()[1] for item in os.popen('tasklist').read().splitlines()[4:] if
                'tribler.exe' in item.split()]


def kill_tribler():
    """ Kills the running Tribler process """
    pids = get_tribler_pid()
    for pid in pids:
        os.kill(int(pid), signal.SIGTERM)


def check_tribler_directory():
    """ Checks if Tribler installation directory is present or not """
    if not os.path.exists(TRIBLER_DIR):
        error('Default tribler installation directory (%s) does not exist. '
              'Tribler is probably not installed' % TRIBLER_DIR)
    if not os.path.exists(TRIBLER_EXECUTABLE):
        error('Tribler executable file not found')


def run_tribler():
    """ Runs Tribler """
    if not get_tribler_pid():
        print 'Starting tribler...'
        subprocess.Popen([TRIBLER_EXECUTABLE])
        # wait few seconds before it starts
        time.sleep(30)
        # check pid if tribler has started
        if not get_tribler_pid():
            error('Tribler could not start properly')
    else:
        print 'Tribler is already running'


def check_dot_tribler_dir():
    """ Checks if .Tribler directory is present """
    print 'Checking if .Tribler directory exists'
    if not os.path.exists(TRIBLER_DOT_DIR):
        error('.Tribler directory does not exist. Installation was not successful')


def check_tribler_core_is_running():
    """ Checks if Tribler core is running """
    events_url = 'http://localhost:%d/events' % DEFAULT_PORT
    response = requests.get(events_url, stream=True)
    for event in response.iter_content(chunk_size=1024):
        print 'event:%s' % event
        event_json = json.loads(event)

        # we are interested in the first event only which contains
        # if tribler has started

        try:
            if not event_json[u'type'] == u'events_start' \
                    and not event_json[u'event'][u'tribler_started']:
                error('No tribler started event found. Tribler core has not started yet.')
            else:
                print 'Tribler core has started fine'
        except KeyError:
            error('KeyError: No tribler started event found')
        break


def take_screenshots():
    """ Takes screenshots of the screen """
    if not os.path.exists(WORKSPACE_SCREENSHOT_DIR):
        print 'Creating screenshot directory'
        os.makedirs(WORKSPACE_SCREENSHOT_DIR)

    with mss.mss() as sct:
        for i in range(1, 11):
            print 'Taking screenshot %d/%d' % (i, 10)
            file_path = os.path.join(WORKSPACE_SCREENSHOT_DIR,
                                     'screenshot-' + time.strftime('%Y%m%d%H%M%S-')
                                     + str(i) + '.png')
            sct.shot(output=file_path)

            # wait 10 seconds before new screenshot

            time.sleep(10)


if __name__ == '__main__':
    # check if the directory & executable exists

    check_tribler_directory()

    # Run Tribler

    run_tribler()

    # Check tribler core is running

    check_tribler_core_is_running()

    # Check if .Tribler directory is present

    check_dot_tribler_dir()

    # Wait few seconds

    time.sleep(30)

    # take few screenshots of the running application state

    take_screenshots()

    # Kill tribler

    kill_tribler()

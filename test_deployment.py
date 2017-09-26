#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script checks if Tribler is installed and tries to run it if it is not already running
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
    print 'ERROR: %s' % msg
    sys.exit(-1)


# Assuming the defaults

DEFAULT_PORT = 8085

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
    if sys.platform == 'linux2':
        pids = []
        for proc in subprocess.check_output(['ps', '-ef']).splitlines():
            if 'python' in proc and 'run_tribler.py' in proc:
                pids += [int(proc.split()[1])]
        return pids
    elif sys.platform == 'win32':
        return [item.split()[1] for item in os.popen('tasklist').read().splitlines()[4:] if 'tribler.exe' in item.split()]


def kill_tribler():
    pids = get_tribler_pid()
    for pid in pids:
        os.kill(int(pid), signal.SIGTERM)


def check_tribler_directory():
    if not os.path.exists(TRIBLER_DIR):
        error('Default tribler installation directory (%s) does not exist. '
              'Tribler is probably not installed' % TRIBLER_DIR)
    if not os.path.exists(TRIBLER_EXECUTABLE):
        error('Tribler executable file not found')


def run_tribler():
    tribler_pids = get_tribler_pid()
    if len(tribler_pids) > 0:
        print 'Tribler is already running'
    else:
        print 'Starting tribler'
        subprocess.Popen([TRIBLER_EXECUTABLE])

        # wait few seconds before it starts

        time.sleep(30)

        # check pid if tribler has started

        tribler_pids = get_tribler_pid()
        if len(tribler_pids) == 0:
            error('Tribler could not start properly')


def check_dot_tribler_dir():
    print 'Checking if .Tribler directory exists'
    if not os.path.exists(TRIBLER_DOT_DIR):
        error('.Tribler directory does not exist. Installation was not successful')


def check_tribler_core_is_running():
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
    WORKSPACE_DIR = os.environ.get('WORKSPACE')
    WORKSPACE_SCREENSHOT_DIR = os.path.join(WORKSPACE_DIR, 'screenshots'
                                            )
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

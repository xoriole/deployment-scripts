"""
This script checks if Tribler is installed and tries to run it if it is not already running
"""
import os
import signal
import subprocess
import time
import sys
import mss

def get_pid(process_name):
    return [item.split()[1] for item in os.popen('tasklist').read().splitlines()[4:] if process_name in item.split()]

def kill_process(process_name):
    pids = get_pid(process_name)
    for pid in pids:
        os.kill(int(pid), signal.SIGTERM)

# Assuming the default installation path
TRIBLER_DIR = r"C:\Program Files\Tribler"
TRIBLER_EXECUTABLE = r"C:\Program Files\Tribler\tribler.exe"

# check if the directory & executable exists
if not os.path.exists(TRIBLER_DIR):
    print "Default tribler installation directory does not exist. Tribler is probably not installed"
    sys.exit(-1)
if not os.path.exists(TRIBLER_EXECUTABLE):
    print "Tribler executable file not found"
    sys.exit(-1)

tribler_pids = get_pid("tribler.exe")
if len(tribler_pids) > 0:
    print "Tribler is already running"
else:
    print "Starting tribler"
    subprocess.Popen([TRIBLER_EXECUTABLE])
    # wait few seconds before it starts
    time.sleep(20)
    # check pid if tribler has started
    tribler_pids = get_pid("tribler.exe")
    if len(tribler_pids) == 0:
        print "Tribler could not start properly"
        sys.exit(-1)

# take few screenshots of running tribler application
WORKSPACE_DIR=os.environ.get("WORKSPACE") or "C:\\Users\\tribler\\"
with mss.mss() as sct:
    for i in range(1,10):
        print "Taking screenshot %d/%d" % (i,10)
        file_path = os.path.join(WORKSPACE_DIR,"screenshot-"+time.strftime("%Y%m%d%H%M%S-")+str(i)+".png")
        sct.shot(output=file_path)
        # wait 5 seconds before new screenshot
        time.sleep(5)

# let tribler run for a minute and stop it
time.sleep(60)
kill_process("tribler.exe")
"""
This script rollbacks specific VMs.
"""
import os
import sys

import time

import jenkins
from pyproxmox import prox_auth, pyproxmox

TIMEOUT = 60
host = os.environ.get("PROXMOX_HOST")
user = os.environ.get("PROXMOX_USER")
password = os.environ.get("PROXMOX_PASS")
rollback_state = os.environ.get("PROXMOX_ROLLBACK_STATE")
vmids = os.environ.get("PROXMOX_VMIDS")

jenkins_url = "http://jenkins.tribler.org"
jenkins_node = os.environ.get("JENKINS_NODE")
jenkins_user = os.environ.get("JENKINS_USER")
jenkins_password = os.environ.get("JENKINS_PASS")


def error(msg):
    print "ERROR: %s" % msg
    sys.exit(1)


def info(msg):
    print "INFO: %s" % msg


def print_env_variables():
    """ Print environment variables for debugging purposes """
    print "Host: %s" % host
    print "Node: %s" % jenkins_node
    print "User: %s" % user
    print "Password: %s" % password
    print "Rollback State : %s" % rollback_state
    print "VM IDs: %s" % vmids


def blocking_jenkins_check(nodename):
    info("Waiting for jenkins[%s] to come online: begin" % nodename)
    jserver = jenkins.Jenkins(jenkins_url, username=jenkins_user, password=jenkins_password)
    timeout = TIMEOUT
    try:
        is_offline = jserver.get_node_info(nodename)['offline']
        while is_offline and timeout > 0:
            time.sleep(1)
            is_offline = jserver.get_node_info(nodename)['offline']
            timeout -= 1

        if is_offline:
            info("Waiting for jenkins[%s] to come online: failed" % nodename)
            return False
        info("Jenkins[%s] is online" % nodename)
        return True
    except:
        pass


def blocking_stop_machine(proxmox, vm_id):
    info("Stopping the machine [VMID:%s]: begin" % vm_id)
    proxmox.stopVirtualMachine("proxmox", vm_id)

    status = proxmox.getVirtualStatus("proxmox", vm_id)['data']['status']
    timeout = TIMEOUT

    while status != u"stopped" and timeout > 0:
        time.sleep(1)
        status = proxmox.getVirtualStatus("proxmox", vm_id)['data']['status']
        # info("Waiting for machine [VMID:%s] to shutdown: %d seconds" % (vm_id, timeout))
        timeout -= 1

    if status != u"stopped":
        error("Stopping the machine [VMID:%s]: failed" % vm_id)
    info("Stopping the machine [VMID:%s]: completed" % vm_id)


def blocking_rollback_machine(proxmox, vm_id):
    info("Rollback machine [VMID:%s]: begin" % vm_id)
    rollback_upid = proxmox.rollbackVirtualMachine("proxmox", vm_id, rollback_state)['data']

    status = proxmox.getNodeTaskStatusByUPID("proxmox", rollback_upid)['data']['status']
    timeout = TIMEOUT

    while status == u"running" and timeout > 0:
        time.sleep(1)
        status = proxmox.getNodeTaskStatusByUPID("proxmox", rollback_upid)['data']['status']
        # info("Waiting for machine [VMID:%s] to shutdown: %d seconds" % (vm_id, timeout))
        timeout -= 1

    if status == u"running":
        error("Rollback machine [VMID:%s]: failed" % vm_id)
    info("Rollback machine [VMID:%s]: completed" % vm_id)


def blocking_start_machine(proxmox, vm_id):
    info("Starting the machine [VMID:%s]: begin" % vm_id)
    proxmox.startVirtualMachine("proxmox", vm_id)

    status = proxmox.getVirtualStatus("proxmox", vm_id)['data']['status']
    timeout = TIMEOUT

    while status == u"stopped" and timeout > 0:
        time.sleep(1)
        status = proxmox.getVirtualStatus("proxmox", vm_id)['data']['status']
        # info("Waiting for machine [VMID:%s] to come online: %d seconds" % (vm_id, timeout))
        timeout -= 1

    if status == u"stopped":
        error("Starting the machine [VMID:%s]: failed" % vm_id)
    info("Starting the machine [VMID:%s]: completed" % vm_id)


def blocking_reset_machine(proxmox, vm_id):
    info("Resetting the machine [VMID:%s]: begin" % vm_id)
    proxmox.resetVirtualMachine("proxmox", vm_id)

    status = proxmox.getVirtualStatus("proxmox", vm_id)['data']['status']
    timeout = TIMEOUT

    while status == u"stopped" and timeout > 0:
        time.sleep(1)
        status = proxmox.getVirtualStatus("proxmox", vm_id)['data']['status']
        # info("Waiting for machine [VMID:%s] to come online: %d seconds" % (vm_id, timeout))
        timeout -= 1

    if status == u"stopped":
        error("Resetting the machine [VMID:%s]: failed" % vm_id)
    info("Resetting the machine [VMID:%s]: completed" % vm_id)


def rollback_vm(proxmox, vm_id, nodename):
    # Shutdown the server if it is online.
    blocking_stop_machine(proxmox, vm_id)

    # Rollback the machine and wait until the machine is stopped
    blocking_rollback_machine(proxmox, vm_id)

    # Start the machine again and wait until it is running again
    blocking_start_machine(proxmox, vm_id)

    # Check if the jenkins is running in the node
    is_running = blocking_jenkins_check(nodename)
    if not is_running:
        # Try resetting the machine
        blocking_reset_machine(proxmox, vm_id)
        # Wait for jenkins to come online
        is_running = blocking_jenkins_check(nodename)

    # if jenkins is still not running, then fail the test
    if not is_running:
        error("Jenkins failed to start. Failing the test")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "show_env":
        # Print environment variables for debugging
        print_env_variables()

    auth = prox_auth(host, user, password)
    proxmox = pyproxmox(auth)

    # Rollback the vm state
    for vm_id_str in vmids.split(','):
        rollback_vm(proxmox, int(vm_id_str), jenkins_node)

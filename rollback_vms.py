"""
This script rollbacks specific VMs.
"""
import os
import sys

import time
from pyproxmox import prox_auth, pyproxmox

host = os.environ.get("PROXMOX_HOST")
proxmox_name = os.environ.get("PROXMOX_NAME") if os.environ.get("PROXMOX_NAME") else "proxmox"
user = os.environ.get("PROXMOX_USER")
password = os.environ.get("PROXMOX_PASS")
rollback_state = os.environ.get("PROXMOX_ROLLBACK_STATE")
vmids = os.environ.get("PROXMOX_VMIDS")


def print_env_variables():
    print "Host: %s" % host
    print "User: %s" % user
    print "Password: %s" % password
    print "Rollback State : %s" % rollback_state
    print "VM IDs: %s" % vmids


def rollback_vm(vm_id):
    a = prox_auth(os.environ.get("PROXMOX_HOST"), os.environ.get("PROXMOX_USER"), os.environ.get("PROXMOX_PASS"))
    b = pyproxmox(a)
    rollback_upid = b.rollbackVirtualMachine(proxmox_name, vm_id, os.environ.get("PROXMOX_ROLLBACK_STATE"))['data']

    status = b.getNodeTaskStatusByUPID(proxmox_name, rollback_upid)['data']['status']
    while status == u"running":
        time.sleep(0.5)
        status = b.getNodeTaskStatusByUPID(proxmox_name, rollback_upid)['data']['status']

    print "rollback done, restarting machine"
    b.startVirtualMachine(proxmox_name, vm_id)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "show_env":
        # Print environment variables for debugging
        print_env_variables()

    # Rollback the vm state
    for vm_id in os.environ.get("PROXMOX_VMIDS").split(','):
        rollback_vm(int(vm_id))

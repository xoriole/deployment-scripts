"""
This script rollbacks specific VMs.
"""
import os

import time
from pyproxmox import prox_auth, pyproxmox


def rollback_vm(vm_id):
    a = prox_auth(os.environ.get("PROXMOX_HOST"), os.environ.get("PROXMOX_USER"), os.environ.get("PROXMOX_PASS"))
    b = pyproxmox(a)
    rollback_upid = b.rollbackVirtualMachine("proxmox", vm_id, "win10_without_ram")['data']

    status = b.getNodeTaskStatusByUPID("proxmox", rollback_upid)['data']['status']
    while status == u"running":
        time.sleep(0.5)
        status = b.getNodeTaskStatusByUPID("proxmox", rollback_upid)['data']['status']

    print "rollback done, restarting machine"
    b.startVirtualMachine("proxmox", vm_id)


for vm_id in os.environ.get("PROXMOX_VMIDS").split(','):
    rollback_vm(int(vm_id))

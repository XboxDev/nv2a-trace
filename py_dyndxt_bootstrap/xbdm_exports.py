"""Export information for xbdm.dll"""

from .export_info import ExportInfo

# Keep in sync with the xbdm.dll.def in dyndxt_loader
DmAllocatePoolWithTag = ExportInfo(2, "DmAllocatePoolWithTag@8")
DmFreePool = ExportInfo(9, "DmFreePool@4")
DmHaltThread = ExportInfo(20, "DmHaltThread@4")
DmRegisterCommandProcessor = ExportInfo(30, "DmRegisterCommandProcessor@8")
DmResumeThread = ExportInfo(35, "DmResumeThread@4")
DmSendNotificationString = ExportInfo(36, "DmSendNotificationString@4")
DmSuspendThread = ExportInfo(48, "DmSuspendThread@4")

XBDM_EXPORTS = [
    DmAllocatePoolWithTag,
    DmFreePool,
    DmHaltThread,
    DmRegisterCommandProcessor,
    DmResumeThread,
    DmSendNotificationString,
    DmSuspendThread,
]

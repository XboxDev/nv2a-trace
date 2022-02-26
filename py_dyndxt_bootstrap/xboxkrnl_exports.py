"""Export information for xboxkrnl.exe"""

# Adapted from https://github.com/XboxDev/nxdk/blob/f0534c1432327ac3e16a137f780cf21ed8d46ff7/lib/xboxkrnl/xboxkrnl.exe.def#L1
# Copyright (C) 2017 Stefan Schmidt
# This specific file is licensed under the CC0 1.0.
# Look here for details: https://creativecommons.org/publicdomain/zero/1.0/

from .export_info import ExportInfo

AvGetSavedDataAddress = ExportInfo(1, "AvGetSavedDataAddress@0")
AvSendTVEncoderOption = ExportInfo(2, "AvSendTVEncoderOption@16")
AvSetDisplayMode = ExportInfo(3, "AvSetDisplayMode@24")
AvSetSavedDataAddress = ExportInfo(4, "AvSetSavedDataAddress@4")
DbgBreakPoint = ExportInfo(5, "DbgBreakPoint@0")
DbgBreakPointWithStatus = ExportInfo(6, "DbgBreakPointWithStatus@4")
DbgLoadImageSymbols = ExportInfo(7, "DbgLoadImageSymbols@12")
DbgPrint = ExportInfo(8, "DbgPrint")
HalReadSMCTrayState = ExportInfo(9, "HalReadSMCTrayState@8")
DbgPrompt = ExportInfo(10, "DbgPrompt@12")
DbgUnLoadImageSymbols = ExportInfo(11, "DbgUnLoadImageSymbols@12")
ExAcquireReadWriteLockExclusive = ExportInfo(12, "ExAcquireReadWriteLockExclusive@4")
ExAcquireReadWriteLockShared = ExportInfo(13, "ExAcquireReadWriteLockShared@4")
ExAllocatePool = ExportInfo(14, "ExAllocatePool@4")
ExAllocatePoolWithTag = ExportInfo(15, "ExAllocatePoolWithTag@8")
ExEventObjectType = ExportInfo(16, "ExEventObjectType")
ExFreePool = ExportInfo(17, "ExFreePool@4")
ExInitializeReadWriteLock = ExportInfo(18, "ExInitializeReadWriteLock@4")
ExInterlockedAddLargeInteger = ExportInfo(19, "ExInterlockedAddLargeInteger@16")
ExInterlockedAddLargeStatistic = ExportInfo(20, "@ExInterlockedAddLargeStatistic@8")
ExInterlockedCompareExchange64 = ExportInfo(21, "@ExInterlockedCompareExchange64@12")
ExMutantObjectType = ExportInfo(22, "ExMutantObjectType")
ExQueryPoolBlockSize = ExportInfo(23, "ExQueryPoolBlockSize@4")
ExQueryNonVolatileSetting = ExportInfo(24, "ExQueryNonVolatileSetting@20")
ExReadWriteRefurbInfo = ExportInfo(25, "ExReadWriteRefurbInfo@12")
ExRaiseException = ExportInfo(26, "ExRaiseException@4")
ExRaiseStatus = ExportInfo(27, "ExRaiseStatus@4")
ExReleaseReadWriteLock = ExportInfo(28, "ExReleaseReadWriteLock@4")
ExSaveNonVolatileSetting = ExportInfo(29, "ExSaveNonVolatileSetting@16")
ExSemaphoreObjectType = ExportInfo(30, "ExSemaphoreObjectType")
ExTimerObjectType = ExportInfo(31, "ExTimerObjectType")
ExfInterlockedInsertHeadList = ExportInfo(32, "@ExfInterlockedInsertHeadList@8")
ExfInterlockedInsertTailList = ExportInfo(33, "@ExfInterlockedInsertTailList@8")
ExfInterlockedRemoveHeadList = ExportInfo(34, "@ExfInterlockedRemoveHeadList@4")
FscGetCacheSize = ExportInfo(35, "FscGetCacheSize@0")
FscInvalidateIdleBlocks = ExportInfo(36, "FscInvalidateIdleBlocks@0")
FscSetCacheSize = ExportInfo(37, "FscSetCacheSize@4")
HalClearSoftwareInterrupt = ExportInfo(38, "@HalClearSoftwareInterrupt@4")
HalDisableSystemInterrupt = ExportInfo(39, "HalDisableSystemInterrupt@4")
HalDiskCachePartitionCount = ExportInfo(40, "HalDiskCachePartitionCount")
HalDiskModelNumber = ExportInfo(41, "HalDiskModelNumber")
HalDiskSerialNumber = ExportInfo(42, "HalDiskSerialNumber")
HalEnableSystemInterrupt = ExportInfo(43, "HalEnableSystemInterrupt@8")
HalGetInterruptVector = ExportInfo(44, "HalGetInterruptVector@8")
HalReadSMBusValue = ExportInfo(45, "HalReadSMBusValue@16")
HalReadWritePCISpace = ExportInfo(46, "HalReadWritePCISpace@24")
HalRegisterShutdownNotification = ExportInfo(47, "HalRegisterShutdownNotification@8")
HalRequestSoftwareInterrupt = ExportInfo(48, "@HalRequestSoftwareInterrupt@4")
HalReturnToFirmware = ExportInfo(49, "HalReturnToFirmware@4")
HalWriteSMBusValue = ExportInfo(50, "HalWriteSMBusValue@16")
InterlockedCompareExchange = ExportInfo(51, "@InterlockedCompareExchange@12")
InterlockedDecrement = ExportInfo(52, "@InterlockedDecrement@4")
InterlockedIncrement = ExportInfo(53, "@InterlockedIncrement@4")
InterlockedExchange = ExportInfo(54, "@InterlockedExchange@8")
InterlockedExchangeAdd = ExportInfo(55, "@InterlockedExchangeAdd@8")
InterlockedFlushSList = ExportInfo(56, "@InterlockedFlushSList@4")
InterlockedPopEntrySList = ExportInfo(57, "@InterlockedPopEntrySList@4")
InterlockedPushEntrySList = ExportInfo(58, "@InterlockedPushEntrySList@8")
IoAllocateIrp = ExportInfo(59, "IoAllocateIrp@4")
IoBuildAsynchronousFsdRequest = ExportInfo(60, "IoBuildAsynchronousFsdRequest@24")
IoBuildDeviceIoControlRequest = ExportInfo(61, "IoBuildDeviceIoControlRequest@36")
IoBuildSynchronousFsdRequest = ExportInfo(62, "IoBuildSynchronousFsdRequest@28")
IoCheckShareAccess = ExportInfo(63, "IoCheckShareAccess@20")
IoCompletionObjectType = ExportInfo(64, "IoCompletionObjectType")
IoCreateDevice = ExportInfo(65, "IoCreateDevice@24")
IoCreateFile = ExportInfo(66, "IoCreateFile@40")
IoCreateSymbolicLink = ExportInfo(67, "IoCreateSymbolicLink@8")
IoDeleteDevice = ExportInfo(68, "IoDeleteDevice@4")
IoDeleteSymbolicLink = ExportInfo(69, "IoDeleteSymbolicLink@4")
IoDeviceObjectType = ExportInfo(70, "IoDeviceObjectType")
IoFileObjectType = ExportInfo(71, "IoFileObjectType")
IoFreeIrp = ExportInfo(72, "IoFreeIrp@4")
IoInitializeIrp = ExportInfo(73, "IoInitializeIrp@12")
IoInvalidDeviceRequest = ExportInfo(74, "IoInvalidDeviceRequest@8")
IoQueryFileInformation = ExportInfo(75, "IoQueryFileInformation@20")
IoQueryVolumeInformation = ExportInfo(76, "IoQueryVolumeInformation@20")
IoQueueThreadIrp = ExportInfo(77, "IoQueueThreadIrp@4")
IoRemoveShareAccess = ExportInfo(78, "IoRemoveShareAccess@8")
IoSetIoCompletion = ExportInfo(79, "IoSetIoCompletion@20")
IoSetShareAccess = ExportInfo(80, "IoSetShareAccess@16")
IoStartNextPacket = ExportInfo(81, "IoStartNextPacket@4")
IoStartNextPacketByKey = ExportInfo(82, "IoStartNextPacketByKey@8")
IoStartPacket = ExportInfo(83, "IoStartPacket@12")
IoSynchronousDeviceIoControlRequest = ExportInfo(
    84, "IoSynchronousDeviceIoControlRequest@32"
)
IoSynchronousFsdRequest = ExportInfo(85, "IoSynchronousFsdRequest@20")
IofCallDriver = ExportInfo(86, "@IofCallDriver@8")
IofCompleteRequest = ExportInfo(87, "@IofCompleteRequest@8")
KdDebuggerEnabled = ExportInfo(88, "KdDebuggerEnabled")
KdDebuggerNotPresent = ExportInfo(89, "KdDebuggerNotPresent")
IoDismountVolume = ExportInfo(90, "IoDismountVolume@4")
IoDismountVolumeByName = ExportInfo(91, "IoDismountVolumeByName@4")
KeAlertResumeThread = ExportInfo(92, "KeAlertResumeThread@4")
KeAlertThread = ExportInfo(93, "KeAlertThread@8")
KeBoostPriorityThread = ExportInfo(94, "KeBoostPriorityThread@8")
KeBugCheck = ExportInfo(95, "KeBugCheck@4")
KeBugCheckEx = ExportInfo(96, "KeBugCheckEx@20")
KeCancelTimer = ExportInfo(97, "KeCancelTimer@4")
KeConnectInterrupt = ExportInfo(98, "KeConnectInterrupt@4")
KeDelayExecutionThread = ExportInfo(99, "KeDelayExecutionThread@12")
KeDisconnectInterrupt = ExportInfo(100, "KeDisconnectInterrupt@4")
KeEnterCriticalRegion = ExportInfo(101, "KeEnterCriticalRegion@0")
MmGlobalData = ExportInfo(102, "MmGlobalData")
KeGetCurrentIrql = ExportInfo(103, "KeGetCurrentIrql@0")
KeGetCurrentThread = ExportInfo(104, "KeGetCurrentThread@0")
KeInitializeApc = ExportInfo(105, "KeInitializeApc@28")
KeInitializeDeviceQueue = ExportInfo(106, "KeInitializeDeviceQueue@4")
KeInitializeDpc = ExportInfo(107, "KeInitializeDpc@12")
KeInitializeEvent = ExportInfo(108, "KeInitializeEvent@12")
KeInitializeInterrupt = ExportInfo(109, "KeInitializeInterrupt@28")
KeInitializeMutant = ExportInfo(110, "KeInitializeMutant@8")
KeInitializeQueue = ExportInfo(111, "KeInitializeQueue@8")
KeInitializeSemaphore = ExportInfo(112, "KeInitializeSemaphore@12")
KeInitializeTimerEx = ExportInfo(113, "KeInitializeTimerEx@8")
KeInsertByKeyDeviceQueue = ExportInfo(114, "KeInsertByKeyDeviceQueue@12")
KeInsertDeviceQueue = ExportInfo(115, "KeInsertDeviceQueue@8")
KeInsertHeadQueue = ExportInfo(116, "KeInsertHeadQueue@8")
KeInsertQueue = ExportInfo(117, "KeInsertQueue@8")
KeInsertQueueApc = ExportInfo(118, "KeInsertQueueApc@16")
KeInsertQueueDpc = ExportInfo(119, "KeInsertQueueDpc@12")
KeInterruptTime = ExportInfo(120, "KeInterruptTime")
KeIsExecutingDpc = ExportInfo(121, "KeIsExecutingDpc@0")
KeLeaveCriticalRegion = ExportInfo(122, "KeLeaveCriticalRegion@0")
KePulseEvent = ExportInfo(123, "KePulseEvent@12")
KeQueryBasePriorityThread = ExportInfo(124, "KeQueryBasePriorityThread@4")
KeQueryInterruptTime = ExportInfo(125, "KeQueryInterruptTime@0")
KeQueryPerformanceCounter = ExportInfo(126, "KeQueryPerformanceCounter@0")
KeQueryPerformanceFrequency = ExportInfo(127, "KeQueryPerformanceFrequency@0")
KeQuerySystemTime = ExportInfo(128, "KeQuerySystemTime@4")
KeRaiseIrqlToDpcLevel = ExportInfo(129, "KeRaiseIrqlToDpcLevel@0")
KeRaiseIrqlToSynchLevel = ExportInfo(130, "KeRaiseIrqlToSynchLevel@0")
KeReleaseMutant = ExportInfo(131, "KeReleaseMutant@16")
KeReleaseSemaphore = ExportInfo(132, "KeReleaseSemaphore@16")
KeRemoveByKeyDeviceQueue = ExportInfo(133, "KeRemoveByKeyDeviceQueue@8")
KeRemoveDeviceQueue = ExportInfo(134, "KeRemoveDeviceQueue@4")
KeRemoveEntryDeviceQueue = ExportInfo(135, "KeRemoveEntryDeviceQueue@8")
KeRemoveQueue = ExportInfo(136, "KeRemoveQueue@12")
KeRemoveQueueDpc = ExportInfo(137, "KeRemoveQueueDpc@4")
KeResetEvent = ExportInfo(138, "KeResetEvent@4")
KeRestoreFloatingPointState = ExportInfo(139, "KeRestoreFloatingPointState@4")
KeResumeThread = ExportInfo(140, "KeResumeThread@4")
KeRundownQueue = ExportInfo(141, "KeRundownQueue@4")
KeSaveFloatingPointState = ExportInfo(142, "KeSaveFloatingPointState@4")
KeSetBasePriorityThread = ExportInfo(143, "KeSetBasePriorityThread@8")
KeSetDisableBoostThread = ExportInfo(144, "KeSetDisableBoostThread@8")
KeSetEvent = ExportInfo(145, "KeSetEvent@12")
KeSetEventBoostPriority = ExportInfo(146, "KeSetEventBoostPriority@8")
KeSetPriorityProcess = ExportInfo(147, "KeSetPriorityProcess@8")
KeSetPriorityThread = ExportInfo(148, "KeSetPriorityThread@8")
KeSetTimer = ExportInfo(149, "KeSetTimer@16")
KeSetTimerEx = ExportInfo(150, "KeSetTimerEx@20")
KeStallExecutionProcessor = ExportInfo(151, "KeStallExecutionProcessor@4")
KeSuspendThread = ExportInfo(152, "KeSuspendThread@4")
KeSynchronizeExecution = ExportInfo(153, "KeSynchronizeExecution@12")
KeSystemTime = ExportInfo(154, "KeSystemTime")
KeTestAlertThread = ExportInfo(155, "KeTestAlertThread@4")
KeTickCount = ExportInfo(156, "KeTickCount")
KeTimeIncrement = ExportInfo(157, "KeTimeIncrement")
KeWaitForMultipleObjects = ExportInfo(158, "KeWaitForMultipleObjects@32")
KeWaitForSingleObject = ExportInfo(159, "KeWaitForSingleObject@20")
KfRaiseIrql = ExportInfo(160, "@KfRaiseIrql@4")
KfLowerIrql = ExportInfo(161, "@KfLowerIrql@4")
KiBugCheckData = ExportInfo(162, "KiBugCheckData")
KiUnlockDispatcherDatabase = ExportInfo(163, "@KiUnlockDispatcherDatabase@4")
LaunchDataPage = ExportInfo(164, "LaunchDataPage")
MmAllocateContiguousMemory = ExportInfo(165, "MmAllocateContiguousMemory@4")
MmAllocateContiguousMemoryEx = ExportInfo(166, "MmAllocateContiguousMemoryEx@20")
MmAllocateSystemMemory = ExportInfo(167, "MmAllocateSystemMemory@8")
MmClaimGpuInstanceMemory = ExportInfo(168, "MmClaimGpuInstanceMemory@8")
MmCreateKernelStack = ExportInfo(169, "MmCreateKernelStack@8")
MmDeleteKernelStack = ExportInfo(170, "MmDeleteKernelStack@8")
MmFreeContiguousMemory = ExportInfo(171, "MmFreeContiguousMemory@4")
MmFreeSystemMemory = ExportInfo(172, "MmFreeSystemMemory@8")
MmGetPhysicalAddress = ExportInfo(173, "MmGetPhysicalAddress@4")
MmIsAddressValid = ExportInfo(174, "MmIsAddressValid@4")
MmLockUnlockBufferPages = ExportInfo(175, "MmLockUnlockBufferPages@12")
MmLockUnlockPhysicalPage = ExportInfo(176, "MmLockUnlockPhysicalPage@8")
MmMapIoSpace = ExportInfo(177, "MmMapIoSpace@12")
MmPersistContiguousMemory = ExportInfo(178, "MmPersistContiguousMemory@12")
MmQueryAddressProtect = ExportInfo(179, "MmQueryAddressProtect@4")
MmQueryAllocationSize = ExportInfo(180, "MmQueryAllocationSize@4")
MmQueryStatistics = ExportInfo(181, "MmQueryStatistics@4")
MmSetAddressProtect = ExportInfo(182, "MmSetAddressProtect@12")
MmUnmapIoSpace = ExportInfo(183, "MmUnmapIoSpace@8")
NtAllocateVirtualMemory = ExportInfo(184, "NtAllocateVirtualMemory@20")
NtCancelTimer = ExportInfo(185, "NtCancelTimer@8")
NtClearEvent = ExportInfo(186, "NtClearEvent@4")
NtClose = ExportInfo(187, "NtClose@4")
NtCreateDirectoryObject = ExportInfo(188, "NtCreateDirectoryObject@8")
NtCreateEvent = ExportInfo(189, "NtCreateEvent@16")
NtCreateFile = ExportInfo(190, "NtCreateFile@36")
NtCreateIoCompletion = ExportInfo(191, "NtCreateIoCompletion@16")
NtCreateMutant = ExportInfo(192, "NtCreateMutant@12")
NtCreateSemaphore = ExportInfo(193, "NtCreateSemaphore@16")
NtCreateTimer = ExportInfo(194, "NtCreateTimer@12")
NtDeleteFile = ExportInfo(195, "NtDeleteFile@4")
NtDeviceIoControlFile = ExportInfo(196, "NtDeviceIoControlFile@40")
NtDuplicateObject = ExportInfo(197, "NtDuplicateObject@12")
NtFlushBuffersFile = ExportInfo(198, "NtFlushBuffersFile@8")
NtFreeVirtualMemory = ExportInfo(199, "NtFreeVirtualMemory@12")
NtFsControlFile = ExportInfo(200, "NtFsControlFile@40")
NtOpenDirectoryObject = ExportInfo(201, "NtOpenDirectoryObject@8")
NtOpenFile = ExportInfo(202, "NtOpenFile@24")
NtOpenSymbolicLinkObject = ExportInfo(203, "NtOpenSymbolicLinkObject@8")
NtProtectVirtualMemory = ExportInfo(204, "NtProtectVirtualMemory@16")
NtPulseEvent = ExportInfo(205, "NtPulseEvent@8")
NtQueueApcThread = ExportInfo(206, "NtQueueApcThread@20")
NtQueryDirectoryFile = ExportInfo(207, "NtQueryDirectoryFile@40")
NtQueryDirectoryObject = ExportInfo(208, "NtQueryDirectoryObject@24")
NtQueryEvent = ExportInfo(209, "NtQueryEvent@8")
NtQueryFullAttributesFile = ExportInfo(210, "NtQueryFullAttributesFile@8")
NtQueryInformationFile = ExportInfo(211, "NtQueryInformationFile@20")
NtQueryIoCompletion = ExportInfo(212, "NtQueryIoCompletion@8")
NtQueryMutant = ExportInfo(213, "NtQueryMutant@8")
NtQuerySemaphore = ExportInfo(214, "NtQuerySemaphore@8")
NtQuerySymbolicLinkObject = ExportInfo(215, "NtQuerySymbolicLinkObject@12")
NtQueryTimer = ExportInfo(216, "NtQueryTimer@8")
NtQueryVirtualMemory = ExportInfo(217, "NtQueryVirtualMemory@8")
NtQueryVolumeInformationFile = ExportInfo(218, "NtQueryVolumeInformationFile@20")
NtReadFile = ExportInfo(219, "NtReadFile@32")
NtReadFileScatter = ExportInfo(220, "NtReadFileScatter@32")
NtReleaseMutant = ExportInfo(221, "NtReleaseMutant@8")
NtReleaseSemaphore = ExportInfo(222, "NtReleaseSemaphore@12")
NtRemoveIoCompletion = ExportInfo(223, "NtRemoveIoCompletion@20")
NtResumeThread = ExportInfo(224, "NtResumeThread@8")
NtSetEvent = ExportInfo(225, "NtSetEvent@8")
NtSetInformationFile = ExportInfo(226, "NtSetInformationFile@20")
NtSetIoCompletion = ExportInfo(227, "NtSetIoCompletion@20")
NtSetSystemTime = ExportInfo(228, "NtSetSystemTime@8")
NtSetTimerEx = ExportInfo(229, "NtSetTimerEx@32")
NtSignalAndWaitForSingleObjectEx = ExportInfo(
    230, "NtSignalAndWaitForSingleObjectEx@20"
)
NtSuspendThread = ExportInfo(231, "NtSuspendThread@8")
NtUserIoApcDispatcher = ExportInfo(232, "NtUserIoApcDispatcher@12")
NtWaitForSingleObject = ExportInfo(233, "NtWaitForSingleObject@12")
NtWaitForSingleObjectEx = ExportInfo(234, "NtWaitForSingleObjectEx@16")
NtWaitForMultipleObjectsEx = ExportInfo(235, "NtWaitForMultipleObjectsEx@24")
NtWriteFile = ExportInfo(236, "NtWriteFile@32")
NtWriteFileGather = ExportInfo(237, "NtWriteFileGather@32")
NtYieldExecution = ExportInfo(238, "NtYieldExecution@0")
ObCreateObject = ExportInfo(239, "ObCreateObject@16")
ObDirectoryObjectType = ExportInfo(240, "ObDirectoryObjectType")
ObInsertObject = ExportInfo(241, "ObInsertObject@16")
ObMakeTemporaryObject = ExportInfo(242, "ObMakeTemporaryObject@4")
ObOpenObjectByName = ExportInfo(243, "ObOpenObjectByName@16")
ObOpenObjectByPointer = ExportInfo(244, "ObOpenObjectByPointer@12")
ObpObjectHandleTable = ExportInfo(245, "ObpObjectHandleTable")
ObReferenceObjectByHandle = ExportInfo(246, "ObReferenceObjectByHandle@12")
ObReferenceObjectByName = ExportInfo(247, "ObReferenceObjectByName@20")
ObReferenceObjectByPointer = ExportInfo(248, "ObReferenceObjectByPointer@8")
ObSymbolicLinkObjectType = ExportInfo(249, "ObSymbolicLinkObjectType")
ObfDereferenceObject = ExportInfo(250, "@ObfDereferenceObject@4")
ObfReferenceObject = ExportInfo(251, "@ObfReferenceObject@4")
PhyGetLinkState = ExportInfo(252, "PhyGetLinkState@4")
PhyInitialize = ExportInfo(253, "PhyInitialize@8")
PsCreateSystemThread = ExportInfo(254, "PsCreateSystemThread@20")
PsCreateSystemThreadEx = ExportInfo(255, "PsCreateSystemThreadEx@40")
PsQueryStatistics = ExportInfo(256, "PsQueryStatistics@4")
PsSetCreateThreadNotifyRoutine = ExportInfo(257, "PsSetCreateThreadNotifyRoutine@4")
PsTerminateSystemThread = ExportInfo(258, "PsTerminateSystemThread@4")
PsThreadObjectType = ExportInfo(259, "PsThreadObjectType")
RtlAnsiStringToUnicodeString = ExportInfo(260, "RtlAnsiStringToUnicodeString@12")
RtlAppendStringToString = ExportInfo(261, "RtlAppendStringToString@8")
RtlAppendUnicodeStringToString = ExportInfo(262, "RtlAppendUnicodeStringToString@8")
RtlAppendUnicodeToString = ExportInfo(263, "RtlAppendUnicodeToString@8")
RtlAssert = ExportInfo(264, "RtlAssert@16")
RtlCaptureContext = ExportInfo(265, "RtlCaptureContext@4")
RtlCaptureStackBackTrace = ExportInfo(266, "RtlCaptureStackBackTrace@16")
RtlCharToInteger = ExportInfo(267, "RtlCharToInteger@12")
RtlCompareMemory = ExportInfo(268, "RtlCompareMemory@12")
RtlCompareMemoryUlong = ExportInfo(269, "RtlCompareMemoryUlong@12")
RtlCompareString = ExportInfo(270, "RtlCompareString@12")
RtlCompareUnicodeString = ExportInfo(271, "RtlCompareUnicodeString@12")
RtlCopyString = ExportInfo(272, "RtlCopyString@8")
RtlCopyUnicodeString = ExportInfo(273, "RtlCopyUnicodeString@8")
RtlCreateUnicodeString = ExportInfo(274, "RtlCreateUnicodeString@8")
RtlDowncaseUnicodeChar = ExportInfo(275, "RtlDowncaseUnicodeChar@4")
RtlDowncaseUnicodeString = ExportInfo(276, "RtlDowncaseUnicodeString@12")
RtlEnterCriticalSection = ExportInfo(277, "RtlEnterCriticalSection@4")
RtlEnterCriticalSectionAndRegion = ExportInfo(278, "RtlEnterCriticalSectionAndRegion@4")
RtlEqualString = ExportInfo(279, "RtlEqualString@12")
RtlEqualUnicodeString = ExportInfo(280, "RtlEqualUnicodeString@12")
RtlExtendedIntegerMultiply = ExportInfo(281, "RtlExtendedIntegerMultiply@12")
RtlExtendedLargeIntegerDivide = ExportInfo(282, "RtlExtendedLargeIntegerDivide@16")
RtlExtendedMagicDivide = ExportInfo(283, "RtlExtendedMagicDivide@20")
RtlFillMemory = ExportInfo(284, "RtlFillMemory@12")
RtlFillMemoryUlong = ExportInfo(285, "RtlFillMemoryUlong@12")
RtlFreeAnsiString = ExportInfo(286, "RtlFreeAnsiString@4")
RtlFreeUnicodeString = ExportInfo(287, "RtlFreeUnicodeString@4")
RtlGetCallersAddress = ExportInfo(288, "RtlGetCallersAddress@8")
RtlInitAnsiString = ExportInfo(289, "RtlInitAnsiString@8")
RtlInitUnicodeString = ExportInfo(290, "RtlInitUnicodeString@8")
RtlInitializeCriticalSection = ExportInfo(291, "RtlInitializeCriticalSection@4")
RtlIntegerToChar = ExportInfo(292, "RtlIntegerToChar@16")
RtlIntegerToUnicodeString = ExportInfo(293, "RtlIntegerToUnicodeString@12")
RtlLeaveCriticalSection = ExportInfo(294, "RtlLeaveCriticalSection@4")
RtlLeaveCriticalSectionAndRegion = ExportInfo(295, "RtlLeaveCriticalSectionAndRegion@4")
RtlLowerChar = ExportInfo(296, "RtlLowerChar@4")
RtlMapGenericMask = ExportInfo(297, "RtlMapGenericMask@8")
RtlMoveMemory = ExportInfo(298, "RtlMoveMemory@12")
RtlMultiByteToUnicodeN = ExportInfo(299, "RtlMultiByteToUnicodeN@20")
RtlMultiByteToUnicodeSize = ExportInfo(300, "RtlMultiByteToUnicodeSize@12")
RtlNtStatusToDosError = ExportInfo(301, "RtlNtStatusToDosError@4")
RtlRaiseException = ExportInfo(302, "RtlRaiseException@4")
RtlRaiseStatus = ExportInfo(303, "RtlRaiseStatus@4")
RtlTimeFieldsToTime = ExportInfo(304, "RtlTimeFieldsToTime@8")
RtlTimeToTimeFields = ExportInfo(305, "RtlTimeToTimeFields@8")
RtlTryEnterCriticalSection = ExportInfo(306, "RtlTryEnterCriticalSection@4")
RtlUlongByteSwap = ExportInfo(307, "@RtlUlongByteSwap@4")
RtlUnicodeStringToAnsiString = ExportInfo(308, "RtlUnicodeStringToAnsiString@12")
RtlUnicodeStringToInteger = ExportInfo(309, "RtlUnicodeStringToInteger@12")
RtlUnicodeToMultiByteN = ExportInfo(310, "RtlUnicodeToMultiByteN@20")
RtlUnicodeToMultiByteSize = ExportInfo(311, "RtlUnicodeToMultiByteSize@12")
RtlUnwind = ExportInfo(312, "RtlUnwind@16")
RtlUpcaseUnicodeChar = ExportInfo(313, "RtlUpcaseUnicodeChar@4")
RtlUpcaseUnicodeString = ExportInfo(314, "RtlUpcaseUnicodeString@12")
RtlUpcaseUnicodeToMultiByteN = ExportInfo(315, "RtlUpcaseUnicodeToMultiByteN@20")
RtlUpperChar = ExportInfo(316, "RtlUpperChar@4")
RtlUpperString = ExportInfo(317, "RtlUpperString@8")
RtlUshortByteSwap = ExportInfo(318, "@RtlUshortByteSwap@4")
RtlWalkFrameChain = ExportInfo(319, "RtlWalkFrameChain@12")
RtlZeroMemory = ExportInfo(320, "RtlZeroMemory@8")
XboxEEPROMKey = ExportInfo(321, "XboxEEPROMKey")
XboxHardwareInfo = ExportInfo(322, "XboxHardwareInfo")
XboxHDKey = ExportInfo(323, "XboxHDKey")
XboxKrnlVersion = ExportInfo(324, "XboxKrnlVersion")
XboxSignatureKey = ExportInfo(325, "XboxSignatureKey")
XeImageFileName = ExportInfo(326, "XeImageFileName")
XeLoadSection = ExportInfo(327, "XeLoadSection@4")
XeUnloadSection = ExportInfo(328, "XeUnloadSection@4")
READ_PORT_BUFFER_UCHAR = ExportInfo(329, "READ_PORT_BUFFER_UCHAR@12")
READ_PORT_BUFFER_USHORT = ExportInfo(330, "READ_PORT_BUFFER_USHORT@12")
READ_PORT_BUFFER_ULONG = ExportInfo(331, "READ_PORT_BUFFER_ULONG@12")
WRITE_PORT_BUFFER_UCHAR = ExportInfo(332, "WRITE_PORT_BUFFER_UCHAR@12")
WRITE_PORT_BUFFER_USHORT = ExportInfo(333, "WRITE_PORT_BUFFER_USHORT@12")
WRITE_PORT_BUFFER_ULONG = ExportInfo(334, "WRITE_PORT_BUFFER_ULONG@12")
XcSHAInit = ExportInfo(335, "XcSHAInit@4")
XcSHAUpdate = ExportInfo(336, "XcSHAUpdate@12")
XcSHAFinal = ExportInfo(337, "XcSHAFinal@8")
XcRC4Key = ExportInfo(338, "XcRC4Key@12")
XcRC4Crypt = ExportInfo(339, "XcRC4Crypt@12")
XcHMAC = ExportInfo(340, "XcHMAC@28")
XcPKEncPublic = ExportInfo(341, "XcPKEncPublic@12")
XcPKDecPrivate = ExportInfo(342, "XcPKDecPrivate@12")
XcPKGetKeyLen = ExportInfo(343, "XcPKGetKeyLen@4")
XcVerifyPKCS1Signature = ExportInfo(344, "XcVerifyPKCS1Signature@12")
XcModExp = ExportInfo(345, "XcModExp@20")
XcDESKeyParity = ExportInfo(346, "XcDESKeyParity@8")
XcKeyTable = ExportInfo(347, "XcKeyTable@12")
XcBlockCrypt = ExportInfo(348, "XcBlockCrypt@20")
XcBlockCryptCBC = ExportInfo(349, "XcBlockCryptCBC@28")
XcCryptService = ExportInfo(350, "XcCryptService@8")
XcUpdateCrypto = ExportInfo(351, "XcUpdateCrypto@8")
RtlRip = ExportInfo(352, "RtlRip@12")
XboxLANKey = ExportInfo(353, "XboxLANKey")
XboxAlternateSignatureKeys = ExportInfo(354, "XboxAlternateSignatureKeys")
XePublicKeyData = ExportInfo(355, "XePublicKeyData")
HalBootSMCVideoMode = ExportInfo(356, "HalBootSMCVideoMode")
IdexChannelObject = ExportInfo(357, "IdexChannelObject")
HalIsResetOrShutdownPending = ExportInfo(358, "HalIsResetOrShutdownPending@0")
IoMarkIrpMustComplete = ExportInfo(359, "IoMarkIrpMustComplete@4")
HalInitiateShutdown = ExportInfo(360, "HalInitiateShutdown@0")
RtlSnprintf = ExportInfo(361, "RtlSnprintf")
RtlSprintf = ExportInfo(362, "RtlSprintf")
RtlVsnprintf = ExportInfo(363, "RtlVsnprintf")
RtlVsprintf = ExportInfo(364, "RtlVsprintf")
HalEnableSecureTrayEject = ExportInfo(365, "HalEnableSecureTrayEject@0")
HalWriteSMCScratchRegister = ExportInfo(366, "HalWriteSMCScratchRegister@4")
MmDbgAllocateMemory = ExportInfo(374, "MmDbgAllocateMemory@8")
MmDbgFreeMemory = ExportInfo(375, "MmDbgFreeMemory@8")
MmDbgQueryAvailablePages = ExportInfo(376, "MmDbgQueryAvailablePages@0")
MmDbgReleaseAddress = ExportInfo(377, "MmDbgReleaseAddress@8")
MmDbgWriteCheck = ExportInfo(378, "MmDbgWriteCheck@8")

XBOXKERNL_EXPORTS = [
    AvGetSavedDataAddress,
    AvSendTVEncoderOption,
    AvSetDisplayMode,
    AvSetSavedDataAddress,
    DbgBreakPoint,
    DbgBreakPointWithStatus,
    DbgLoadImageSymbols,
    DbgPrint,
    HalReadSMCTrayState,
    DbgPrompt,
    DbgUnLoadImageSymbols,
    ExAcquireReadWriteLockExclusive,
    ExAcquireReadWriteLockShared,
    ExAllocatePool,
    ExAllocatePoolWithTag,
    ExEventObjectType,
    ExFreePool,
    ExInitializeReadWriteLock,
    ExInterlockedAddLargeInteger,
    ExInterlockedAddLargeStatistic,
    ExInterlockedCompareExchange64,
    ExMutantObjectType,
    ExQueryPoolBlockSize,
    ExQueryNonVolatileSetting,
    ExReadWriteRefurbInfo,
    ExRaiseException,
    ExRaiseStatus,
    ExReleaseReadWriteLock,
    ExSaveNonVolatileSetting,
    ExSemaphoreObjectType,
    ExTimerObjectType,
    ExfInterlockedInsertHeadList,
    ExfInterlockedInsertTailList,
    ExfInterlockedRemoveHeadList,
    FscGetCacheSize,
    FscInvalidateIdleBlocks,
    FscSetCacheSize,
    HalClearSoftwareInterrupt,
    HalDisableSystemInterrupt,
    HalDiskCachePartitionCount,
    HalDiskModelNumber,
    HalDiskSerialNumber,
    HalEnableSystemInterrupt,
    HalGetInterruptVector,
    HalReadSMBusValue,
    HalReadWritePCISpace,
    HalRegisterShutdownNotification,
    HalRequestSoftwareInterrupt,
    HalReturnToFirmware,
    HalWriteSMBusValue,
    InterlockedCompareExchange,
    InterlockedDecrement,
    InterlockedIncrement,
    InterlockedExchange,
    InterlockedExchangeAdd,
    InterlockedFlushSList,
    InterlockedPopEntrySList,
    InterlockedPushEntrySList,
    IoAllocateIrp,
    IoBuildAsynchronousFsdRequest,
    IoBuildDeviceIoControlRequest,
    IoBuildSynchronousFsdRequest,
    IoCheckShareAccess,
    IoCompletionObjectType,
    IoCreateDevice,
    IoCreateFile,
    IoCreateSymbolicLink,
    IoDeleteDevice,
    IoDeleteSymbolicLink,
    IoDeviceObjectType,
    IoFileObjectType,
    IoFreeIrp,
    IoInitializeIrp,
    IoInvalidDeviceRequest,
    IoQueryFileInformation,
    IoQueryVolumeInformation,
    IoQueueThreadIrp,
    IoRemoveShareAccess,
    IoSetIoCompletion,
    IoSetShareAccess,
    IoStartNextPacket,
    IoStartNextPacketByKey,
    IoStartPacket,
    IoSynchronousDeviceIoControlRequest,
    IoSynchronousFsdRequest,
    IofCallDriver,
    IofCompleteRequest,
    KdDebuggerEnabled,
    KdDebuggerNotPresent,
    IoDismountVolume,
    IoDismountVolumeByName,
    KeAlertResumeThread,
    KeAlertThread,
    KeBoostPriorityThread,
    KeBugCheck,
    KeBugCheckEx,
    KeCancelTimer,
    KeConnectInterrupt,
    KeDelayExecutionThread,
    KeDisconnectInterrupt,
    KeEnterCriticalRegion,
    MmGlobalData,
    KeGetCurrentIrql,
    KeGetCurrentThread,
    KeInitializeApc,
    KeInitializeDeviceQueue,
    KeInitializeDpc,
    KeInitializeEvent,
    KeInitializeInterrupt,
    KeInitializeMutant,
    KeInitializeQueue,
    KeInitializeSemaphore,
    KeInitializeTimerEx,
    KeInsertByKeyDeviceQueue,
    KeInsertDeviceQueue,
    KeInsertHeadQueue,
    KeInsertQueue,
    KeInsertQueueApc,
    KeInsertQueueDpc,
    KeInterruptTime,
    KeIsExecutingDpc,
    KeLeaveCriticalRegion,
    KePulseEvent,
    KeQueryBasePriorityThread,
    KeQueryInterruptTime,
    KeQueryPerformanceCounter,
    KeQueryPerformanceFrequency,
    KeQuerySystemTime,
    KeRaiseIrqlToDpcLevel,
    KeRaiseIrqlToSynchLevel,
    KeReleaseMutant,
    KeReleaseSemaphore,
    KeRemoveByKeyDeviceQueue,
    KeRemoveDeviceQueue,
    KeRemoveEntryDeviceQueue,
    KeRemoveQueue,
    KeRemoveQueueDpc,
    KeResetEvent,
    KeRestoreFloatingPointState,
    KeResumeThread,
    KeRundownQueue,
    KeSaveFloatingPointState,
    KeSetBasePriorityThread,
    KeSetDisableBoostThread,
    KeSetEvent,
    KeSetEventBoostPriority,
    KeSetPriorityProcess,
    KeSetPriorityThread,
    KeSetTimer,
    KeSetTimerEx,
    KeStallExecutionProcessor,
    KeSuspendThread,
    KeSynchronizeExecution,
    KeSystemTime,
    KeTestAlertThread,
    KeTickCount,
    KeTimeIncrement,
    KeWaitForMultipleObjects,
    KeWaitForSingleObject,
    KfRaiseIrql,
    KfLowerIrql,
    KiBugCheckData,
    KiUnlockDispatcherDatabase,
    LaunchDataPage,
    MmAllocateContiguousMemory,
    MmAllocateContiguousMemoryEx,
    MmAllocateSystemMemory,
    MmClaimGpuInstanceMemory,
    MmCreateKernelStack,
    MmDeleteKernelStack,
    MmFreeContiguousMemory,
    MmFreeSystemMemory,
    MmGetPhysicalAddress,
    MmIsAddressValid,
    MmLockUnlockBufferPages,
    MmLockUnlockPhysicalPage,
    MmMapIoSpace,
    MmPersistContiguousMemory,
    MmQueryAddressProtect,
    MmQueryAllocationSize,
    MmQueryStatistics,
    MmSetAddressProtect,
    MmUnmapIoSpace,
    NtAllocateVirtualMemory,
    NtCancelTimer,
    NtClearEvent,
    NtClose,
    NtCreateDirectoryObject,
    NtCreateEvent,
    NtCreateFile,
    NtCreateIoCompletion,
    NtCreateMutant,
    NtCreateSemaphore,
    NtCreateTimer,
    NtDeleteFile,
    NtDeviceIoControlFile,
    NtDuplicateObject,
    NtFlushBuffersFile,
    NtFreeVirtualMemory,
    NtFsControlFile,
    NtOpenDirectoryObject,
    NtOpenFile,
    NtOpenSymbolicLinkObject,
    NtProtectVirtualMemory,
    NtPulseEvent,
    NtQueueApcThread,
    NtQueryDirectoryFile,
    NtQueryDirectoryObject,
    NtQueryEvent,
    NtQueryFullAttributesFile,
    NtQueryInformationFile,
    NtQueryIoCompletion,
    NtQueryMutant,
    NtQuerySemaphore,
    NtQuerySymbolicLinkObject,
    NtQueryTimer,
    NtQueryVirtualMemory,
    NtQueryVolumeInformationFile,
    NtReadFile,
    NtReadFileScatter,
    NtReleaseMutant,
    NtReleaseSemaphore,
    NtRemoveIoCompletion,
    NtResumeThread,
    NtSetEvent,
    NtSetInformationFile,
    NtSetIoCompletion,
    NtSetSystemTime,
    NtSetTimerEx,
    NtSignalAndWaitForSingleObjectEx,
    NtSuspendThread,
    NtUserIoApcDispatcher,
    NtWaitForSingleObject,
    NtWaitForSingleObjectEx,
    NtWaitForMultipleObjectsEx,
    NtWriteFile,
    NtWriteFileGather,
    NtYieldExecution,
    ObCreateObject,
    ObDirectoryObjectType,
    ObInsertObject,
    ObMakeTemporaryObject,
    ObOpenObjectByName,
    ObOpenObjectByPointer,
    ObpObjectHandleTable,
    ObReferenceObjectByHandle,
    ObReferenceObjectByName,
    ObReferenceObjectByPointer,
    ObSymbolicLinkObjectType,
    ObfDereferenceObject,
    ObfReferenceObject,
    PhyGetLinkState,
    PhyInitialize,
    PsCreateSystemThread,
    PsCreateSystemThreadEx,
    PsQueryStatistics,
    PsSetCreateThreadNotifyRoutine,
    PsTerminateSystemThread,
    PsThreadObjectType,
    RtlAnsiStringToUnicodeString,
    RtlAppendStringToString,
    RtlAppendUnicodeStringToString,
    RtlAppendUnicodeToString,
    RtlAssert,
    RtlCaptureContext,
    RtlCaptureStackBackTrace,
    RtlCharToInteger,
    RtlCompareMemory,
    RtlCompareMemoryUlong,
    RtlCompareString,
    RtlCompareUnicodeString,
    RtlCopyString,
    RtlCopyUnicodeString,
    RtlCreateUnicodeString,
    RtlDowncaseUnicodeChar,
    RtlDowncaseUnicodeString,
    RtlEnterCriticalSection,
    RtlEnterCriticalSectionAndRegion,
    RtlEqualString,
    RtlEqualUnicodeString,
    RtlExtendedIntegerMultiply,
    RtlExtendedLargeIntegerDivide,
    RtlExtendedMagicDivide,
    RtlFillMemory,
    RtlFillMemoryUlong,
    RtlFreeAnsiString,
    RtlFreeUnicodeString,
    RtlGetCallersAddress,
    RtlInitAnsiString,
    RtlInitUnicodeString,
    RtlInitializeCriticalSection,
    RtlIntegerToChar,
    RtlIntegerToUnicodeString,
    RtlLeaveCriticalSection,
    RtlLeaveCriticalSectionAndRegion,
    RtlLowerChar,
    RtlMapGenericMask,
    RtlMoveMemory,
    RtlMultiByteToUnicodeN,
    RtlMultiByteToUnicodeSize,
    RtlNtStatusToDosError,
    RtlRaiseException,
    RtlRaiseStatus,
    RtlTimeFieldsToTime,
    RtlTimeToTimeFields,
    RtlTryEnterCriticalSection,
    RtlUlongByteSwap,
    RtlUnicodeStringToAnsiString,
    RtlUnicodeStringToInteger,
    RtlUnicodeToMultiByteN,
    RtlUnicodeToMultiByteSize,
    RtlUnwind,
    RtlUpcaseUnicodeChar,
    RtlUpcaseUnicodeString,
    RtlUpcaseUnicodeToMultiByteN,
    RtlUpperChar,
    RtlUpperString,
    RtlUshortByteSwap,
    RtlWalkFrameChain,
    RtlZeroMemory,
    XboxEEPROMKey,
    XboxHardwareInfo,
    XboxHDKey,
    XboxKrnlVersion,
    XboxSignatureKey,
    XeImageFileName,
    XeLoadSection,
    XeUnloadSection,
    READ_PORT_BUFFER_UCHAR,
    READ_PORT_BUFFER_USHORT,
    READ_PORT_BUFFER_ULONG,
    WRITE_PORT_BUFFER_UCHAR,
    WRITE_PORT_BUFFER_USHORT,
    WRITE_PORT_BUFFER_ULONG,
    XcSHAInit,
    XcSHAUpdate,
    XcSHAFinal,
    XcRC4Key,
    XcRC4Crypt,
    XcHMAC,
    XcPKEncPublic,
    XcPKDecPrivate,
    XcPKGetKeyLen,
    XcVerifyPKCS1Signature,
    XcModExp,
    XcDESKeyParity,
    XcKeyTable,
    XcBlockCrypt,
    XcBlockCryptCBC,
    XcCryptService,
    XcUpdateCrypto,
    RtlRip,
    XboxLANKey,
    XboxAlternateSignatureKeys,
    XePublicKeyData,
    HalBootSMCVideoMode,
    IdexChannelObject,
    HalIsResetOrShutdownPending,
    IoMarkIrpMustComplete,
    HalInitiateShutdown,
    RtlSnprintf,
    RtlSprintf,
    RtlVsnprintf,
    RtlVsprintf,
    HalEnableSecureTrayEject,
    HalWriteSMCScratchRegister,
    MmDbgAllocateMemory,
    MmDbgFreeMemory,
    MmDbgQueryAvailablePages,
    MmDbgReleaseAddress,
    MmDbgWriteCheck,
]

"""Injects and manages the Dynamic DXT loader."""

# pylint: disable=too-many-instance-attributes

import copy
import os
import struct

from xboxpy.interface import if_xbdm
from .export_info import ExportInfo
from .py_dll_loader import DLLLoader
from . import xbdm_exports
from . import xboxkrnl_exports


_XBDM_HOOK_COMMAND_FMT = "resume thread=0x%X"
_XBDM_HOOK_EXPORT_INFO = xbdm_exports.DmResumeThread


class _DynamicDXTLoader:
    """Manages communication with the Dynamic DXT loader."""

    def __init__(self):
        self._bootstrapped = False
        self._bootstrap_path = None

        self._l1_bootstrap_path = None
        self._l1_bootstrap = None
        self._loader_path = None
        self._loader = None

        self._module_info = {}

        self._xbdm_hook_proc = None
        self._dm_allocate_pool_with_tag = None

    def set_bootstrap_path(self, path):
        """Sets the path to the Dynamic DXT 'lib' directory."""
        self._bootstrap_path = path

        self._l1_bootstrap_path = os.path.join(
            self._bootstrap_path, "bootstrap_l1.asm.obj"
        )
        self._loader_path = os.path.join(
            self._bootstrap_path, "libdynamic_dxt_loader.dll"
        )

    def load(self, dll_path):
        """Attempts to load the given Dynamic DXT DLL."""
        if not self._bootstrap():
            return False

        with open(dll_path, "rb") as dll_file:
            raw_image = dll_file.read()

        cmd = f"ddxt!load size=0x{len(raw_image):x}"
        status, message = if_xbdm.xbdm_command(cmd, raw_image, len(raw_image))
        if status != 200:
            print(f"Load failed: {status} {message}")
            return False
        return True

    def _bootstrap(self):
        """Attempts to install the Dynamic DXT loader."""
        if self._bootstrapped:
            return True

        if self._check_loader_installed():
            return True

        if not self._bootstrap_path:
            raise Exception("Loader bootstrap path must be set via set_bootstrap_path.")

        self._prepare_bootstrap_dependencies()

        patch_memory = if_xbdm.GetMem(self._xbdm_hook_proc, len(self._l1_bootstrap))
        try:
            self._inject_loader()
        finally:
            if_xbdm.SetMem(self._xbdm_hook_proc, patch_memory)

        self._fill_loader_export_registry()

        return True

    def _check_loader_installed(self):
        response = if_xbdm.xbdm_command("ddxt!hello")
        if response[0] != 202:
            return False
        self._bootstrapped = True
        return True

    def _prepare_bootstrap_dependencies(self):
        """Loads files and fetches memory addresses for the injection process."""
        self._load_bootstrap_files()

        self._fetch_base_address("xbdm.dll")
        self._module_info["xbdm.dll"]["exports"] = xbdm_exports.XBDM_EXPORTS

        self._fetch_base_address("xboxkrnl.exe")
        self._module_info["xboxkrnl.exe"][
            "exports"
        ] = xboxkrnl_exports.XBOXKERNL_EXPORTS

        self._xbdm_hook_proc = self._resolve_export_info(
            "xbdm.dll", _XBDM_HOOK_EXPORT_INFO
        )
        self._dm_allocate_pool_with_tag = self._resolve_export_info(
            "xbdm.dll", xbdm_exports.DmAllocatePoolWithTag
        )

    def _load_bootstrap_files(self):
        with open(self._l1_bootstrap_path, "rb") as infile:
            self._l1_bootstrap = infile.read()

        with open(self._loader_path, "rb") as infile:
            self._loader = infile.read()

    def _fetch_base_address(self, module_name):
        for module in if_xbdm.modules:
            if module["name"] == module_name:
                info = copy.deepcopy(module)
                self._module_info[module_name] = info
                image_base = module["base"]
                temp = _read_u32(image_base + 0x3C)
                temp = _read_u32(image_base + temp + 0x78)
                info["export_count"] = _read_u32(image_base + temp + 0x14)
                info["export_base"] = image_base + _read_u32(image_base + temp + 0x1C)
                return
        raise Exception(f"Failed to fetch module information for {module_name}")

    def _resolve_export_info(self, module: str, export_info: ExportInfo) -> int:
        if export_info.address is not None:
            return export_info.address

        info = self._module_info.get(module)
        if not info:
            raise Exception(f"Failed to resolve export for unknown module {module}")

        export_count = info["export_count"]
        export_base = info["export_base"]

        index = export_info.ordinal - 1
        if index >= export_count:
            raise Exception(
                f"Ordinal {export_info.ordinal} out of range for module {module}. Export count is "
                f"{export_count}."
            )

        method_address = info["base"] + _read_u32(export_base + index * 4)
        export_info.address = method_address

        return method_address

    def _inject_loader(self):
        if_xbdm.SetMem(self._xbdm_hook_proc, self._l1_bootstrap)

        # The last DWORD of the loader is used to set the requested size and fetch the
        # result.
        l1_bootstrap_len = len(self._l1_bootstrap)
        io_address = self._xbdm_hook_proc + l1_bootstrap_len - 4

        loader = DLLLoader(self._loader)
        loader.load(self._resolve_import_by_ordinal, self._resolve_import_by_name)

        if not loader.image_size:
            raise Exception("Loader is corrupt, image size == 0")

        _write_u32(io_address, loader.image_size)
        _invoke_bootstrap(self._dm_allocate_pool_with_tag)
        allocated_address = _read_u32(io_address)
        if not allocated_address:
            raise Exception("Failed to allocate memory for loader image.")

        if not loader.relocate(allocated_address):
            loader.free()
            raise Exception("Failed to relocate loader image.")

        if_xbdm.SetMem(allocated_address, loader.image)

        # Put the L1 loader into entrypoint mode.
        _write_u32(io_address, 0)

        loader_entrypoint = loader.entry_point

        print(
            f"Loader installed at 0x{allocated_address:x} with entrypoint at "
            f"0x{loader_entrypoint:x}"
        )
        _invoke_bootstrap(loader_entrypoint)

        loader.free()

    def _fill_loader_export_registry(self):
        for info in self._module_info.values():
            module_name = info["name"]
            for export in info["exports"]:
                self._resolve_export_info(module_name, export)
                _populate_export_info(module_name, export)

    def _resolve_import_by_ordinal(self, module_name, ordinal):
        info = self._module_info.get(module_name)
        if not info:
            print(f"Failed to resolve export for unknown module {module_name}")
            return 0

        for export in info["exports"]:
            if export.ordinal == ordinal:
                return self._resolve_export_info(module_name, export)

        print(f"Failed to resolve export {ordinal} in {module_name}")
        return 0

    def _resolve_import_by_name(self, module_name, export_name):
        info = self._module_info.get(module_name)
        if not info:
            print(f"Failed to resolve export for unknown module {module_name}")
            return 0

        for export in info["exports"]:
            if export.name == export_name:
                return self._resolve_export_info(module_name, export)

        print(f"Failed to resolve export {export_name} in {module_name}")
        return 0


def _invoke_bootstrap(arg):
    if_xbdm.xbdm_command(_XBDM_HOOK_COMMAND_FMT % arg)


def _populate_export_info(module_name: str, info: ExportInfo):
    cmd = f'ddxt!export module="{module_name}" ordinal=0x{info.ordinal:x} addr=0x{info.address:x}'
    if info.name:
        cmd += f' name="{info.name}"'

    status, msg = if_xbdm.xbdm_command(cmd)
    if status != 200:
        raise Exception(
            f"Failed to populate export info for {module_name}@{info.ordinal}: {status} {msg}"
        )


# The helper functions in xboxpy use the same `resume` override as this loader and
# cannot be used.
def _write_u32(address, value):
    packed = struct.pack("<L", value)
    if_xbdm.SetMem(address, packed)


def _read_u32(address):
    value = if_xbdm.GetMem(address, 4)
    value = struct.unpack("<L", value)[0]
    return value


_loader = _DynamicDXTLoader()


def set_dyndxt_lib_path(path):
    """Sets the path to the dynamic ddxt 'lib' directory."""
    _loader.set_bootstrap_path(path)


def load(dll_path):
    """Attempts to load the given dynamic DXT DLL."""
    return _loader.load(dll_path)

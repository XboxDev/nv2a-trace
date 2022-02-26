"""Wrapper around the nxdk_dyndxt bundled dll_loader."""
import ctypes
import platform
import os

_RESOLVE_IMPORT_BY_ORDINAL = ctypes.CFUNCTYPE(
    ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32
)

_RESOLVE_IMPORT_BY_NAME = ctypes.CFUNCTYPE(
    ctypes.c_uint32, ctypes.c_char_p, ctypes.c_char_p
)


class DLLLoader:
    """Provides python bindings for the dll_loader bundled within nxdk_dyndxt."""

    LIBRARY_PATH = None
    _LIBRARY = None

    def __init__(self, raw_dll_data):
        self._hook_dll_loader()
        self.raw_image = raw_dll_data

    def load(self, resolve_import_by_ordinal, resolve_import_by_name):
        """Loads the raw DLL image owned by this loader instance.

        :param resolve_import_by_ordinal - Function to resolve the actual address of an exported
                function on the target. (module_name: str, ordinal: int) -> int
        :param resolve_import_by_name - Function to resolve the actual address of an exported
                function on the target. (module_name: str, export_name: str) -> int
        """
        image_data = ctypes.c_ubyte * len(self.raw_image)

        def unwrap_resolve_import_by_ordinal(module_name, ordinal):
            result = resolve_import_by_ordinal(module_name.decode("utf-8"), ordinal)
            return result

        def unwrap_resolve_import_by_name(module_name, export_name):
            result = resolve_import_by_name(
                module_name.decode("utf-8"), export_name.decode("utf-8")
            )
            return result

        result = self._LIBRARY.LoadDLL(
            image_data(*self.raw_image),
            ctypes.c_uint32(len(self.raw_image)),
            _RESOLVE_IMPORT_BY_ORDINAL(unwrap_resolve_import_by_ordinal),
            _RESOLVE_IMPORT_BY_NAME(unwrap_resolve_import_by_name),
        )
        if not result:
            raise Exception("Failed to load DLL")

    def relocate(self, new_base):
        """Relocates the loaded DLL image to the given base address."""
        return self._LIBRARY.RelocateDLL(ctypes.c_uint32(new_base))

    def free(self):
        """Releases the loaded DLL image."""
        self._LIBRARY.FreeDLL()

    @property
    def image(self):
        """Returns a copy of the current state of the loaded DLL image."""
        data = self._LIBRARY.LoadedImage()
        data_len = self.image_size

        data = ctypes.string_at(data, data_len)
        return data

    @property
    def image_size(self):
        """Returns the size of the loaded DLL image."""
        ret = self._LIBRARY.LoadedImageSize()
        return ret

    @property
    def entry_point(self):
        """Returns the (target) address of the entrypoint method of the loaded DLL image."""
        ret = self._LIBRARY.LoadedImageEntrypoint()
        return ret

    @classmethod
    def _hook_dll_loader(cls):
        if cls._LIBRARY:
            return

        if not cls.LIBRARY_PATH:
            raise Exception(
                "Path to py_dyndxt_bootstrap library must be set with set_bootstrap_lib_path"
            )
        cls._LIBRARY = _wrap_shared_object(cls.LIBRARY_PATH)


def _wrap_shared_object(lib_path):
    platform_name = platform.system()

    if platform_name == "Linux":
        library = ctypes.CDLL(os.path.join(lib_path, "libpy_dnydxt_bootstrap.so"))
    elif platform_name == "Darwin":
        library = ctypes.CDLL(os.path.join(lib_path, "libpy_dnydxt_bootstrap.dylib"))
    else:
        raise Exception(f"Unsupported platform {platform_name}")

    library.LoadDLL.argtypes = (
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_uint32,
        _RESOLVE_IMPORT_BY_ORDINAL,
        _RESOLVE_IMPORT_BY_NAME,
    )
    library.LoadDLL.restype = ctypes.c_bool

    library.RelocateDLL.argtypes = (ctypes.c_uint32,)
    library.RelocateDLL.restype = ctypes.c_bool

    library.LoadedImage.restype = ctypes.POINTER(ctypes.c_ubyte)
    library.LoadedImageSize.restype = ctypes.c_uint32
    library.LoadedImageEntrypoint.restype = ctypes.c_uint32

    library.FreeDLL.argtypes = None
    library.FreeDLL.restype = None

    return library


def set_bootstrap_lib_path(path):
    """Sets the path to the py_dyndxt_bootstrap lib directory."""
    DLLLoader.LIBRARY_PATH = path

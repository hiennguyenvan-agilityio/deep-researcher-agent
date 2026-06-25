from fs.memoryfs import MemoryFS

# from fs.osfs import OSFS

_vfs = None


def get_vfs():
    global _vfs

    if _vfs is None:
        _vfs = MemoryFS()
        # _vfs = OSFS('./')

    return _vfs

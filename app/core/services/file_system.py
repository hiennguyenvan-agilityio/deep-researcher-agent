from fs.osfs import OSFS

_fs = None


def get_fs():
    global _fs

    if _fs is None:
        # _fs = MemoryFS()
        _fs = OSFS("./tmp", create=True)

    return _fs

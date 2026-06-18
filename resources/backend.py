from deepagents.backends.filesystem import FilesystemBackend


_fileSystemBackend = None

def get_filesystem_backend():
    global _fileSystemBackend

    if _fileSystemBackend is None:
        _fileSystemBackend = FilesystemBackend()

    return _fileSystemBackend

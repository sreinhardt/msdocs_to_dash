from tarfile import TarFile, TarInfo
import io

def tar_write(tar, name, len, data):
    if not isinstance(name, str):
        name = str(name)
    member = None
    try:
        member = tar.getmember(name)
        return # already written
    except KeyError:
        pass
    info = TarInfo(name=name)
    info.size = len
    info.mode = 444
    tar.addfile(tarinfo=info, fileobj=data)
def tar_write_bytes(tar, name, data):
    tar_write(tar, name, len(data), io.BytesIO(data))
def tar_write_str(tar, name, data):
    tar_write_bytes(tar, name, data.encode('utf-8'))
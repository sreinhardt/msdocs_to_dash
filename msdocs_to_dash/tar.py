from tarfile import TarFile, TarInfo
import io

def tar_write(tar, name, data):
    info = TarInfo(name=name)
    info.size = len(data)
    info.mode = 444
    tar.add_file(tarinfo=info, fileobj=data)
def tar_write_bytes(tar, name, data):
    write(tar, name, io.BytesIO(data))
def tar_write_str(tar, name, data):
    tar_write_bytes(tar, name, data.encode('utf-8'))
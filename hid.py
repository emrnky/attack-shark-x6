import ctypes as C
import fcntl
import os
import select


class DevInfo(C.Structure):
    _fields_ = [
        ('bustype', C.c_uint32),
        ('vendor', C.c_uint16),
        ('product', C.c_uint16),
    ]


def ioc(direction, number, size):
    return direction << 30 | size << 16 | ord('H') << 8 | number


READ, WRITE = 2, 1
GET_INFO = ioc(READ, 0x03, C.sizeof(DevInfo))
GET_NAME = ioc(READ, 0x04, 256)
GET_PHYS = ioc(READ, 0x05, 256)


def nodes():
    names = [n for n in os.listdir('/dev') if n.startswith('hidraw')]
    return sorted(os.path.join('/dev', n) for n in names)


def paths():
    return [p for p in nodes() if os.access(p, os.R_OK)]


def text(f, question):
    raw = fcntl.ioctl(f, question, bytes(256))
    return raw.split(b'\0', 1)[0].decode()


def info(f):
    raw = fcntl.ioctl(f, GET_INFO, bytes(C.sizeof(DevInfo)))
    return DevInfo.from_buffer_copy(raw)


def interface(f):
    phys = text(f, GET_PHYS)
    return int(phys.rsplit('input', 1)[-1])


def describe(path):
    with open(path, 'rb', buffering=0) as f:
        i = info(f)
        return {
            'path': path,
            'vid': i.vendor,
            'pid': i.product,
            'product': text(f, GET_NAME),
            'interface': interface(f),
        }


def matches(d, vid, pid, iface):
    same = (d['vid'], d['pid']) == (vid, pid)
    return same and iface in (None, d['interface'])


def find_interfaces(vid, pid, iface=None):
    found = (describe(p) for p in paths())
    return [d for d in found if matches(d, vid, pid, iface)]


def show(d):
    ids = f"{d['vid']:04x}:{d['pid']:04x}"
    return f"{d['path']}  {ids}  input{d['interface']}  {d['product']}"


class HidInterface:
    def __init__(self, info):
        self.info = info
        self.path = info['path']
        self.fd = None

    def open(self):
        self.fd = os.open(self.path, os.O_RDWR)
        return self

    def close(self):
        os.close(self.fd)

    def __enter__(self):
        return self.open()

    def __exit__(self, *args):
        self.close()

    def set_feature(self, data):
        buf = bytearray(data)
        fcntl.ioctl(self.fd, ioc(READ | WRITE, 0x06, len(buf)), buf)

    def get_feature(self, report_id, length):
        buf = bytearray(length)
        buf[0] = report_id
        fcntl.ioctl(self.fd, ioc(READ | WRITE, 0x07, length), buf)
        return bytes(buf)

    def read_input(self, timeout=3.0):
        if select.select([self.fd], [], [], timeout)[0]:
            return os.read(self.fd, 64)
        return None


if __name__ == '__main__':
    for d in find_interfaces(0x1d57, 0xfa60, 1):
        print(show(d))

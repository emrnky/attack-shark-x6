import ctypes as C
import fcntl
import os
import select
import socket


class DevInfo(C.Structure):
    _fields_ = [
        ('bustype', C.c_uint32),
        ('vendor', C.c_uint16),
        ('product', C.c_uint16),
    ]


class UdevHeader(C.Structure):
    _fields_ = [
        ('prefix', C.c_char * 8),
        ('magic', C.c_uint32),
        ('header_size', C.c_uint32),
        ('properties_off', C.c_uint32),
        ('properties_len', C.c_uint32),
    ]


def ioc(direction, number, size):
    return direction << 30 | size << 16 | ord('H') << 8 | number


READ, WRITE = 2, 1

BUS_USB = 3
BUS_BLUETOOTH = 5

GET_INFO = ioc(READ, 0x03, C.sizeof(DevInfo))
GET_NAME = ioc(READ, 0x04, 256)
GET_PHYS = ioc(READ, 0x05, 256)
SET_FEATURE = 0x06
GET_FEATURE = 0x07

NETLINK_KOBJECT_UEVENT = 15
UDEV_GROUP = 2


def nodes():
    names = [n for n in os.listdir('/dev') if n.startswith('hidraw')]
    return sorted(os.path.join('/dev', n) for n in names)


def node(link, links):
    bus, vid, pid, iface = links[link]
    found = [n for n in find_interfaces(vid, pid, iface) if n['bus'] == bus]
    return dict(found[0], link=link) if found else None


def connect(links):
    nodes = (node(link, links) for link in links)
    return next((n for n in nodes if n), None)


def paths():
    return [p for p in nodes() if os.access(p, os.R_OK)]


def text(f, question):
    raw = fcntl.ioctl(f, question, bytes(256))
    return raw.split(b'\0', 1)[0].decode()


def devinfo(f):
    raw = fcntl.ioctl(f, GET_INFO, bytes(C.sizeof(DevInfo)))
    return DevInfo.from_buffer_copy(raw)


def interface(f):
    tail = text(f, GET_PHYS).rsplit('input', 1)[-1]
    return int(tail) if tail.isdigit() else None


def describe(path):
    with open(path, 'rb', buffering=0) as f:
        info = devinfo(f)
        return {
            'path': path,
            'bus': info.bustype,
            'vid': info.vendor,
            'pid': info.product,
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

    def __enter__(self):
        return self.open()

    def __exit__(self, *args):
        self.close()

    def open(self):
        self.fd = os.open(self.path, os.O_RDWR)
        return self

    def close(self):
        os.close(self.fd)

    def fileno(self):
        return self.fd

    def set_feature(self, data):
        buf = bytearray(data)
        question = ioc(READ | WRITE, SET_FEATURE, len(buf))
        fcntl.ioctl(self.fd, question, buf)

    def get_feature(self, report_id, size):
        buf = bytearray(size)
        buf[0] = report_id
        question = ioc(READ | WRITE, GET_FEATURE, size)
        fcntl.ioctl(self.fd, question, buf)
        return bytes(buf)

    def read_input(self, timeout=3.0):
        if not select.select([self], [], [], timeout)[0]:
            return None
        try:
            return os.read(self.fd, 64)
        except OSError:
            return b''


class Events:
    def __init__(self):
        family, kind = socket.AF_NETLINK, socket.SOCK_DGRAM
        self.sock = socket.socket(family, kind, NETLINK_KOBJECT_UEVENT)
        self.sock.bind((0, UDEV_GROUP))

    def fileno(self):
        return self.sock.fileno()

    def read(self):
        msg = self.sock.recv(8192)
        if not msg.startswith(b'libudev'):
            return {}
        head = UdevHeader.from_buffer_copy(msg)
        start, size = head.properties_off, head.properties_len
        pairs = msg[start:start + size].split(b'\0')
        return dict(p.decode().split('=', 1) for p in pairs if b'=' in p)


if __name__ == '__main__':
    for pid in (0xfa60, 0xfa61):
        for d in find_interfaces(0x1d57, pid):
            print(show(d))

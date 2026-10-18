import time

from . import decode
from . import defaults as d
from .hid import HidInterface


class Mouse:
    def __init__(self, info):
        self.info = info
        self.link = info['link']
        self.iface = HidInterface(info)
        self.timeout = d.FRAME_TIMEOUT

    def __enter__(self):
        self.iface.open()
        return self

    def __exit__(self, *args):
        self.iface.close()

    def fileno(self):
        return self.iface.fileno()

    def frame(self, timeout=d.FRAME_TIMEOUT):
        return self.iface.read_input(timeout)

    def event(self, frame):
        name, value = decode.event(frame)
        if name == 'battery' and self.link == 'cable':
            return name, (value[0], 'charging')
        return name, value

    def battery(self, timeout=d.FRAME_TIMEOUT):
        end = time.monotonic() + timeout
        while (left := end - time.monotonic()) > 0:
            frame = self.frame(left)
            if frame is None:
                break
            if not frame:
                raise ConnectionError('mouse was disconnected')
            if frame[0] != d.REPORT_EVENT:
                continue
            name, value = self.event(frame)
            if name == 'battery' and value[1]:
                return value
        raise TimeoutError(f'no battery frame in {timeout} s: asleep or off')

    def ready(self):
        size = d.REPORT_SIZE[d.REPORT_READ]
        for poll in range(d.READ_POLLS):
            time.sleep(d.READ_DELAY)
            if self.iface.get_feature(d.REPORT_READ, size)[1] == d.READY:
                return True
        return False

    def report(self, report_id):
        size = d.REPORT_SIZE[report_id]
        request = bytes([d.REPORT_READ, report_id, size, 0, 0, 0, 0, 0])
        for attempt in range(d.READ_RETRIES):
            self.iface.set_feature(request)
            if self.ready():
                return self.iface.get_feature(report_id, size)
        raise TimeoutError(f'report {report_id:02x} not ready: asleep or off')

    def polling_rate(self):
        return decode.polling(self.report(d.REPORT_POLLING))

    def sensor(self):
        return decode.dec_repid04(self.report(d.REPORT_SENSOR))

    def light(self):
        return decode.dec_repid05(self.report(d.REPORT_LIGHT))

    def buttons(self):
        return decode.buttons(self.report(d.REPORT_BUTTONS))

    def settings(self):
        return {
            'polling-rate': self.polling_rate(),
            'sensor': self.sensor(),
            'light': self.light(),
            'buttons': self.buttons(),
        }

import json
import select
import time
from contextlib import ExitStack

from . import defaults as d
from .decode import sleep_state
from .hid import Events, HidInterface, connect, node
from .x6 import Mouse


def send(**values):
    print(json.dumps(values), flush=True)


def watch(info, events):
    send(link=info['link'], path=info['path'])
    last = None
    dongle = node('dongle', d.LINKS) if info['link'] == 'bluetooth' else None
    with ExitStack() as stack:
        mouse = stack.enter_context(Mouse(info))
        standby = [stack.enter_context(HidInterface(dongle))] if dongle else []
        while True:
            ready = select.select([mouse, events, *standby], [], [])[0]
            if events in ready and events.read().get('SUBSYSTEM') == 'hidraw':
                if connect(d.LINKS) != info:
                    return connect(d.LINKS)
            if standby and standby[0] in ready:
                if standby[0].read_input(0):
                    return dongle
                standby.clear()
            if mouse not in ready:
                continue
            frame = mouse.frame(0)
            if not frame:
                return connect(d.LINKS)
            if len(frame) < 5 or frame[0] != d.REPORT_EVENT:
                continue
            if frame[2] == d.EVENT_DPI:
                send(stage=mouse.event(frame)[1])
            if frame[2] == d.EVENT_LIGHT:
                send(light=mouse.event(frame)[1])
            if frame[2] != d.EVENT_BATTERY:
                continue
            percent, charge = mouse.event(frame)[1]
            now = time.monotonic()
            state = sleep_state(now - last) if last else ''
            last = now
            send(battery=percent, charge=charge, state=state)


if __name__ == '__main__':
    events = Events()
    info = connect(d.LINKS)
    while True:
        if info:
            info = watch(info, events)
        else:
            events.read()
            info = connect(d.LINKS)

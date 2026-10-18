import json
import sys

from . import defaults as d
from .hid import HidInterface, connect, find_interfaces, node
from .x6 import Mouse


def moved(info):
    nodes = find_interfaces(d.VENDOR_USB, d.PRODUCT_DONGLE, 1)
    if info['link'] != 'dongle' or not nodes:
        return
    with HidInterface(nodes[0]) as movement:
        movement.read_input(None)


def fresh(info, get):
    for attempt in range(d.MOVE_TRIES):
        moved(info)
        try:
            return get()
        except TimeoutError as error:
            failed = error
    raise failed


def status(mouse, info):
    return {
        'polling-rate': fresh(info, mouse.polling_rate),
        'sensor': fresh(info, mouse.sensor),
        'light': fresh(info, mouse.light),
        'buttons': fresh(info, mouse.buttons),
    }


def read():
    info = node(sys.argv[1], d.LINKS) if len(sys.argv) > 1 else connect(d.LINKS)
    if info is None:
        raise SystemExit('No X6 found: plug in the dongle or cable')
    if info['link'] == 'bluetooth':
        raise SystemExit('Settings are not readable over bluetooth')
    with Mouse(info) as mouse:
        try:
            values = status(mouse, info)
        except TimeoutError as error:
            raise SystemExit(f'Could not read settings: {error}')
    print(json.dumps({'link': info['link'], 'path': info['path'], **values}), flush=True)


if __name__ == '__main__':
    read()

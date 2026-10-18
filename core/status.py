from . import defaults as d
from .hid import connect
from .x6 import Mouse


def status(mouse):
    try:
        percent, charge = mouse.battery()
        battery = f'{percent}% {charge}'
    except TimeoutError:
        battery = 'unknown: asleep'
    return {'battery': battery, **mouse.settings()}


def stages(sensor):
    shown = []
    for i, (dpi, on) in enumerate(zip(sensor['dpi'], sensor['enabled']), 1):
        if on:
            shown.append(f'{dpi}*' if i == sensor['active'] else f'{dpi}')
    return ' '.join(shown)


def show(info, values):
    sensor, light = values['sensor'], values['light']
    print(f"link          {info['link']} {info['path']}")
    print(f"battery       {values['battery']}")
    print(f"polling rate  {values['polling-rate']} Hz")
    print(f"dpi           {stages(sensor)}")
    print(f"ripple        {sensor['ripple']}")
    print(f"angle snap    {sensor['angle-snap']}")
    print(f"motion sync   {sensor['motion-sync']}")
    print(f"light         {light['mode']} #{light['color']} "
          f"speed {light['speed']} brightness {light['brightness']}")
    print(f"sleep         {light['sleep']} min")
    print(f"deep sleep    {light['deep-sleep']} min")
    print(f"key response  {light['key-response']} ms")
    for i, button in enumerate(values['buttons'], 1):
        print(f"button {i:<6} {button}")


def main():
    info = connect(d.LINKS)
    if info is None:
        raise SystemExit('No X6 found: plug in the dongle or cable')
    if info['link'] == 'bluetooth':
        raise SystemExit('Settings are not readable over bluetooth')
    with Mouse(info) as mouse:
        try:
            values = status(mouse)
        except TimeoutError as error:
            raise SystemExit(f'Could not read settings: {error}')
    show(info, values)


if __name__ == '__main__':
    main()

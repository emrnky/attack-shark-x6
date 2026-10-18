from . import defaults as d


def in_range(name, val, low, high, step=1):
    if val not in range(low, high + 1, step):
        steps = f' in steps of {step}' if step != 1 else ''
        raise ValueError(f'{name} {val} is not in {low}-{high}{steps}')
    return val


def battery_level(val: d.Level) -> d.Percent:
    low, high = d.BATTERY_LEVELS
    return in_range('Battery level', val, low, high) * d.BATTERY_STEP


def charge(state: int) -> str:
    if state not in d.CHARGE_NAME:
        raise ValueError(f'Charge state {state} is unknown')
    return d.CHARGE_NAME[state]


def light_mode(mode: d.LMode) -> str:
    return d.LIGHT_MODES[in_range('Light mode', mode, 0,
                                  len(d.LIGHT_MODES) - 1)]


def light_speed(raw: int) -> int:
    low, high = d.LIGHT_SPEED
    return in_range('Light speed', 9 - raw, low, high)


def brightness(val: int) -> int:
    low, high = d.LIGHT_BRIGHTNESS
    return in_range('Brightness', val, low, high)


def sleep_time(raw: int) -> float:
    low, high = d.SLEEP_TIME
    return in_range('Sleep time', raw, low, high) * d.SLEEP_STEP


def deep_sleep_time(high_half: int, low_half: int) -> int:
    low, high = d.DEEP_SLEEP_TIME
    return in_range('Deep sleep time', high_half << 4 | low_half, low, high)


def key_response(raw: int) -> int:
    low, high = d.KEY_RESPONSE
    step = d.KEY_RESPONSE_STEP
    return in_range('Key response', raw * step, low, high, step)


def polling_rate(code: int) -> int:
    if code not in d.POLLING_CODE:
        raise ValueError(f'Polling rate code {code:#04x} is unknown')
    return d.POLLING_CODE[code]


def dpi_value(low: int, high: int) -> int:
    val = (high << 8 | low) + 1
    return in_range('DPI', val * d.DPI_STEP, d.DPI_MIN, d.DPI_MAX, d.DPI_STEP)


def color(rgb) -> str:
    return bytes(rgb).hex()


def sleep_state(gap: float) -> str:
    if 0 < gap < d.AWAKE_GAP:
        return 'awake'
    if d.AWAKE_GAP <= gap < d.FRAME_TIMEOUT:
        return 'asleep'
    return 'unknown'


def action(slot):
    if slot.action == d.ACTION_KEY:
        return f'key {slot.modifiers:02x}:{slot.key:02x}'
    if slot.action == d.ACTION_MACRO:
        return f'macro {slot.key}'
    if slot.action not in d.ACTION_NAME:
        raise ValueError(f'Button action {slot.action:02x} is unknown')
    return d.ACTION_NAME[slot.action]


def checked(data, report_id):
    if not data or data[0] != report_id:
        got = f'{data[0]:02x}' if data else 'empty'
        raise ValueError(f'Expected report {report_id:02x}, got {got}')
    size = d.REPORT_SIZE[report_id]
    if len(data) != size:
        raise ValueError(f'Report {report_id:02x} is {len(data)} bytes, '
                         f'expected {size}')
    if report_id == d.REPORT_POLLING:
        ok = data[3] == data[2] ^ 0xff
    elif report_id in d.CHECKSUM_AT:
        at = d.CHECKSUM_AT[report_id]
        ok = sum(data[2:at]) == int.from_bytes(data[at:at + 2], 'big')
    else:
        ok = True
    if not ok:
        raise ValueError(f'Report {report_id:02x} has a bad checksum')
    return data


def dec_repid04(data) -> dict:
    """Report 04: DPI stages (active, enabled, values, colors) and the
    sensor options ripple, angle snap and motion sync."""
    raw = d.RepID_04.from_buffer_copy(checked(data, d.REPORT_SENSOR), 2)
    return {
        'active': in_range('Active stage', raw.active, 1, d.DPI_STAGES),
        'enabled': [bool(raw.enabled >> i & 1) for i in range(d.DPI_STAGES)],
        'dpi': [dpi_value(*pair) for pair in zip(raw.dpi_low, raw.dpi_high)],
        'colors': [color(c) for c in raw.colors],
        'ripple': bool(raw.ripple),
        'angle-snap': bool(raw.angle_snap),
        'motion-sync': bool(raw.motion_sync),
    }


def dec_repid05(data) -> dict:
    """Report 05: light mode, speed, brightness and color, plus the sleep
    and deep sleep timers and the key response time."""
    raw = d.RepID_05.from_buffer_copy(checked(data, d.REPORT_LIGHT), 2)
    return {
        'mode': light_mode(raw.mode),
        'speed': light_speed(raw.speed),
        'brightness': brightness(raw.brightness),
        'color': color(raw.color),
        'sleep': sleep_time(raw.sleep),
        'deep-sleep': deep_sleep_time(raw.deep_sleep_high,
                                      raw.deep_sleep_low),
        'key-response': key_response(raw.key_response),
    }


def dec_repid06(data) -> int:
    """Report 06: polling rate in Hz."""
    return polling_rate(checked(data, d.REPORT_POLLING)[2])


def dec_repid08(data) -> list:
    """Report 08: the action bound to each of the 18 button slots."""
    raw = d.Buttons.from_buffer_copy(checked(data, d.REPORT_BUTTONS), 2)
    return [action(slot) for slot in raw.slots]


def event(frame):
    if len(frame) < 5 or frame[0] != d.REPORT_EVENT:
        raise ValueError(f'Not an event frame: {bytes(frame).hex(" ")}')
    if frame[1] != d.MODEL:
        raise ValueError(f'Event from model {frame[1]:02x}, not the X6')
    code, first, second = frame[2], frame[3], frame[4]
    if code == d.EVENT_BATTERY:
        return 'battery', (battery_level(second), charge(first))
    if code == d.EVENT_LEVEL:
        return 'level', battery_level(first)
    if code == d.EVENT_DPI:
        return 'dpi', in_range('DPI stage', first, 1, d.DPI_STAGES)
    if code == d.EVENT_LIGHT:
        return 'light', light_mode(first >> 4)
    if code == d.EVENT_ACK:
        return 'ack', (second, first == 0)
    raise ValueError(f'Event {code:02x} is unknown')

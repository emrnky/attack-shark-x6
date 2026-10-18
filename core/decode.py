from . import defaults as d


def battery_level(val: d.Level) -> d.Percent:
    low, high = d.BATTERY_LEVELS
    if val not in range(low, high + 1):
        raise ValueError(f'Battery level {val} is not in {low}-{high}')
    return val * d.BATTERY_STEP


def light_mode(mode: d.LMode) -> d.LModeName:
    last = len(d.LIGHT_MODES) - 1
    if mode not in range(last + 1):
        raise ValueError(f'Light mode {mode} is not in 0-{last}')
    return d.LIGHT_MODES[mode]


def dpi_value(low: int, high: int) -> int:
    val = ((high << 8 | low) + 1) * d.DPI_STEP
    if val not in range(d.DPI_MIN, d.DPI_MAX + 1, d.DPI_STEP):
        raise ValueError(f'DPI {val} is not in {d.DPI_MIN}-{d.DPI_MAX} '
                         f'in steps of {d.DPI_STEP}')
    return val


def action(slot):
    if slot.action == d.ACTION_KEY:
        return f'key {slot.modifiers:02x}:{slot.key:02x}'
    if slot.action == d.ACTION_MACRO:
        return f'macro {slot.key}'
    return d.ACTION_NAME.get(slot.action, f'unknown {slot.action:02x}')


if __name__ == "__main__":

    # print(battery_level(2))
    """
       vals are 1-10 
            -> 5 will return 50% 
       else will return None
    """
    # print(light_mode(0.5))
    """
        vals are as long as the color mode list 
        else will return None
    """
    # print(dpi_value(0x07, 0x02))  # highest
    # print(dpi_value(0x02, 0x07))  # higher than highest error
    # print(dpi_value(0x0f, 0x00))
    # print(dpi_value(-1, 1)) error negative

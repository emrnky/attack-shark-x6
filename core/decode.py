from . import defaults as d
from .defaults import Level, LMode, LModeName, Percent


def level(val: Level) -> Percent:
    low, high = d.BATTERY_LEVELS
    if val not in range(low, high + 1):
        raise ValueError(f'Battery level {val} is not in {low}-{high}')
    return val * d.BATTERY_STEP


def light_mode(mode: LMode) -> LModeName:
    last = len(d.LIGHT_MODES) - 1
    if mode not in range(last + 1):
        raise ValueError(f'Light mode {mode} is not in 0-{last}')
    return d.LIGHT_MODES[mode]


def dpi(low: int, high: int) -> int:
    val = ((high << 8 | low) + 1) * d.DPI_STEP
    if val not in range(d.DPI_MIN, d.DPI_MAX + 1, d.DPI_STEP):
        raise ValueError(f'DPI {val} is not in {d.DPI_MIN}-{d.DPI_MAX} '
                         f'in steps of {d.DPI_STEP}')
    return val


if __name__ == "__main__":

    # print(level(2))
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
    # print(dpi(0x07, 0x02))  # highest
    # print(dpi(0x02, 0x07))  # higher than highest error
    # print(dpi(0x0f, 0x00))
    # print(dpi(-1, 1)) error negative

"""Attack Shark X6 protocol constants.

Event frames (input report 0x03)::

    [0] 0x03   [1] model   [2] event   [3] value   [4] value

Settings (feature reports), as read back from the mouse::

    [0] report id   [1] length   ... payload

Read a report with ``a0 <id> <size> 00 00 00 00 00``, poll ``a0`` until byte 1
is 0x01, then fetch ``<id>``.
"""

# ---------------------------------------------------------------- identity ---
BUS_USB = 3
BUS_BLUETOOTH = 5

VENDOR_USB = 0x1d57
VENDOR_BLUETOOTH = 0x045e
PRODUCT_CABLE = 0xfa61
PRODUCT_DONGLE = 0xfa60
PRODUCT_BLUETOOTH = 0x0040
PRODUCT_IDS = (PRODUCT_CABLE, PRODUCT_DONGLE)

MODEL = 0x10
CONFIG_INTERFACE = 2
PROFILE = 0x01
READY = 0x01

LINKS = {
    'cable': (BUS_USB, VENDOR_USB, PRODUCT_CABLE, CONFIG_INTERFACE),
    'bluetooth': (BUS_BLUETOOTH, VENDOR_BLUETOOTH, PRODUCT_BLUETOOTH, None),
    'dongle': (BUS_USB, VENDOR_USB, PRODUCT_DONGLE, CONFIG_INTERFACE),
}

# ------------------------------------------------------------------ events ---
EVENT_DPI = 0x10
# EVENT_POLLING = 0x20
EVENT_BATTERY = 0x40
EVENT_ACK = 0x50
EVENT_LEVEL = 0x60
EVENT_LIGHT = 0x70
EVENT_PROFILE = 0x80

EVENTS = {
    'dpi': EVENT_DPI,
    # 'polling': EVENT_POLLING,
    'battery': EVENT_BATTERY,
    'ack': EVENT_ACK,
    'level': EVENT_LEVEL,
    'light': EVENT_LIGHT,
    'profile': EVENT_PROFILE,
}
EVENT_NAME = {v: k for k, v in EVENTS.items()}

CHARGE_DISCHARGING = 0x01
CHARGE_FULL = 0x02
CHARGE_CHARGING = 0x03

CHARGE = {
    'discharging': CHARGE_DISCHARGING,
    'full': CHARGE_FULL,
    'charging': CHARGE_CHARGING,
}
CHARGE_NAME = {v: k for k, v in CHARGE.items()}

BATTERY_LEVELS = (1, 10)
BATTERY_STEP = 10

# ------------------------------------------------------------- report ids ----
REPORT_EVENT = 0x03
REPORT_SENSOR = 0x04
REPORT_LIGHT = 0x05
REPORT_POLLING = 0x06
REPORT_BUTTONS = 0x08
REPORT_MACRO = 0x09
REPORT_INFO = 0x0b
REPORT_COMMIT = 0x0c
REPORT_READ = 0xa0

READABLE = (REPORT_SENSOR, REPORT_LIGHT, REPORT_POLLING, REPORT_BUTTONS,
            REPORT_INFO)

REPORT_SIZE = {
    REPORT_SENSOR: 52,
    REPORT_LIGHT: 13,
    REPORT_POLLING: 9,
    REPORT_BUTTONS: 59,
    REPORT_MACRO: 64,
    REPORT_INFO: 8,
    REPORT_COMMIT: 6,
    REPORT_READ: 8,
}

REPORT_LENGTH = {
    REPORT_SENSOR: 0x38,
    REPORT_LIGHT: 0x0f,
    REPORT_POLLING: 0x09,
    REPORT_BUTTONS: 0x3b,
    REPORT_COMMIT: 0x0a,
}

CHECKSUM_AT = {
    REPORT_SENSOR: 49,
    REPORT_LIGHT: 10,
    REPORT_BUTTONS: 56,
}

COMMIT = bytes([REPORT_COMMIT, 0x0a, PROFILE, 0xfe, 0x01, 0xfe])

# ----------------------------------------------------------------- timing ---
FRAME_TIMEOUT = 6
AWAKE_GAP = 3

READ_RETRIES = 20
READ_POLLS = 3
READ_DELAY = 0.1
ACK_TIMEOUT = 0.5
ACK_RETRIES = 10

# ----------------------------------------------------------------- values ---
POLLING_RATES = {1000: 0x01, 500: 0x02, 250: 0x04, 125: 0x08}
POLLING_BY_CODE = {v: k for k, v in POLLING_RATES.items()}
POLLING_NAMES = {
    1000: 'esports',
    500: 'gaming',
    250: 'office',
    125: 'power-saving',
}

DPI_MIN = 50
DPI_MAX = 26000
DPI_STEP = 50
DPI_STAGES = 8

LIGHT_MODES = [
    'off',
    'static',
    'breathing',
    'neon',
    'color-breathing',
    'static-dpi',
    'breathing-dpi',
    # 'rainbow-wave',
    # 'lightning',
    # 'static-mixed',
    # 'marquee',
    # 'marquee-2',
]
LIGHT_MODE = {name: code for code, name in enumerate(LIGHT_MODES)}

BRIGHTNESS_MODES = (LIGHT_MODE['static'], 9)
LIGHT_SPEED = (4, 8)
LIGHT_BRIGHTNESS = (1, 8)
SLEEP_TIME = (1, 60)
DEEP_SLEEP_TIME = (1, 60)
KEY_RESPONSE = (4, 50)
KEY_RESPONSE_STEP = 2

# ---------------------------------------------------------------- buttons ---
BUTTON_SLOTS = 18

# BUTTONS = {
#     1: 'left',
#     2: 'right',
#     3: 'wheel',
#     4: 'dpi',
#     7: 'side-front',
#     8: 'side-rear',
#     9: 'mode',
# }

ACTION_KEY = 0x11
ACTION_MACRO = 0x12

ACTIONS = {
    'off': 0x01,
    'left': 0x02,
    'right': 0x03,
    'middle': 0x04,
    'backward': 0x05,
    'forward': 0x06,
    'double-click': 0x07,
    'fire': 0x08,
    'scroll-up': 0x09,
    'scroll-down': 0x0a,
    # 'scroll-left': 0x0b,
    # 'scroll-right': 0x0c,
    'dpi-cycle': 0x0d,
    'dpi-up': 0x0e,
    'dpi-down': 0x0f,
    'easy-aim': 0x10,
    'key': 0x11,
    'macro': 0x12,
    # 'led-loop': 0x13,
    'media-player': 0x15,
    'previous-track': 0x16,
    'next-track': 0x17,
    'play-pause': 0x18,
    'stop': 0x19,
    'mute': 0x1a,
    'volume-up': 0x1b,
    'volume-down': 0x1c,
    'calculator': 0x1d,
    'email': 0x1e,
    'browser-forward': 0x20,
    'browser-backward': 0x21,
    'browser-stop': 0x22,
    # 'my-computer': 0x23,
    'browser-refresh': 0x24,
    'browser-home': 0x25,
    'browser-search': 0x26,
    'profile-cycle': 0x34,
    'profile-up': 0x35,
    'profile-down': 0x36,
    'light-mode': 0x3c,
}
ACTION_NAME = {v: k for k, v in ACTIONS.items()}

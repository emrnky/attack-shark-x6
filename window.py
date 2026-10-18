import ctypes
import ctypes.util
import importlib
import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

Gdk = importlib.import_module("gi.repository.Gdk")
Gio = importlib.import_module("gi.repository.Gio")
GLib = importlib.import_module("gi.repository.GLib")
Gtk = importlib.import_module("gi.repository.Gtk")

name = "Attack Shark X6"
here = os.path.dirname(os.path.abspath(__file__))

fonts = ctypes.CDLL("libfontconfig.so.1")
for font in ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf"):
    fonts.FcConfigAppFontAddFile(None, os.path.join(here, "fonts", font).encode())

Gtk.init()

desktop = Gio.Settings.new("org.gnome.desktop.interface")
theme = Gtk.Settings.get_default()
theme.props.gtk_theme_name = desktop.get_string("gtk-theme")
theme.props.gtk_application_prefer_dark_theme = desktop.get_string("color-scheme") == "prefer-dark"

css = Gtk.CssProvider()
css.load_from_string("""
window.popup {
    border-radius: 0 0 12px 12px;
    font-family: "DejaVu Sans Mono";
}
.mouse {
    line-height: 1;
}
""")
Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

window = Gtk.Window(title=name, decorated=False, resizable=False)
window.add_css_class("popup")

RIGHT, TOP = 1, 2
LAYER_TOP = 2
KEYBOARD_ON_DEMAND = 2

layer = ctypes.util.find_library("gtk4-layer-shell")
shell = ctypes.CDLL(layer) if layer else None
if shell and shell.gtk_layer_is_supported():
    get = ctypes.pythonapi.PyCapsule_GetPointer
    get.restype = ctypes.c_void_p
    get.argtypes = [ctypes.py_object, ctypes.c_char_p]
    pointer = ctypes.c_void_p(get(window.__gpointer__, None))
    shell.gtk_layer_init_for_window(pointer)
    shell.gtk_layer_set_layer(pointer, LAYER_TOP)
    shell.gtk_layer_set_keyboard_mode(pointer, KEYBOARD_ON_DEMAND)
    shell.gtk_layer_set_anchor(pointer, TOP, True)
    shell.gtk_layer_set_anchor(pointer, RIGHT, True)
    shell.gtk_layer_set_margin(pointer, RIGHT, 8)

grid = Gtk.Grid(column_spacing=12, row_spacing=8)
for side in ("top", "bottom", "start", "end"):
    getattr(grid, f"set_margin_{side}")(16)
window.set_child(grid)

logo = Gtk.Image.new_from_file(os.path.join(here, "icons", "logo-dark.svg"))
logo.set_pixel_size(24)
heading = Gtk.Label(label=name, xalign=0)
heading.add_css_class("title-3")
title = Gtk.Box(spacing=8, margin_bottom=8)
title.append(logo)
title.append(heading)
grid.attach(title, 0, 0, 4, 1)
hint = Gtk.Label(xalign=0, margin_top=8)
hint.add_css_class("dim-label")
values = {}


def frames(path):
    with open(path, encoding="utf-8") as f:
        shots = [shot.split("\n") for shot in f.read().split("\f")]
    height = max(len(shot) for shot in shots)
    shots = [shot + [""] * (height - len(shot)) for shot in shots]
    used = [r for r in range(height) if any(shot[r].strip() for shot in shots)]
    width = max(len(line) for shot in shots for line in shot)
    return ["\n".join(line.ljust(width).replace(" ", "⠀") for line in shot[used[0]:used[-1] + 1])
            for shot in shots]


shots = frames(os.path.join(here, "mouse.txt"))
mouse = Gtk.Label(label=shots[0], halign=Gtk.Align.CENTER, margin_top=12)
mouse.add_css_class("mouse")
mouse.add_css_class("dim-label")
frame = 0
timer = None


def spin():
    global frame
    frame = (frame + 1) % len(shots)
    mouse.set_text(shots[frame])
    return True


def setup(names):
    for i, key in enumerate(names):
        row, col = i // 2 + 1, i % 2 * 2
        label = Gtk.Label(label=key.title().replace("Dpi", "DPI"), xalign=0, margin_start=32 if col else 0)
        label.add_css_class("dim-label")
        values[key] = Gtk.Label(label="-", xalign=0, width_chars=14)
        values[key].add_css_class("heading")
        grid.attach(label, col, row, 1, 1)
        grid.attach(values[key], col + 1, row, 1, 1)
    grid.attach(hint, 0, len(names) // 2 + 2, 4, 1)
    grid.attach(mouse, 0, len(names) // 2 + 3, 4, 1)


def show():
    global timer
    window.present()
    timer = timer or GLib.timeout_add(80, spin)


def hide():
    global timer
    window.set_visible(False)
    if timer:
        GLib.source_remove(timer)
        timer = None


def toggle():
    hide() if window.get_visible() else show()
    return False


def escape(controller, key, code, state):
    if key == Gdk.KEY_Escape:
        hide()
        return True
    return False


keyboard = Gtk.EventControllerKey()
keyboard.connect("key-pressed", escape)
window.add_controller(keyboard)


def update(status, note):
    for key, label in values.items():
        label.set_text(str(status.get(key, "-")))
    hint.set_text(note)

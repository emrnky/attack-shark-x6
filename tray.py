import ctypes.util
import importlib
import json
import os
import sys

layer = ctypes.util.find_library("gtk4-layer-shell")
if layer and layer not in os.environ.get("LD_PRELOAD", ""):
    os.environ["LD_PRELOAD"] = layer
    os.execv(sys.executable, [sys.executable] + sys.argv)

Gio = importlib.import_module("gi.repository.Gio")
GLib = importlib.import_module("gi.repository.GLib")

import window


here = os.path.dirname(os.path.abspath(__file__))
waiting = "move the mouse to read the settings"

with open(os.path.join(here, "tray.xml")) as f:
    sni, menu = Gio.DBusNodeInfo.new_for_xml(f.read()).interfaces


def tooltip(text):
    return GLib.Variant("(sa(iiay)ss)", ("", [], window.name, text))


item = {
    "Id": GLib.Variant("s", "attack-shark-x6"),
    "Title": GLib.Variant("s", window.name),
    "Status": GLib.Variant("s", "Active"),
    "IconName": GLib.Variant("s", "logo-dark"),
    "IconThemePath": GLib.Variant("s", os.path.join(here, "icons")),
    "ToolTip": tooltip(""),
    "ItemIsMenu": GLib.Variant("b", False),
    "Menu": GLib.Variant("o", "/Menu"),
}

labels = {1: "Settings", 2: "Quit"}
props = {i: {"label": GLib.Variant("s", label)} for i, label in labels.items()}
children = [GLib.Variant("(ia{sv}av)", (i, p, [])) for i, p in props.items()]
layout = (0, {"children-display": GLib.Variant("s", "submenu")}, children)

loop = GLib.MainLoop()
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
status = {}
known = {}
note = waiting
fetching = None
order = [
    "battery", "charge", "state", "link", "polling", "dpi", "dpi stage", "stage color",
    "light", "light color", "light speed", "brightness", "sleep", "deep sleep",
    "ripple", "angle snap", "motion sync", "key response",
]

window.setup(order)


def show(values, hint=None):
    global note
    status.update(values)
    note = note if hint is None else hint
    item["ToolTip"] = tooltip(f"battery: {status['battery']} {status['charge']}" if "battery" in status else "")
    window.update(status, note)
    bus.emit_signal(None, "/StatusNotifierItem", "org.kde.StatusNotifierItem", "NewToolTip", None)


def onoff(flag):
    return "on" if flag else "off"


def settings(data):
    sensor, light = data["sensor"], data["light"]
    stage = sensor["active"]
    color = f"#{sensor['colors'][stage - 1]}" if sensor["enabled"][stage - 1] else "off"
    return {
        "polling": f"{data['polling-rate']} Hz",
        "dpi": sensor["dpi"][stage - 1],
        "dpi stage": stage,
        "stage color": color,
        "light": light["mode"],
        "light color": f"#{light['color']}",
        "light speed": light["speed"],
        "brightness": light["brightness"],
        "sleep": f"{light['sleep']} min",
        "deep sleep": f"{light['deep-sleep']} min",
        "ripple": onoff(sensor["ripple"]),
        "angle snap": onoff(sensor["angle-snap"]),
        "motion sync": onoff(sensor["motion-sync"]),
        "key response": f"{light['key-response']} ms",
    }


def read(stream, result):
    line, length = stream.read_line_finish_utf8(result)
    if line is None:
        return
    values = json.loads(line)
    link = values.get("link")
    if "battery" in values:
        state = {"state": values["state"]} if values["state"] else {}
        show({"battery": f"{values['battery']}%", "charge": values["charge"], **state})
    if link == "bluetooth":
        if fetching:
            fetching.force_exit()
        show({"link": link}, "bluetooth: showing the last read values")
    elif link:
        show({"link": link}, waiting)
        update(restart=True)
    if "stage" in values and known:
        known["sensor"]["active"] = values["stage"]
        show(settings(known))
    if "light" in values and known:
        known["light"]["mode"] = values["light"]
        show(settings(known))
    stream.read_line_async(GLib.PRIORITY_DEFAULT, None, read)


def fetched(stream, result):
    line, length = stream.read_line_finish_utf8(result)
    if line and line.startswith("{"):
        known.update(json.loads(line))
        show(settings(known), "")
    elif status.get("link") != "bluetooth":
        show({}, waiting)


def finished(process, result):
    global fetching
    if process is fetching:
        fetching = None


def spawn(module, flags, *args):
    launcher = Gio.SubprocessLauncher.new(flags)
    launcher.set_cwd(here)
    launcher.unsetenv("LD_PRELOAD")
    return launcher.spawnv([sys.executable, "-m", module, *args])


def update(restart=False):
    global fetching
    if fetching and restart:
        fetching.force_exit()
    elif fetching:
        return
    flags = Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE
    fetching = spawn("core.status", flags, status["link"])
    stream = Gio.DataInputStream.new(fetching.get_stdout_pipe())
    stream.read_line_async(GLib.PRIORITY_DEFAULT, None, fetched)
    fetching.wait_async(None, finished)


def stop():
    bat.force_exit()
    if fetching:
        fetching.force_exit()
    loop.quit()


def sni_get(conn, sender, path, iface, prop):
    return item[prop]


def sni_call(conn, sender, path, iface, method, params, invocation):
    invocation.return_value(None)
    if method == "Activate":
        GLib.idle_add(window.toggle)


def menu_get(conn, sender, path, iface, prop):
    return GLib.Variant("u", 3)


def menu_call(conn, sender, path, iface, method, params, invocation):
    if method == "GetLayout":
        invocation.return_value(GLib.Variant("(u(ia{sv}av))", (1, layout)))
    elif method == "GetGroupProperties":
        out = [(i, props[i]) for i in params[0] if i in props]
        invocation.return_value(GLib.Variant("(a(ia{sv}))", (out,)))
    elif method == "AboutToShow":
        invocation.return_value(GLib.Variant("(b)", (False,)))
    else:
        invocation.return_value(None)
        if params[1] == "clicked" and params[0] == 1:
            GLib.idle_add(window.toggle)
        elif params[1] == "clicked" and params[0] == 2:
            stop()


bus.register_object("/StatusNotifierItem", sni, sni_call, sni_get, None)
bus.register_object("/Menu", menu, menu_call, menu_get, None)
bus.call_sync(
    "org.kde.StatusNotifierWatcher",
    "/StatusNotifierWatcher",
    "org.kde.StatusNotifierWatcher",
    "RegisterStatusNotifierItem",
    GLib.Variant("(s)", (bus.get_unique_name(),)),
    None,
    Gio.DBusCallFlags.NONE,
    -1,
    None,
)

bat = spawn("core.bat", Gio.SubprocessFlags.STDOUT_PIPE)
lines = Gio.DataInputStream.new(bat.get_stdout_pipe())
lines.read_line_async(GLib.PRIORITY_DEFAULT, None, read)
show({}, waiting)
loop.run()

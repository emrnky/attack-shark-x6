# attack-shark-x6

A small monitoring tool for the Attack Shark X6 mouse on Linux, written in
Python. 

## Installation

The udev rule lets you run this without root. Without it, run it with sudo.

1. Install the udev rule:

   ```
   sudo cp 99-attacksharkx6.rules /etc/udev/rules.d/
   sudo udevadm control --reload
   sudo udevadm trigger --subsystem-match=hidraw
   ```

## Disclaimer

This is an unofficial fun project. It is not affiliated with, endorsed by or
supported by Attack Shark.

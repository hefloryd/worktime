#!/usr/bin/env python

from dbus_idle import IdleMonitor
from mss import mss
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

import argparse
import time
import logging
import daemon
import os
import shutil
import sys
import subprocess
import json
import tempfile

FOLDER_FORMAT    = "%Y-%m-%d"
FOLDER_WILDCARD  = "????-??-??"
FILENAME_FORMAT  = "%Y-%m-%d-%H-%M"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
TIMESTAMP_FONT   = "FreeMono.ttf"
TIMESTAMP_COLOUR = "lime"

def get_active_region(sct):
    # Method 1: Try Sway IPC to get focused output
    try:
        result = subprocess.run(['swaymsg', '-t', 'get_outputs'],
                              capture_output=True, text=True, check=True)
        outputs = json.loads(result.stdout)

        for output in outputs:
            if output.get('focused', False):
                # Match sway output to mss monitor by geometry
                for monitor in sct.monitors[1:]:  # skip index 0
                    if (monitor['left'] == output['rect']['x'] and
                        monitor['top'] == output['rect']['y'] and
                        monitor['width'] == output['rect']['width'] and
                        monitor['height'] == output['rect']['height']):
                        logging.debug("Found focused monitor via swaymsg: {}".format(monitor))
                        return monitor
    except Exception as e:
        logging.debug("swaymsg failed: {}".format(e))

    # Method 2: Try pyautogui for X11 compatibility
    try:
        import pyautogui
        x, y = pyautogui.position()
        monitors = sct.monitors[1:] # skip index 0 containing size of all monitors

        for m in monitors:
            left = m['left']
            right = m['left'] + m['width']
            top = m['top']
            bottom = m['top'] + m['height']

            if x > left and x < right and y > top and y < bottom:
                logging.debug("Found active monitor via pyautogui: {}".format(m))
                return m

        # Did not find active region
        return sct.monitors[0]
    except Exception as e:
        logging.debug("pyautogui failed: {}".format(e))

    # Fallback: Return the first actual monitor
    fallback = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
    logging.debug("Using fallback monitor: {}".format(fallback))
    return fallback

def get_wayland_outputs():
    """Get list of Wayland outputs using swaymsg"""
    try:
        result = subprocess.run(['swaymsg', '-t', 'get_outputs'],
                              capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return []

def get_active_wayland_output():
    """Get the active/focused Wayland output name"""
    outputs = get_wayland_outputs()
    
    # Try to find focused output first
    for output in outputs:
        if output.get('focused', False):
            return output.get('name')
    
    # Fallback to first active output
    for output in outputs:
        if output.get('active', True):
            return output.get('name')
    
    return None

def take_screenshot_grim(monitor_index=None):
    """Fallback screenshot using grim for Wayland"""
    output_name = None
    
    if monitor_index is not None:
        # Get specific monitor by index
        outputs = get_wayland_outputs()
        if outputs and 0 <= monitor_index < len(outputs):
            output_name = outputs[monitor_index].get('name')
        else:
            logging.debug("Monitor index {} out of range, using active monitor".format(monitor_index))
    
    # If no specific monitor or index out of range, use active monitor
    if output_name is None:
        output_name = get_active_wayland_output()
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        try:
            cmd = ['grim']
            if output_name:
                cmd.extend(['-o', output_name])
                logging.debug("Taking screenshot of output: {}".format(output_name))
            else:
                logging.debug("Taking screenshot of all outputs")
            cmd.append(tmp.name)
            
            subprocess.run(cmd, check=True, capture_output=True)
            img = Image.open(tmp.name)
            os.unlink(tmp.name)
            return img
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise e

def trigger_screenshot(args, monitor):
    logging.debug("idle time: {}".format(monitor.get_dbus_idle()))

    if monitor.get_dbus_idle() < args.interval * 1000:
        logging.debug("triggered")
        now = datetime.now()

        img = None
        try:
            # Try mss first (X11/Windows)
            with mss() as sct:
                try:
                    # Try to grab region of requested monitor
                    region = sct.monitors[args.monitor]
                except (IndexError, TypeError):
                    # Grab region of active monitor
                    region = get_active_region(sct)

                logging.debug("region: {}".format(region))
                sct_img = sct.grab(region)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                logging.debug("Screenshot taken with mss")

        except Exception as e:
            logging.debug("mss failed: {}, trying grim fallback".format(e))
            try:
                # Fallback to grim for Wayland
                # Convert mss monitor index to grim output (subtract 1 since mss index 0 is all monitors)
                grim_monitor = args.monitor - 1 if args.monitor and args.monitor > 0 else None
                img = take_screenshot_grim(grim_monitor)
                logging.debug("Screenshot taken with grim")
            except Exception as grim_error:
                logging.error("Both mss and grim failed: mss={}, grim={}".format(e, grim_error))
                return

        if img:
            # Add timestamp to image and save
            font = ImageFont.truetype(TIMESTAMP_FONT, 40)
            draw = ImageDraw.Draw(img)
            draw.text([10, 10],
                      now.strftime(TIMESTAMP_FORMAT),
                      fill=TIMESTAMP_COLOUR,
                      font=font)
            del font, draw

            folder = Path(args.folder, now.strftime(FOLDER_FORMAT))
            filename = "{}.png".format(now.strftime(FILENAME_FORMAT))

            try:
                os.mkdir(folder)
            except FileExistsError:
                pass

            img.save(Path(folder, filename), compress_level=9)

def trim_screenshots(args):
    path = Path(args.folder)
    folders = sorted([p.name for p in list(path.glob(FOLDER_WILDCARD))])
    old = folders[:-args.keep]

    for o in old:
        shutil.rmtree(Path(args.folder, o))

def tracker(args):
    # Disable read/write permission for everyone but owner
    os.umask(0o077)
    m = IdleMonitor.get_monitor()
    while True:
        trigger_screenshot(args, m)
        trim_screenshots(args)
        time.sleep(args.interval)

def main(args):

    parser = argparse.ArgumentParser(description="Worktime tracker")

    parser.add_argument("--folder", "-f", help="screenshot folder", default=Path.home()/".screenshots")
    parser.add_argument("--monitor", "-m", help="monitor to capture", type=int)
    parser.add_argument("--daemon", action="store_true", help="run in background")
    parser.add_argument("--interval", "-i", help="interval time [seconds]", type=int, default=5*60)
    parser.add_argument("--keep", "-k", help="number of days to keep", type=int, default=21)
    parser.add_argument("--verbose", "-v", help="verbose logging", action="store_true")

    args = parser.parse_args(args)

    if args.verbose:
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG, force=True)

    if args.daemon:
        with daemon.DaemonContext(stderr=sys.stderr,stdout=sys.stdout):
            tracker(args)
    else:
        tracker(args)

def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

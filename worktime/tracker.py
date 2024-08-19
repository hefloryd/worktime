#!/usr/bin/env python

from idle_time import IdleMonitor
from mss import mss
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

import argparse
import time
import logging
import daemon
import os
import shutil
import pyautogui
import sys

FOLDER_FORMAT    = "%Y-%m-%d"
FOLDER_WILDCARD  = "????-??-??"
FILENAME_FORMAT  = "%Y-%m-%d-%H-%M"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
TIMESTAMP_FONT   = "FreeMono.ttf"
TIMESTAMP_COLOUR = "lime"

def get_active_region(sct):
    x, y = pyautogui.position()
    monitors = sct.monitors[1:] # skip index 0 containing size of all monitors

    for m in monitors:
        left = m['left']
        right = m['left'] + m['width']
        top = m['top']
        bottom = m['top'] + m['height']

        if x > left and x < right and y > top and y < bottom:
            return m

    # Did not find active region
    return sct.monitors[0]

def trigger_screenshot(args):
    m = IdleMonitor.get_monitor()
    logging.debug("idle time: {}".format(m.get_idle_time()))

    if m.get_idle_time() < args.interval:
        logging.debug("triggered")
        now = datetime.now()

        # Grab the screenshot
        with mss() as sct:
            try:
                # Try to grab region of requested monitor
                region = sct.monitors[args.monitor]
            except (IndexError, TypeError):
                # Grab region of active monitor
                region = get_active_region(sct)

            logging.debug("region: {}".format(region))
            sct_img = sct.grab(region)

            # Add timestamp to image and save
            with Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX") as img:
                font = ImageFont.truetype(TIMESTAMP_FONT, 40)
                draw = ImageDraw.Draw(img)
                draw.text([10, 10],
                          now.strftime(TIMESTAMP_FORMAT),
                          fill=TIMESTAMP_COLOUR,
                          font=font
                )
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
    while True:
        trigger_screenshot(args)
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
        logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

    if args.daemon:
        with daemon.DaemonContext(stderr=sys.stderr,stdout=sys.stdout):
            tracker(args)
    else:
        tracker(args)

def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

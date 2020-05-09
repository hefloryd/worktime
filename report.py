#!/usr/bin/env python

from datetime import datetime, timedelta
from pathlib import Path

import argparse

FOLDER_FORMAT   = "%Y-%m-%d"
FILENAME_FORMAT = "%Y-%m-%d-%H-%M"
REPORT_FORMAT   = "{:10} {:10} {:10} {:10} {}"

def report_day(args, date):
    folder = "{}/{}".format(args.folder, date.strftime(FOLDER_FORMAT))
    path = Path(folder)
    screenshots = [p.stem for p in list(path.glob('*.png'))]
    timestamps = sorted([datetime.strptime(s, FILENAME_FORMAT) for s in screenshots])

    if len(timestamps) > 0:
        arrive = timestamps[0]
        leave = timestamps[-1]
        total = leave - arrive
        lunch = args.lunch if args.lunch < total else timedelta(minutes=0)
        total -= lunch
        print(REPORT_FORMAT.format(
            date.strftime("%a"),
            arrive.strftime("%H:%M"),
            leave.strftime("%H:%M"),
            str(lunch)[0:-3],
            str(total)[0:-3],
        ))

def report_week(args):
    start = datetime.strptime("{}-{}-1".format(args.year, args.week), "%G-%V-%u")

    print(REPORT_FORMAT.format(
        "Week " + str(args.week),
        "Arrive",
        "Leave",
        "Lunch",
        "Total"
    ))

    for date in [start + timedelta(days=days) for days in range(7)]:
        report_day(args, date)

if __name__ == "__main__":

    # Default to previous week
    default_start = datetime.now() - timedelta(days=7)
    default_year = default_start.isocalendar()[0]
    default_week = default_start.isocalendar()[1]

    parser = argparse.ArgumentParser(description="Worktime report")

    parser.add_argument("--folder", "-f", help="screenshot folder", required=True)
    parser.add_argument("--year", "-y", help="report year", type=int, default=default_year)
    parser.add_argument("--week", "-w", help="report week", type=int, default=default_week)
    parser.add_argument("--lunch", "-l", help="lunch time [minutes]", type=int, default=40)

    args = parser.parse_args()
    args.lunch = timedelta(minutes=args.lunch)

    report_week(args)

#!/usr/bin/env python

import argparse
import sys
from datetime import datetime, time, timedelta
from pathlib import Path

from rich.console import Console
from rich.table import Table, box

FOLDER_FORMAT = "%Y-%m-%d"
FILENAME_FORMAT = "%Y-%m-%d-%H-%M"


def is_lunch(t1, t2):
    lunch_earliest = t1.combine(t1.date(), time(10))
    lunch_latest = t1.combine(t1.date(), time(15))

    return t1 >= lunch_earliest and t2 <= lunch_latest


def report_day(table, args, date):
    folder = "{}/{}".format(args.folder, date.strftime(FOLDER_FORMAT))
    path = Path(folder)
    screenshots = [p.stem for p in list(path.glob("*.png"))]
    timestamps = sorted([datetime.strptime(s, FILENAME_FORMAT) for s in screenshots])

    # Compute longest delta between consecutive timestamps
    longest_break = timedelta(minutes=0)
    longest_break_start = None
    longest_break_end = None
    long_breaks = []
    if len(timestamps) > 1:
        deltas = [(timestamps[i] - timestamps[i-1], timestamps[i-1], timestamps[i]) for i in range(1, len(timestamps))]
        longest_break, longest_break_start, longest_break_end = max(deltas, key=lambda x: x[0])
        
        # Collect all breaks longer than 20 minutes for -vv mode
        if args.verbose >= 2:
            long_breaks = [(delta, start, end) for delta, start, end in deltas if delta > timedelta(minutes=20)]

    if len(timestamps) > 0:
        arrive = timestamps[0]
        leave = timestamps[-1]
        total = leave - arrive
        lunch = longest_break if is_lunch(longest_break_start, longest_break_end) else args.lunch
        if lunch > total:
            lunch = timedelta(0)
        total -= lunch

        row = []
        row.append(date.strftime('%-d/%-m %a'))
        row.append(arrive.strftime('%H:%M'))
        row.append(leave.strftime('%H:%M'))
        row.append((datetime.min + lunch).strftime('%H:%M'))
        if args.verbose >= 1:
            row.append("{}-{}".format(
                longest_break_start.strftime('%H:%M'),
                longest_break_end.strftime('%H:%M')
                )
            )
        if args.verbose >= 2:
            if long_breaks:
                breaks_str = ", ".join([
                    "{}-{} ({})".format(
                        start.strftime('%H:%M'),
                        end.strftime('%H:%M'),
                        (datetime.min + delta).strftime('%H:%M')
                    )
                    for delta, start, end in long_breaks
                ])
                row.append(breaks_str)
            else:
                row.append("-")
        row.append((datetime.min + total).strftime('%H:%M'))

        table.add_row(*row)


def report_week(args):
    start = datetime.strptime("{}-{}-1".format(args.year, args.week), "%G-%V-%u")

    table = Table(title=f"Week {args.week}", box=box.SIMPLE)
    table.add_column("Day")
    table.add_column("Arrive")
    table.add_column("Leave")
    table.add_column("Lunch")
    if args.verbose >= 1:
        table.add_column("Break")
    if args.verbose >= 2:
        table.add_column("Long Breaks (>20m)")
    table.add_column("Total")

    for date in [start + timedelta(days=days) for days in range(7)]:
        report_day(table, args, date)

    console = Console()
    console.print(table)

def main(args):
    # Default to previous week
    default_start = datetime.now() - timedelta(days=7)
    default_year = default_start.isocalendar()[0]
    default_week = default_start.isocalendar()[1]

    parser = argparse.ArgumentParser(description="Worktime report")

    parser.add_argument(
        "--verbose", "-v", action="count", default=0
    )

    parser.add_argument(
        "--folder", "-f", help="screenshot folder", default=Path.home() / ".screenshots"
    )
    parser.add_argument(
        "--year", "-y", help="report year", type=int, default=default_year
    )
    parser.add_argument(
        "--week", "-w", help="report week", type=int, default=default_week
    )
    parser.add_argument(
        "--lunch", "-l", help="lunch time [minutes]", type=int, default=40
    )

    args = parser.parse_args(args)
    args.lunch = timedelta(minutes=args.lunch)

    report_week(args)


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

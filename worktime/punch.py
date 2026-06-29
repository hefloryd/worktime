#!/usr/bin/env python

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ADJUSTMENTS_FILE = "adjustments.json"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


def load_adjustments(folder):
    """Load time adjustments from JSON file"""
    adjustments_path = Path(folder) / ADJUSTMENTS_FILE
    if adjustments_path.exists():
        with open(adjustments_path, "r") as f:
            return json.load(f)
    return {}


def save_adjustments(folder, adjustments):
    """Save time adjustments to JSON file"""
    adjustments_path = Path(folder) / ADJUSTMENTS_FILE
    with open(adjustments_path, "w") as f:
        json.dump(adjustments, f, indent=2)


def punch_in(args):
    """Set the start time for a day"""
    adjustments = load_adjustments(args.folder)
    date_key = args.date.strftime(DATE_FORMAT)

    if date_key not in adjustments:
        adjustments[date_key] = {}

    adjustments[date_key]["punch_in"] = args.time.strftime(TIME_FORMAT)
    save_adjustments(args.folder, adjustments)

    print(f"Punched in for {date_key} at {args.time.strftime(TIME_FORMAT)}")


def punch_out(args):
    """Set the end time for a day"""
    adjustments = load_adjustments(args.folder)
    date_key = args.date.strftime(DATE_FORMAT)

    if date_key not in adjustments:
        adjustments[date_key] = {}

    adjustments[date_key]["punch_out"] = args.time.strftime(TIME_FORMAT)
    save_adjustments(args.folder, adjustments)

    print(f"Punched out for {date_key} at {args.time.strftime(TIME_FORMAT)}")


def punch_lunch(args):
    """Set lunch duration for a day"""
    adjustments = load_adjustments(args.folder)
    date_key = args.date.strftime(DATE_FORMAT)

    if date_key not in adjustments:
        adjustments[date_key] = {}

    # Store lunch as minutes
    adjustments[date_key]["lunch"] = args.minutes
    save_adjustments(args.folder, adjustments)

    print(f"Set lunch for {date_key} to {args.minutes} minutes")


def clear_adjustments(args):
    """Clear adjustments for a specific date"""
    adjustments = load_adjustments(args.folder)
    date_key = args.date.strftime(DATE_FORMAT)

    if date_key in adjustments:
        del adjustments[date_key]
        save_adjustments(args.folder, adjustments)
        print(f"Cleared adjustments for {date_key}")
    else:
        print(f"No adjustments found for {date_key}")


def list_adjustments(args):
    """List all time adjustments"""
    adjustments = load_adjustments(args.folder)

    if not adjustments:
        print("No time adjustments found")
        return

    print("Time adjustments:")
    for date_key in sorted(adjustments.keys()):
        adj = adjustments[date_key]
        punch_in = adj.get("punch_in", "-")
        punch_out = adj.get("punch_out", "-")
        lunch = adj.get("lunch", "-")
        if lunch != "-":
            lunch = f"{lunch}m"
        print(f"  {date_key}: in={punch_in}, out={punch_out}, lunch={lunch}")


def main(args):
    parser = argparse.ArgumentParser(
        description="Manually adjust work times",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Punch in for today at 9:00
  worktime-punch in 09:00
  
  # Punch out for today at 17:30
  worktime-punch out 17:30
  
  # Set lunch duration for today to 30 minutes
  worktime-punch lunch 30
  
  # Punch in for a specific date
  worktime-punch in 09:00 --date 2024-06-15
  
  # Set lunch for a specific date
  worktime-punch lunch 45 --date 2024-06-15
  
  # Clear adjustments for a date
  worktime-punch clear --date 2024-06-15
  
  # List all adjustments
  worktime-punch list
        """,
    )

    parser.add_argument(
        "--folder", "-f", help="screenshot folder", default=Path.home() / ".screenshots"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Punch in command
    punch_in_parser = subparsers.add_parser("in", help="Set start time for a day")
    punch_in_parser.add_argument("time", help="Time in HH:MM format")
    punch_in_parser.add_argument(
        "--date",
        "-d",
        type=lambda s: datetime.strptime(s, DATE_FORMAT),
        default=datetime.now(),
        help="Date (YYYY-MM-DD), defaults to today",
    )

    # Punch out command
    punch_out_parser = subparsers.add_parser("out", help="Set end time for a day")
    punch_out_parser.add_argument("time", help="Time in HH:MM format")
    punch_out_parser.add_argument(
        "--date",
        "-d",
        type=lambda s: datetime.strptime(s, DATE_FORMAT),
        default=datetime.now(),
        help="Date (YYYY-MM-DD), defaults to today",
    )

    # Lunch command
    lunch_parser = subparsers.add_parser("lunch", help="Set lunch duration for a day")
    lunch_parser.add_argument("minutes", type=int, help="Lunch duration in minutes")
    lunch_parser.add_argument(
        "--date",
        "-d",
        type=lambda s: datetime.strptime(s, DATE_FORMAT),
        default=datetime.now(),
        help="Date (YYYY-MM-DD), defaults to today",
    )

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear adjustments for a date")
    clear_parser.add_argument(
        "--date",
        "-d",
        type=lambda s: datetime.strptime(s, DATE_FORMAT),
        default=datetime.now(),
        help="Date (YYYY-MM-DD), defaults to today",
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all time adjustments")

    args = parser.parse_args(args)

    # Parse time for punch in/out commands
    if args.command in ["in", "out"]:
        try:
            args.time = datetime.strptime(args.time, TIME_FORMAT)
        except ValueError:
            print(f"Error: Invalid time format. Use HH:MM (e.g., 09:00)")
            sys.exit(1)

    # Execute command
    if args.command == "in":
        punch_in(args)
    elif args.command == "out":
        punch_out(args)
    elif args.command == "lunch":
        punch_lunch(args)
    elif args.command == "clear":
        clear_adjustments(args)
    elif args.command == "list":
        list_adjustments(args)


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

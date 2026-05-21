#!/usr/bin/env python

import argparse
import sys
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

try:
    import pytesseract
    from PIL import Image
except ImportError:
    print("Please install: pip install pytesseract pillow")
    sys.exit(1)

from rich.console import Console
from rich.table import Table, box

FOLDER_FORMAT = "%Y-%m-%d"
FILENAME_FORMAT = "%Y-%m-%d-%H-%M"


class ProjectMatcher:
    """Match OCR text to project identifiers"""

    def __init__(self, config_file=None):
        self.patterns = []
        if config_file and Path(config_file).exists():
            self.load_config(config_file)
        else:
            # Default patterns
            self.patterns = [
                # Ticket numbers: PROJ-123, JIRA-456
                (r"\b([A-Z]{2,10}-\d+)\b", "ticket"),
                # Git repos in paths: /path/to/project-name/
                (r"/([a-z0-9_-]+)/(?:src|lib|tests?|docs?|bin)", "repo"),
                # Emacs buffers: filename.ext
                (
                    r"([a-z0-9_-]+\.(py|js|go|rs|c|cpp|java|rb|sh|md|txt|json|yaml|yml))",
                    "file",
                ),
                # Directory paths in bash prompts: ~/project-name or /path/to/project
                (r"[~\/]([a-z0-9_-]+(?:/[a-z0-9_-]+)*)\s*[$#>]", "directory"),
            ]

    def load_config(self, config_file):
        """Load project patterns from JSON config"""
        with open(config_file, "r") as f:
            config = json.load(f)
            self.patterns = [
                (p["pattern"], p["type"]) for p in config.get("patterns", [])
            ]

    def extract_projects(self, text):
        """Extract project identifiers from OCR text"""
        projects = []

        for pattern, ptype in self.patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                project_name = match.group(1)
                projects.append((project_name, ptype))

        return projects

    def normalize_project(self, project_name, ptype):
        """Normalize project names for grouping"""
        # Remove common prefixes/suffixes
        normalized = project_name.lower()

        # For files, extract just the base name without extension
        if ptype == "file":
            normalized = Path(normalized).stem

        # For directories, take the last component
        if ptype == "directory":
            parts = normalized.split("/")
            normalized = parts[-1] if parts else normalized

        return normalized


def analyze_screenshot(image_path, matcher):
    """Run OCR on a screenshot and extract project information"""
    try:
        print(image_path)
        img = Image.open(image_path)

        # OCR the image
        text = pytesseract.image_to_string(img)
        print(text)

        # Extract projects
        projects = matcher.extract_projects(text)

        return projects
    except Exception as e:
        print(f"Error analyzing {image_path}: {e}", file=sys.stderr)
        return []


def analyze_day(args, matcher, date):
    """Analyze all screenshots for a given day"""
    folder = Path(args.folder) / date.strftime(FOLDER_FORMAT)

    if not folder.exists():
        return {}

    screenshots = sorted(list(folder.glob("*.png")))
    project_time = defaultdict(int)

    for screenshot in screenshots:
        timestamp = datetime.strptime(screenshot.stem, FILENAME_FORMAT)
        projects = analyze_screenshot(screenshot, matcher)

        if projects:
            # Use the first/most prominent project found
            project_name, ptype = projects[0]
            normalized = matcher.normalize_project(project_name, ptype)
            project_time[normalized] += args.interval
        else:
            # No project identified
            project_time["[unknown]"] += args.interval

    return project_time


def format_minutes(minutes):
    """Format minutes as HH:MM"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def generate_report(args, matcher, date):
    """Generate a Rich table report of time per project for a single day"""
    project_time = analyze_day(args, matcher, date)

    # Sort projects by time spent (descending)
    sorted_projects = sorted(project_time.items(), key=lambda x: x[1], reverse=True)

    table = Table(
        title=f"Project Time Analysis - {date.strftime('%Y-%m-%d %A')}", box=box.SIMPLE
    )
    table.add_column("Project", style="cyan")
    table.add_column("Time", justify="right", style="green")
    table.add_column("Percentage", justify="right")

    total_minutes = sum(project_time.values())

    for project, minutes in sorted_projects:
        percentage = (minutes / total_minutes * 100) if total_minutes > 0 else 0
        table.add_row(project, format_minutes(minutes), f"{percentage:.1f}%")

    # Add total row
    table.add_section()
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{format_minutes(total_minutes)}[/bold]",
        "[bold]100.0%[/bold]",
    )

    console = Console()
    console.print(table)

    # Optionally show detailed breakdown
    if args.verbose:
        console.print(
            f"\n[bold]Screenshots analyzed:[/bold] {len(project_time)} intervals"
        )


def main(args):
    # Default to yesterday
    default_day = datetime.now() - timedelta(days=1)

    parser = argparse.ArgumentParser(
        description="Analyze screenshots for project billing"
    )

    parser.add_argument(
        "--folder", "-f", help="screenshot folder", default=Path.home() / ".screenshots"
    )
    parser.add_argument(
        "--day",
        "-d",
        help="day to analyze (YYYY-MM-DD)",
        type=str,
        default=default_day.strftime("%Y-%m-%d"),
    )
    parser.add_argument(
        "--interval", "-i", help="interval time [minutes]", type=int, default=5
    )
    parser.add_argument("--config", "-c", help="project patterns config file (JSON)")
    parser.add_argument(
        "--verbose", "-v", help="show detailed information", action="store_true"
    )

    args = parser.parse_args(args)

    # Parse the day
    day = datetime.strptime(args.day, "%Y-%m-%d")

    matcher = ProjectMatcher(args.config)
    generate_report(args, matcher, day)


def run():
    main(sys.argv[1:])


if __name__ == "__main__":
    run()

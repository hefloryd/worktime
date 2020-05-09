# Worktime

Track time using screenshots. This utility takes a screenshot of your
monitors at a configurable interval. The screenshot is only taken if
you were not idle during the interval. When you need to fill out a
timesheet, use the screenshots to figure out what you were working
on. Also included is a report utility that uses the timestamps of the
screenshots to produce a weekly time report.

## Installation

This utility has only been tested on Ubuntu Linux.

Install the requirements using pip or similar (pipenv or virtualenv):

    $ pip install -r requirements.txt

## Usage

Start the worktime tracker in the background:

    $ ./worktime.py --daemon -f /path/to/screenshots

By default, a screenshot will be taken every 5 minutes and stored in
the folder you specified. Note that this may produce a lot of
data. Screenshots older than 21 days will be deleted.

Generate a weekly report:

    $ ./report.py -f /path/to/screenshots

By default, times of the previous week are reported:

    Week 18    Arrive     Leave      Lunch      Total
    Mon        08:32      18:52      0:40       9:40
    Tue        08:02      15:47      0:40       7:05
    Wed        10:07      17:12      0:40       6:25
    Thu        08:42      17:57      0:40       8:35
    Fri        09:42      17:37      0:40       7:15

## Security

The screenshots may contain sensitive information such as
passwords. The default umask is set so that screenshots are only
readable by the owner. Use at your own risk.

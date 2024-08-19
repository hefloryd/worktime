# Worktime

**Worktime** is a time-tracking utility that helps you monitor your
work activities by capturing screenshots at configurable
intervals. The tool only takes screenshots when you're active,
ensuring that your time tracking is accurate and efficient. These
screenshots can be useful when filling out timesheets, as they provide
a visual record of your tasks. Additionally, Worktime includes a
reporting utility that generates a weekly time report based on the
timestamps of the screenshots.

## Features

- **Automated Time Tracking**: Captures screenshots at set intervals
  when activity is detected.
- **Weekly Reports**: Generates time reports based on captured
  screenshots, helping you review your weekly work hours.
- **Configurable**: Customize screenshot intervals and storage
  locations.
- **Automatic Cleanup**: Older screenshots are automatically deleted
  to conserve storage.

## Installation

Worktime has been tested on Ubuntu Linux.

### Using `pipx` (Recommended)

To install Worktime, it is recommended to use `pipx`. If `pipx` is not
already installed, you can follow the [installation
instructions](https://pipx.pypa.io/stable/).

Once `pipx` is set up, install Worktime by running:

    pipx install /path/to/worktime

## Usage

### Starting the Worktime Tracker

To start the Worktime tracker as a background process, run:

    worktime --daemon -f /path/to/screenshots

By default, a screenshot is captured every 5 minutes and saved in the
specified folder. Please note that the tracker can generate a
substantial amount of data. Screenshots older than 21 days are
automatically deleted to conserve storage.

### Generating a Weekly Report

To generate a report of your work hours for the previous week, run:

    report -f /path/to/screenshots

The report provides a summary similar to the following:

    Week 27    Arrive     Leave      Lunch      Total
    Mon        09:16      17:48      0:40       7:52
    Tue        08:30      17:20      0:40       8:10
    Wed        09:00      17:52      0:40       8:12
    Thu        09:02      17:57      0:40       8:15
    Fri        09:42      17:37      0:40       7:15


## Installing as a systemd Service

To run Worktime as a `systemd` service, follow these steps:

1. Create a systemd unit file at
   `~/.config/systemd/user/worktime.service` with the following
   content:

    ```
    [Unit]
    Description=Worktime service

    [Service]
    ExecStart=%h/.local/bin/worktime -f %h/.screenshots
    Restart=on-failure
    Environment=PYTHONUNBUFFERED=1

    [Install]
    WantedBy=default.target
    ```

2. Install and start the service by running:

    ```
    systemctl --user start worktime.service
    systemctl --user enable worktime.service
    ```

## Security Considerations

Please be aware that the screenshots may contain sensitive
information, such as passwords. By default, the umask is configured so
that screenshots are only accessible by the owner. Exercise caution
and use Worktime at your own risk.

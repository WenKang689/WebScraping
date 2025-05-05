# 📈 SGX Derivatives Data Downloader
This Python-based automation tool retrieves daily derivatives data from the Singapore Exchange (SGX). It supports full automation, retry scheduling, and interactive retry handling to ensure high data reliability.

# 🚀 Features
Automated daily downloads using the schedule module (time configurable via config.ini)

Supports historical and date-range downloads via CLI

Retry logic for failed downloads with cooldown intervals and a separate retry handler

Logging system to track successful/failed downloads and recovery attempts

Interactive retry mode for manual download recovery

Cross-platform automation support: Works with cron (Linux) and Task Scheduler (Windows)

# 🛠 Technical Stack
Python (3.7+)

Libraries: requests, argparse, configparser, schedule, logging, datetime, os, sys

Automation: Supports integration with cron jobs and Windows Task Scheduler

Configuration-driven: All paths and schedule settings controlled via config.ini

# 📂 Sample Use Cases
## Setup
1. Unzip the file.
2. Open command line and navigate to the extracted folder.
3. Ensure Python is installed, and run the following command:

```
pip install -r requirements.txt
```

## Manual Execution

1. This command will download the files for the specific date.

```
python SGX_Main.py --date 2025-03-05
```

2. This command will download the files for the date range.

```
python SGX_Main.py --start 2025-03-01 --end 2025-03-05
```

3. Since this command only specific the start date, it will automatically set today's date as the end date and download files from the start date to today's date.

```
python SGX_Main.py --start 2025-03-01
```

4. This command will only download the specific file stated in the argument. "--file" can be combined with the command above to download specific files within a date range.

```
python SGX_Main.py --file TC.txt WEBPXTICK_DT.zip
```

5. This command will download today's file when no arguments is provided.

```
python SGX_Main.py
```

## Automation Execution

1. Run the script daily on a scheduled time based on the configuration file.

```
python SGX_Main.py --schedule
```

2. This will run the script daily at the specified time.

```
python SGX_Main.py --schedule 12:16
```

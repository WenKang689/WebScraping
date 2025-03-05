import argparse
import configparser
import os
import logging
import requests
from datetime import datetime, timedelta
import time
import sys

#Load configurations in config.ini
config_file = "config.ini"
config = configparser.ConfigParser()
config.read(config_file)

#Read settings from config.ini
dir = config.get("Settings", "download_directory", fallback = "./downloads")
link = config.get("Settings","SGX_URL",fallback="https://links.sgx.com/1.0.0/derivatives-historical/")
log_file = config.get("Settings", "log_file", fallback = "download.log")
retry_cooldown = config.getint("Settings", "retry_cooldown", fallback = 3)
max_retry = config.getint("Settings", "max_retries", fallback=3)
base_date = datetime.strptime(config.get("Settings", "base_date", fallback = "2021-01-01"),"%Y-%m-%d")
base_index = int(config.get("Settings","base_index",fallback = "4803"))
files = ["WEBPXTICK_DT.zip","TickData_structure.dat","TC.txt","TC_structure.dat"]
failed_download_log = "Failed_Download.log"

#Ensure the folder is created
os.makedirs(dir, exist_ok=True)
open(failed_download_log, 'a').close()

#Configure logging
logging.basicConfig(
    filename = log_file,
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",)

#Display log message in console
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logging.getLogger().addHandler(handler)

def get_date_range(arg):
    # Validate and calculate date range for download
    dates = []
    today = datetime.today()

    if arg.date and (arg.start or arg.end):
        logging.error("Cannot use --date with --start or --end. You must specify one of: --date, --start, or --start with --end.")
        sys.exit(1)

    if arg.start and arg.end:
        start_date = validate_date(arg.start)
        end_date = validate_date(arg.end)
        if start_date > end_date:
            logging.error("--start date cannot be later than --end date.")
            sys.exit(1)
        for i in range((end_date - start_date).days + 1):
            dates.append(start_date + timedelta(days=i))
    elif arg.start:
        start_date = validate_date(arg.start)
        for i in range((today - start_date).days + 1):
            dates.append(start_date + timedelta(days=i))
    elif arg.date:
        dates.append(validate_date(arg.date))
    else:
        dates.append(validate_date(str(today.date())))  # Extract only the date part


    return dates

# Validate date format
def validate_date(date):
    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        logging.error(f"Invalid date format: {date}. Must follow YYYY-MM-DD.")
        sys.exit(1)

#Validate file name
def validate_file(arg):
    invalid = []
    if arg.file:
        for i in arg.file:
            if i not in files:
                invalid.append(i)
        if invalid:
            logging.error(f"Invalid file(s): {', '.join(invalid)}. Available files: {', '.join(files)}")
            sys.exit(1)
        return arg.file
    return files

#Calculate the corresponding index
def index_calc(dates):
    date_now = base_date
    index_now = base_index

    index_list = []
    for date in dates:
        if date < base_date:
            logging.info(f"{date.strftime('%Y-%m-%d')} is before base date {base_date.strftime('%Y-%m-%d')}.")
            continue

        if date.date() > datetime.today().date():
            logging.info(f"{date.strftime('%Y-%m-%d')} is after today's date {datetime.today().strftime('%Y-%m-%d')}.")
            continue

        if date.weekday() >= 5:  # Saturday (5) or Sunday (6)
            logging.info(f"No data available for weekends: {date.strftime('%Y-%m-%d')}.")
            continue
        
        while date_now < date:
            if date_now.weekday() < 5:
                index_now += 1
            date_now += timedelta(days = 1)
        index_list.append(index_now)

    return(index_list)

#Download data
def dwl_data(indices,file_name):
    failed_dwl = []

    for index in indices:
        for file in file_name:
            logging.info(f"Initializing download for file {file} (Index: {index})")
            base_url = f"{link}{index}/{file}"
            path = get_save_path(index)
            save_path = os.path.join(path,file)

            if os.path.exists(save_path):
                logging.info(f"File {file} (Index: {index}) already exists.")
                continue

            try:
                response = requests.get(base_url)
                if response.status_code == 200:
                    with open(save_path,"wb") as w:
                        w.write(response.content)
                    logging.info(f"Downloaded: {os.path.basename(file)} (Index: {index})")
                else:
                    failed_dwl.append((index,file,1))
                    logging.warning(f"Failed downloading for {os.path.basename(file)} (Index: {index}). HTTP {response.status_code}")
            except requests.RequestException as e:
                failed_dwl.append((index,file,1))
                logging.error(f"Error downloading {file} for index {index}: {e}")
    
    if failed_dwl:
        dwl_retry(failed_dwl)

# Create folder and get save path for each index
def get_save_path(index):
    index_folder = os.path.join(dir,str(index))
    os.makedirs(index_folder, exist_ok=True)
    return index_folder

def dwl_retry(failed_dwl):
    logging.info(f"Retrying failed download(s)")
    while failed_dwl:
        logging.info(f"Waiting {retry_cooldown} hours before retrying failed downloads.")
        time.sleep(retry_cooldown * 3600)

        buffer_queue = []

        for index,file,attempt in failed_dwl:
            if attempt > max_retry:
                logging.error(f"Max retry attempts reached for {file} (Index {index})")
                with open(failed_download_log,"a") as fail_log:
                    fail_log.write(f"{datetime.now()} - Failed Download for {attempt} attempt: {file} (Index: {index})\n")
                continue

            logging.info(f"Retrying download attempt {attempt} for {file} (Index: {index})")
            base_url = f"{link}{index}/{file}"
            path = get_save_path(index)
            save_path = os.path.join(path,file)

            try:
                response = requests.get(base_url)
                if response.status_code == 200:
                    with open(save_path, "wb") as w:
                        w.write(response.content)
                    logging.info(f"Download retry successful: {os.path.basename(file)} (Index: {index})")
                else:
                    buffer_queue.append((index,file,attempt+1))
                    logging.warning(f"Download retry failed for {os.path.basename(file)} (Index: {index}). HTTP {response.status_code}")
            except requests.RequestException as e:
                buffer_queue.append((index,file,attempt+1))
                logging.error(f"Download retry error: {file} for index {index}: {e}")
                
        failed_dwl = buffer_queue

#---Main---

#Parsing argument for manual intervention
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--date", type=str)
arg_parser.add_argument("--start", type=str)
arg_parser.add_argument("--end", type=str)
arg_parser.add_argument("--file", nargs="+")

arg = arg_parser.parse_args()

dates = get_date_range(arg)
file = validate_file(arg)
indices = index_calc(dates)
dwl_data(indices,file)
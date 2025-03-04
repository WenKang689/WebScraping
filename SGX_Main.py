import argparse
import configparser
import os
import logging
import requests
from datetime import datetime, timedelta
import time

#Load configurations in config.ini
config_file = "config.ini"
config = configparser.ConfigParser()
config.read(config_file)

#Read settings from config.ini
dir = config.get("Settings", "download_directory", fallback = "./downloads")
retry_duration = config.getint("Settings", "retry_duration", fallback = 3)
log_file = config.get("Settings", "log_file", fallback = "download.log")

#Ensure the folder is created
os.makedirs(dir, exist_ok=True)

#Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",)

#Display log message in console
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logging.getLogger().addHandler(handler)

# Create folder and get save path for each index
def get_save_path(index):
    index_folder = os.path.join(dir,str(index))
    os.makedirs(index_folder, exist_ok=True)
    return index_folder

#Calculate the corresponding index
def index_calc(dates):
    base_date = datetime.strptime(config.get("Settings", "base_date", fallback = "2021-01-01"),"%Y-%m-%d")
    base_index = int(config.get("Settings","base_index",fallback = "4803"))

    date_now = base_date
    index_now = base_index

    index_list = []
    for date in dates:
        if date < base_date:
            index_list.append(None)
            print(f"Warning: {date.strftime('%Y-%m-%d')} is before base date ({base_date.strftime('%Y-%m-%d')}).")
            continue
        
        while date_now < date:
            if date_now.weekday() < 5:
                index_now += 1
            date_now += timedelta(days = 1)
        index_list.append(index_now)
    if len(dates) == 1:
        return(index_list[0])
    return(index_list)

#Download data
def dwl_data(indices):
    file_name = ["WEBPXTICK_DT.zip","TickData_structure.dat","TC.txt","TC_structure.dat"]
    link = config.get("Settings","SGX_URL",fallback="https://links.sgx.com/1.0.0/derivatives-historical/")

    for index in indices:
        for file in file_name:
            base_url = f"{link}{index}/{file}"
            path = get_save_path(index)
            save_path = os.path.join(path,file)

            if os.path.exists(save_path):
                continue

            try:
                response = requests.get(base_url)
                if response.status_code == 200:
                    with open(save_path,"wb") as w:
                        w.write(response.content)
                    logging.info(f"Downloaded: {os.path.basename(file)} (Index: {index})")
                else:
                    dwl_retry(index,file)
                    logging.warning(f"Download failed for {os.path.basename(file)} (Index: {index}). HTTP {response.status_code}")
            except requests.RequestException as e:
                dwl_retry(index,file)
                logging.error(f"Error downloading {file} for index {index}: {e}")

def dwl_retry(index,file):
    link = config.get("Settings","SGX_URL",fallback="https://links.sgx.com/1.0.0/derivatives-historical/")
    logging.info(f"Retrying failed downloads after {retry_duration} hours...")
    time.sleep(retry_duration * 3600)    

    for index, file in fail_dwl:
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
                logging.warning(f"Download retry failed for {os.path.basename(file)} (Index: {index}). HTTP {response.status_code}")
        except requests.RequestException as e:
            logging.error(f"Download retry error: {file} for index {index}: {e}")

#---Main---

#Parsing argument for manual intervention
argparse.ArgumentParser.add_argument("--date", type=str)
argparse.ArgumentParser.add_argument("--start", type=str)
argparse.ArgumentParser.add_argument("--end", type=str)
argparse.ArgumentParser.add_argument("--retry", action="store_true")
arg = argparse.ArgumentParser.parse_args()

# Calculate date range for download
dates = []
if arg.retry:
    dwl_retry(index,file)
    exit(0)

if arg.date:
    dates.append(datetime.strptime(arg.date, "%Y-%m-%d"))
elif arg.start and arg.end:
    start_date = datetime.strptime(arg.start, "%Y-%m-%d")
    end_date = datetime.strptime(arg.end, "%Y-%m-%d")
    for i in range((end_date - start_date).days + 1):
        dates = [start_date + timedelta(days=i)]
elif arg.start:
    start_date = datetime.strptime(arg.start, "%Y-%m-%d")
    for i in range((datetime.today() - start_date).days + 1):
        dates = [start_date + timedelta(days=i)]
else:
    dates.append(datetime.today())

indices = index_calc(dates)
dwl_data(indices)
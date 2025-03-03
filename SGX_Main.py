import argparse
import configparser
import os
import logging
import requests
from datetime import datetime, timedelta

#Load configurations in config.ini
config_file = "config.ini"
config = configparser.ConfigParser()
config.read(config_file)

#Read settings from config.ini
dir = config.get("Settings", "download_directory", fallback = "./downloads")
retry_duration = config.getint("Settings", "retry_duration", fallback = 3)
log_file = config.get("Settings", "log_file", fallback = "download.log")

#Name different folders for each data type
folder_directory = {
    "WEBPXTICK_DT": os.path.join(dir, "WEBPXTICK_DT"),
    "TickData_structure": os.path.join(dir, "TickData_structure"),
    "TC": os.path.join(dir, "TC"),
    "TC_structure": os.path.join(dir, "TC_structure"),
}

#Create new folders if folder not exists
for folder in folder_directory.values():
    os.makedirs(folder, exist_ok=True)

#Configure logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

#Display log message in console
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logging.getLogger().addHandler(handler)

# Get save path for each file type
def get_save_path(file_name):
    if file_name.startswith("WEBPXTICK_DT") and file_name.endswith(".zip"):
        return os.path.join(folder_directory["WEBPXTICK_DT"], file_name)
    elif file_name == "TickData_structure.dat":
        return os.path.join(folder_directory["TickData_structure"], file_name)
    elif file_name.startswith("TC_") and file_name.endswith(".txt"):
        return os.path.join(folder_directory["TC"], file_name)
    elif file_name == "TC_structure.dat":
        return os.path.join(folder_directory["TC_structure"], file_name)
    return os.path.join(dir, file_name)

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

def dwl_data():
    link = config.get("Settings","SGX_URL",fallback="https://www.sgx.com/research-education/derivatives")

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
    retry_download()
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
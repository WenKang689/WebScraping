import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--disable-popup-blocking")  # Ensure popups are not blocked
chrome_options.add_argument("--auto-open-devtools-for-tabs")  # Enable DevTools to capture network logs
chrome_options.add_experimental_option("w3c", False)  # Ensure old DevTools works

# Automatically install and manage ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open SGX website
driver.get("https://www.sgx.com/research-education/derivatives")
print("🌍 Page loaded successfully!")

# Wait for the Download button and click it
try:
    wait = WebDriverWait(driver, 10)
    button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "sgx-button--primary")))
    button.click()
    print("📥 Download button clicked.")
except Exception as e:
    print(f"❌ Download button not found or not clickable: {e}")
    driver.quit()
    exit()

# Wait briefly to capture the request
time.sleep(5)

# Extract network logs to find the download URL
logs = driver.get_log("performance")  # Get all performance logs
download_url = None

for entry in logs:
    message = entry.get("message", "")
    if "sgx.com/1.0.0/derivatives-historical" in message:
        download_url = message.split('"url":"')[1].split('"')[0]
        print(f"🔗 Captured Download URL: {download_url}")
        break

# If we captured a download URL, download the file
if download_url:
    file_name = os.path.basename(download_url)
    save_path = os.path.join(os.getcwd(), file_name)

    response = requests.get(download_url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"✅ File downloaded successfully: {save_path}")
    else:
        print(f"❌ Failed to download file. HTTP Status Code: {response.status_code}")
else:
    print("❌ No download URL captured.")

# Close driver when done
driver.quit()

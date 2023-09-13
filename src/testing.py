import os
import utils
import sys

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    cred_path = os.path.join("..", "credentials.txt")
    creds = utils.load_credentials(cred_path)
    tmp_dir = os.path.join("..", "tmp")
    records_dir = os.path.join("..", "records")

    n_attempts = 5

    pages = ["mintos", "estateguru"]
    attempts = {p: {
        "attempts": n_attempts,
        "successful": False
    } for p in pages}

    while True:
        tot_n_attempts = 0
        for p in pages:
            if attempts[p]["successful"] or attempts[p]["attempts"] == 0: continue
            try:
                soup = utils.get_soup(p, creds[p])
                utils.save_soup(soup, p, tmp_dir)
                json_data = utils.parse_soup(p, soup)
                utils.write_data_to_csv(json_data, p, records_dir)
                attempts[p]["successful"] = True
                attempts[p]["attempts"] = 0
            except Exception as e:
                attempts[p]["attempts"] -= 1
                print(f"WARNING: Attempt {n_attempts - attempts[p]['attempts']} of updating {p} data not successful")
                print(f"EXCEPTION: {e}")
                if attempts[p]["attempts"] == 0:
                    print(f"ERROR: {p} run out of attempts. Could not upload data")
            tot_n_attempts += attempts[p]["attempts"]
        if tot_n_attempts == 0:
            break
    for p in pages:
        if attempts[p]["successful"]: print(f"SUMMARY: {p} data was successfully updated")
        else: print(f"SUMMARY: Could not update {p} data")
    print(f"SUMMARY: {sum([attempts[p]['successful'] for p in pages])}/{len(pages)} successful updates")

    pass


def test():
    cred_path = os.path.join("..", "credentials.txt")
    creds = utils.load_credentials(cred_path)
    tmp_dir = os.path.join("..", "tmp")
    records_dir = os.path.join("..", "records")

    creds = creds["peerberry"]

    soup = utils.peerberry_get_soup(creds["email"],creds["password"])
    # utils.save_soup(soup, "peerberry",tmp_dir)

def clean_text(text):
    ctext = "_".join(text.lower().split(" "))
    weird = ["á","é","í","ó","ú"]
    clean = ["a","e","i","o","u"]
    for i in range(len(weird)):
        ctext=ctext.replace(weird[i],clean[i])
    return ctext


def peerberry_get_soup(email, password):
    # Configure Firefox options
    options = Options()
    options.headless = False # Run Firefox in headless mode (without GUI)

    # Set path to geckodriver executable
    geckodriver_path = "./geckodriver.exe"  # Replace with the actual path to geckodriver

    # Create a new Firefox browser instance
    browser = webdriver.Firefox(options=options, executable_path=geckodriver_path)

    # Navigate to the login page
    url = "https://peerberry.com/es/client/"
    browser.get(url)
    print(f"INFO: Opened {url}")

    # Find the email and password fields, and submit button
    email_field = WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']")))
    password_field = WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']")))
    submit_button = WebDriverWait(browser, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[class^='MuiButton'][type='submit']")))

    # Enter the email and password, and submit the login form
    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()
    print(f"INFO: Tried to log in to {url}")

    # Wait for the account page to load
    url = "https://peerberry.com/es/client/overview"
    WebDriverWait(browser, 30).until(EC.url_to_be(url))
    print(f"INFO: Loading {url}...")
    time.sleep(9)
    html = browser.page_source
    browser.quit()
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.prettify()
    print(f"INFO: Obtained soup from {url} and closed browser")

    return soup


if __name__ == "__main__":
    cred_path = os.path.join("..", "credentials.txt")
    creds = utils.load_credentials(cred_path)
    tmp_dir = os.path.join("..", "tmp")
    records_dir = os.path.join("..", "records")

    p = "peerberry"
    creds = creds["peerberry"]

    soup = peerberry_get_soup(creds["email"], creds["password"])

    # soup = utils.load_soup(r"C:\Users\Fernando_Celaya\Documents\optimfin\tmp\peerberry\peerberry_20230601215928.txt")
    # json_data = utils.parse_soup(p,soup)

    # utils.write_data_to_csv(json_data, p, records_dir)
    pass

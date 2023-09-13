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

    pages = ["mintos", "estateguru", "peerberry"]
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
                if soup is not None:
                    utils.save_soup(soup, p, tmp_dir)
                    json_data = utils.parse_soup(p, soup)
                    utils.write_data_to_csv(json_data, p, records_dir)
                    attempts[p]["successful"] = True
                    attempts[p]["attempts"] = 0
                else:
                    raise RuntimeError(f"Returned empty {p} soup")
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

if __name__ == "__main__":
    dir_path = os.path.join("..", "logs")
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
        print(f"INFO: Created folder {dir_path}")
    log_path = os.path.join(dir_path, "log_" + utils.get_current_timestamp() + ".txt")
    sys.stdout = utils.Logger(log_path)

    # CODE HERE

    main()

    # CODE HERE

    sys.stdout.quit()

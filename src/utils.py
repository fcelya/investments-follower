import os.path
import csv
import sys

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from treelib import Tree

def clean_text(text):
    ctext = "_".join(text.lower().split(" "))
    weird = ["á","é","í","ó","ú"]
    clean = ["a","e","i","o","u"]
    for i in range(len(weird)):
        ctext=ctext.replace(weird[i],clean[i])
    return ctext

def load_credentials(fpath):
    creds = {}

    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            try:
                page, cred, s = line.split(" ")
                if page not in creds.keys(): creds[page] = {}
                creds[page][cred] = s
                print(f"INFO: Loaded {cred} for {page}")
            except:
                print(f"WARNING: Could not extract credentials from {f}")
    return creds

def parse_soup(page, html_string):
    s = 0
    pairs = {}
    match page:
        case "mintos":
            try:
                pairs = mintos_parse_soup(html_string)
            except Exception as e:
                print(f"ERROR: Could not parse {page} soup")
                print(f"EXCEPTION: {e}")
                s = 1
        case "estateguru":
            try:
                pairs = estateguru_parse_soup(html_string)
            except Exception as e:
                print(f"ERROR: Could not parse {page} soup")
                print(f"EXCEPTION: {e}")
                s = 1
        case "peerberry":
            try:
                pairs = peerberry_parse_soup(html_string)
            except Exception as e:
                print(f"ERROR: Could not parse {page} soup")
                print(f"EXCEPTION: {e}")
                s = 1
        case _:
            print(f"ERROR: {page} is not an option for parsing")
            s = 1

    return pairs

def get_soup(page, cred_dict):
    s = 0
    soup = None
    match page:
        case "mintos":
            try:
                soup = mintos_get_soup(cred_dict["email"],cred_dict["password"])
            except Exception as e:
                print(f"ERROR: Could not get {page} soup")
                print(f"EXCEPTION: {e}")
                s = 1
        case "estateguru":
            try:
                soup = estateguru_get_soup(cred_dict["email"],cred_dict["password"])
            except Exception as e:
                print(f"ERROR: Could not get {page} soup")
                print(f"EXCEPTION: {e}")
                s = 1
        case "peerberry":
            try:
                soup = peerberry_get_soup(cred_dict["email"],cred_dict["password"])
            except Exception as e:
                print(f"ERROR: Could not get {page} soup")
                print(f"EXCEPTION: {e}")
                s = 1
        case _:
            print(f"ERROR: {page} is not an option for scrapping")
            s = 1

    return soup

def mintos_parse_soup(html_string):
    amounts = []
    names = []
    pairs = {}

    soup = BeautifulSoup(html_string, 'html.parser')

    # Extract available funds, invested funds, pending payments, and overdue amounts
    div_elements = soup.find_all('div', class_='mw-overview-card__aggregate')
    for div in div_elements:
        span_elements = div.find_all('span', title='EUR')
        if span_elements:
            n = div.find('span', class_='m-u-d-flex m-u-ai-center')
            name = n.get_text(strip=True)
            if len(name) > 20:
                children = n.findChildren("span")
                name = children[0].get_text(strip=True)
            amount = span_elements[-1].next_sibling.strip()
            if " " in amount:
                amount = "".join(amount.split(" "))
            amount = float(amount)
            amounts.append(amount)
            names.append(name)

    # Extract total amount
    total_element = soup.find('p', class_='mw-overview-card__aggregate--total')
    if total_element:
        name = total_element.find('span').get_text(strip=True)
        amount = total_element.find('span', title='EUR').next_sibling.strip()
        if " " in amount:
            amount = "".join(amount.split(" "))
        amount = float(amount)
        names.append(name)
        amounts.append(amount)
    names[3] = "Overdue"
    names[7] = "Secondary Market Transaction"
    names[8] = "Service Fees"
    names[9] = "Withholding Tax"

    names_aux = names
    names = []
    for n in names_aux:
        names.append("_".join(n.split(" ")).lower())

    pairs = {names[i]: amounts[i] for i in range(len(names))}
    print(f"INFO: Parsed soup for mintos")
    return pairs

def estateguru_parse_soup(html_string):
    soup = BeautifulSoup(html_string, "html.parser")
    sections = soup.find_all('div', class_="detail-item-header")

    pairs = {}
    pre_strings = ["outstanding_portfolio_", "historic_portfolio_", "annual_return_", "account_balance_"]
    pre_number = [9, 1, 13, 9999]
    psidx = 0
    idx = 1

    for s in sections:
        fideo = Fideo(s)
        fideo.create_tree_names()
        names = fideo.nodes
        for n in names:
            if 'txt' not in n:
                continue
            if '€' in n:
                aux = n.split("txt")
                aux = aux[-1][1:-1]
                aux = aux.replace("€", "")
                aux = aux.replace(" ", "")
                val = float(aux)
            else:
                aux = n.split("txt")
                aux = aux[-1][1:-1].lower().replace(" ", "_")
                it = pre_strings[psidx] + aux
                idx += 1
                if idx >= pre_number[psidx]:
                    idx = 1
                    psidx += 1
        pairs[it] = val
    print(f"INFO: Parsed soup for estateguru")
    return pairs

def peerberry_parse_soup(html_string):
    pairs = {}

    soup = BeautifulSoup(html_string, 'html.parser')

    # Extract available funds, invested funds, pending payments, and overdue amounts
    sections = soup.find_all('div', class_="MuiGrid-root MuiGrid-container MuiGrid-justify-xs-space-between")
    for s in sections:
        children = s.findChildren("div", recursive=False)
        for c in children:
            text = c.get_text(strip=True)
            if "€" in text:
                val = float(text[2:])
            elif text == "-":
                val = 0.0
            else:
                name = clean_text(text)
        pairs[name] = val
    sections = soup.find_all('div', class_="H-r2F7fopaM1LRgfpzMhSg==")
    for s in sections:
        children = s.findChildren("div", recursive=False)
        for c in children:
            text = c.get_text(strip=True)
            if "€" in text:
                val = float(text[2:])
            elif text == "-":
                val = 0.0
            else:
                name = clean_text(text)
        pairs[name] = val
    return pairs

def mintos_get_soup(email, password):
    # Configure Firefox options
    options = Options()
    options.headless = False # Run Firefox in headless mode (without GUI)

    # Set path to geckodriver executable
    geckodriver_path = "./geckodriver.exe"  # Replace with the actual path to geckodriver

    # Create a new Firefox browser instance
    browser = webdriver.Firefox(options=options, executable_path=geckodriver_path)

    # Navigate to the login page
    url = "https://www.mintos.com/en/login/"
    browser.get(url)
    print(f"INFO: Opened {url}")

    # Find the email and password fields, and submit button
    email_field = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "login-username")))
    password_field = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "login-password")))
    submit_button = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='login-button']")))

    # Enter the email and password, and submit the login form
    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()
    print(f"INFO: Tried to log in to {url}")

    # Wait for the account page to load
    url = "https://www.mintos.com/en/overview/"
    WebDriverWait(browser, 30).until(EC.url_to_be(url))
    print(f"INFO: Loading {url}...")
    time.sleep(9)
    html = browser.page_source
    browser.quit()
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.prettify()
    print(f"INFO: Obtained soup from {url} and closed browser")

    return soup

def estateguru_get_soup(email, password):
    # Configure Firefox options
    options = Options()
    options.headless = True  # Run Firefox in headless mode (without GUI)

    # Set path to geckodriver executable
    geckodriver_path = "./geckodriver.exe"  # Replace with the actual path to geckodriver

    # Create a new Firefox browser instance
    browser = webdriver.Firefox(options=options, executable_path=geckodriver_path)

    # Navigate to the login page
    url = "https://account.estateguru.co/auth/login/"
    browser.get(url)
    print(f"INFO: Opened {url}")

    # Find the email and password fields, and submit button
    email_field = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, ":r0:")))
    password_field = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, ":r1:")))
    submit_button = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, ":r2:")))


    # Enter the email and password, and submit the login form
    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()
    print(f"INFO: Tried to log in to {url}")

    # Wait for the account page to load
    url = "https://app.estateguru.co/portfolio/overview"
    WebDriverWait(browser, 30).until(EC.url_to_be(url))
    print(f"INFO: Loading {url}...")
    time.sleep(9)
    html = browser.page_source
    browser.quit()
    soup = BeautifulSoup(html, "html.parser")
    soup = soup.prettify()
    print(f"INFO: Obtained soup from {url} and closed browser")

    return soup

def peerberry_get_soup(email, password):
    # Configure Firefox options
    options = Options()
    options.headless = True # Run Firefox in headless mode (without GUI)

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

def get_current_timestamp():
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S")
    return timestamp

def save_soup(soup, page, dirpath,timestamp = None):
    final_dirpath = os.path.join(dirpath,page)
    if not os.path.isdir(final_dirpath):
        os.makedirs(final_dirpath)
        print(f"INFO: Created folder {final_dirpath}")
    if timestamp is None:
        file_path = os.path.join(final_dirpath, page + "_" + get_current_timestamp() + ".txt")
    else:
        file_path = os.path.join(final_dirpath, page + "_" + timestamp + ".txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(soup)
        print(f"INFO: Saved {page} soup to {file_path}")
    return

def load_soup(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = f.read()
        print(f"INFO: Loaded soup from {file_path}")
    return soup

def write_data_to_csv(json_data,web,dir_path,timestamp = None):
    file_path = os.path.join(dir_path,web+".csv")
    field_names = list(json_data.keys())
    field_names.insert(0,"timestamp")
    if timestamp is None: timestamp = get_current_timestamp()
    json_data["timestamp"] = timestamp
    with open(file_path, 'a', newline='') as file:
        try:
            writer = csv.DictWriter(file, fieldnames=field_names)
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(json_data)
            print(f"INFO: Wrote {web} data to {file_path}")
        except Exception as e:
            print(f"ERROR: Could not write data to {web} report")
            print("EXCEPTION: "+e)
            return 0
    return 1

def climb_tree_recursive(tag, route):
    children = tag.findChildren(recursive=False)
    if not children:
        return route
    else:
        for c in children:
            route[c] = tag
            climb_tree_recursive(c, route)
    return route

class Fideo():

    def __init__(self, fideo):
        self.grandpa = fideo
        self.raw_route = {}
        self.translation = {}
        self.route = {}
        self.tree = None
        self.nodes = set()

    def extract_tag_text(self, tag):
        t_stripped_strings = [t for t in tag.stripped_strings]

        if len(t_stripped_strings) == 1:
            return t_stripped_strings[0]
        else:
            children = tag.findChildren()
            if children:
                c_stripped_strings = []
                for c in children:
                    for i in c.stripped_strings:
                        c_stripped_strings.append(i)
                t_stripped_strings = list(set(t_stripped_strings) - set(c_stripped_strings))
                if len(t_stripped_strings) == 1:
                    return t_stripped_strings[0]
        if not t_stripped_strings:
            return None
        else:
            txt = " ".join(t_stripped_strings)

        return txt

    def create_node_name(self, tag, class_=True, id_=True, string_=True):
        name = tag.name
        c = None
        if "class" in tag.attrs.keys():
            c = ".".join(tag.attrs["class"])[:20]
        idx = None
        if "id" in tag.attrs.keys():
            c = tag.attrs["idx"][:20]
        txt = None
        txt = self.extract_tag_text(tag)

        s = [name]
        if idx and id_: s.append(f'id({idx})')
        if c and class_: s.append(f'class({c})')
        if txt and string_: s.append(f'txt({txt})')

        return "-".join(s)

    def create_tree_names(self):
        if not self.raw_route:
            self.climb_tree()
        names_dict = {}
        name = self.create_node_name(self.grandpa)
        self.nodes.add(name)
        names_dict[self.grandpa] = name
        for node in self.raw_route.keys():
            name = self.create_node_name(node)
            i = 1
            while True:
                if name not in self.nodes: break
                if i == 1:
                    name = name + "_1"
                    i+= 1
                else:
                    num = str(i)
                    name = name[:-len(num)] + num
            if name not in self.nodes:
                self.nodes.add(name)
            names_dict[node] = name
        self.translation = names_dict
        return

    def climb_tree(self):
        self.raw_route = climb_tree_recursive(self.grandpa,{})

    def translate_tree(self):
        if not self.translation:
            self.create_tree_names()

        translated_route = {}
        for k in self.raw_route.keys():
            translated_route[self.translation[k]] = self.translation[self.raw_route[k]]
        self.route = translated_route
        return

    def create_tree(self):
        if not self.route:
            self.translate_tree()
        self.tree = Tree()
        self.tree.create_node(self.translation[self.grandpa], self.translation[self.grandpa])
        for n in self.route.keys():
            self.tree.create_node(n, n, parent=self.route[n])
        return

    def show(self):
        if not self.tree:
            self.create_tree()

        self.tree.show()
        return

class Logger:

    def __init__(self, filename):
        self.console = sys.stdout
        self.file = open(filename, 'w', encoding="utf-8")

    def write(self, message):
        self.console.write(message)
        self.file.write(message)

    def flush(self):
        self.console.flush()
        self.file.flush()

    def quit(self):
        self.file.close()
        sys.stdout = sys.__stdout__
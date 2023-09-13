from utils import write_data_to_csv,load_soup
import os
import glob
import utils
import time
import math
from datetime import datetime
pages = ["mintos","estateguru","peerberry"]

def get_tmp_path(page):
    return os.path.join(os.path.dirname(__file__),"..","tmp",page)


def get_csvs(page):
    os.chdir(get_tmp_path(page))
    return glob.glob("*.txt")

records_dir = os.path.join(os.path.dirname(__file__),"..", "records")

for p in pages:
    for t in get_csvs(p):
        path = os.path.join(get_tmp_path(p),t)
        soup = utils.load_soup(path)
        json_data = utils.parse_soup(p, soup)
        timestamp = os.path.getmtime(path)
        timestamp = datetime.fromtimestamp(timestamp)
        timestamp = timestamp.strftime("%Y%m%d%H%M%S")
        utils.write_data_to_csv(json_data, p, records_dir,timestamp=timestamp)
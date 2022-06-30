# %% ######################################################################
###                                                                     ###
###                          Table of Contents                          ###
###                                                                     ###
###     0.          Dependent Libraries                                 ###
###     1.          Variable Initialization                             ###
###     3.          Helper Functions                                    ###
###     4.          Multi Threading                                     ###
###                                                                     ###
###########################################################################
###                                                                     ###
###     Input file : latlon.csv                                         ###
###         Index, Latitude, Longitude                                  ###
###         No Headers                                                  ###
###     Outfile file : latlon_elev.csv                                  ###
###         Index, Latitude, Longitude, Elevation                       ###
###         No Headers                                                  ###
###                                                                     ###
###     Unit is Feet.                                                   ###
###                                                                     ###
###########################################################################

### find /v /c "" latlon_elev.csv



# %% ######################################################################
###     0.          Dependent Libraries                                 ###
###########################################################################

import os, concurrent.futures
import requests, urllib
import re



# %% ######################################################################
###     1.          Variable Initialization                             ###
###########################################################################

url = r"https://nationalmap.gov/epqs/pqs.php?"
data_dir = os.getcwd()
loc_latlon = os.path.join(data_dir, "latlon.csv")
loc_elev = os.path.join(data_dir,
    os.path.splitext(os.path.basename(loc_latlon))[0] + "_elev.csv")



# %% ######################################################################
###     3.          Helper Functions                                    ###
###########################################################################

def query_elevation(lat, lon):
    params = {
        "output" : "json",
        "x" : lon,
        "y" : lat,
        "units" : "Feet",}
    http_get = requests.get(
        url + urllib.parse.urlencode(params),
        timeout = None)
    http_elev = http_get.json() \
        ["USGS_Elevation_Point_Query_Service"] \
        ["Elevation_Query"] \
        ["Elevation"]
    return(http_elev)

###########################################################################

def read_query_write(line):
    if (line.count(",") == 2):
        line = re.sub(" ", "", line.strip("\n"))
        id, lat, lon = line.split(",")
        elevation = query_elevation(lat, lon)
        line = f"{line},{elevation}\n"
    f_elev.write(line)
    f_elev.flush()
    os.fsync(f_elev.fileno())
    return



# %% ######################################################################
###     4.          Multi Threading                                     ###
###########################################################################

### Potential improvement :
### Use file as an iterator instead of reading in entire file.

f_latlon = open(loc_latlon, "r")
f_latlon_lines = f_latlon.readlines()
f_latlon.close()

import time
f_elev = open(loc_elev, "w")
t0 = time.time()
thread_pool = concurrent.futures.ThreadPoolExecutor(256)
thread_tasks = thread_pool.map(read_query_write, f_latlon_lines)
thread_pool.shutdown()
t1 = time.time()
t1 - t0

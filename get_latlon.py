# %% ######################################################################
###                                                                     ###
###                          Table of Contents                          ###
###                                                                     ###
###     0.          Dependent Libraries                                 ###
###     1.          Variable Initialization                             ###
###     3.          Helper Functions                                    ###
###     4.          Processing                                          ###
###     a.          Temporary - Determining Necessary Geocoders         ###
###     b.          Temporary - Supplementing in a Geocoder             ###
###     c.          Temporary - Remove Processed                        ###
###                                                                     ###
###########################################################################
###                                                                     ###
###     Input file : addr.csv                                           ###
###         Index, Address                                              ###
###         No Headers                                                  ###
###     Output file : latlon.csv                                        ###
###         Index, Latitude, Longitude                                  ###
###         No Headers                                                  ###
###                                                                     ###
###########################################################################
###                                                                     ###
### df_addr = df_id[[                                                   ###
###     "CONV_POLNUM",                                                  ###
###     "PROPERTY_STREET1",                                             ###
###     "PROPERTY_STREET2",                                             ###
###     "PROPERTY_CITY",                                                ###
###     "PROPERTY_STATE"]]                                              ###
### df_addr["address"] = df_addr \                                      ###
###     .filter(like = "PROPERTY_") \                                   ###
###     .fillna("") \                                                   ###
###     .apply(",".join, 1)                                             ###
### df_addr[["CONV_POLNUM", "address"]] \                               ###
###     .to_csv(os.path.join(data_dir_raw, "addr.csv"),                 ###
###         header = None, index = None, sep = "\t")                    ###
###                                                                     ###
###########################################################################

### find /v /c "" latlon.csv
### copy latlon.csv + latlon_finished.csv latlon_together.csv



# %% ######################################################################
###     0.          Dependent Libraries                                 ###
###########################################################################

import os # , concurrent.futures
# import pandas as pd
import re
import geopy, geopy.extra.rate_limiter as rl



# %% ######################################################################
###     1.          Variable Initialization                             ###
###########################################################################

data_dir = os.getcwd()
loc_addr = os.path.join(data_dir, "addr.csv")
loc_latlon = os.path.join(data_dir, "latlon.csv")



# %% ######################################################################
###     3.          Helper Functions                                    ###
###########################################################################

def query_geocoder(fn):
    def __query_geocoder__(addr):
        lat, lon = 0, 0
        loc = fn(addr)
        if (loc is not None):
            lat = loc.latitude
            lon = loc.longitude
        return(lat, lon)
    return(__query_geocoder__)

def query_latlon(addr):
    lat, lon = 0, 0
    for query_fn in query_fn_list:
        lat, lon = query_fn(addr)
        if ((lat != 0) or (lon != 0)):
            break
    return(lat, lon)

###########################################################################

name = "xufreddy9@gmail.com"
gc_limit = lambda gc : \
    rl.RateLimiter(gc.geocode, min_delay_seconds = 1)

gc_nom = geopy.geocoders.Nominatim(user_agent = name, timeout = None)
gc_arc = geopy.geocoders.ArcGIS(user_agent = name, timeout = None)

query_fn_list = [
    query_geocoder(gc_limit(gc_nom)),
    query_geocoder(gc_limit(gc_arc))]

###########################################################################

def read_query_write(line):
    if (line.count("\t") == 1):
        line = re.sub(",+", ",", line.strip("\n"))
        id, addr = line.split("\t")
        addr += ",USA"
        lat, lon = query_latlon(addr)
        line = f"{id},{lat},{lon}\n"
    f_latlon.write(line)
    f_latlon.flush()
    os.fsync(f_latlon.fileno())
    return



# %% ######################################################################
###     4.          Processing                                          ###
###########################################################################

f_addr = open(loc_addr, "r")
f_latlon = open(loc_latlon, "w")
for line in f_addr:
    read_query_write(line)

f_latlon.close()
f_addr.close()

###########################################################################

### Threading breaks TOS and minimum delay requirements.
### https://operations.osmfoundation.org/policies/nominatim/.

# f_addr = open(loc_addr, "r")
# f_addr_lines = f_addr.readlines()
# f_addr.close()
#
# import time
# f_latlon = open(loc_latlon, "w")
# t0 = time.time()
# thread_pool = concurrent.futures.ThreadPoolExecutor(256)
# thread_tasks = thread_pool.map(read_query_write, f_addr_lines)
# thread_pool.shutdown()
# t1 = time.time()
# t1 - t0

###########################################################################

### Caching is not immediate.

# df = pd.read_csv(loc_addr,
#     delimiter = "\t",
#     names = ["index", "address"])
# df.set_index("index", inplace = True)
# df["address"] = df["address"] \
#     .apply(lambda v : re.sub(",+", ",", v.strip("\n")))
# df["lat_lon"] = df["address"] \
#     .apply(query_latlon)
# df[["latitude", "longitude"]] = \
#     pd.DataFrame(df["lat_lon"].tolist(), index = df.index)
# df.reset_index(inplace = True)
# df[["index", "latitude", "longitude"]] \
#     .to_csv(loc_latlon, header = None, index = None)



# %% ######################################################################
###     a.          Temporary - Determining Necessary Geocoders         ###
###########################################################################

# import os, pandas as pd
#
# df = pd.read_csv(
#     os.path.join(os.getcwd(), "latlon.csv"),
#     names = ["index", "latitude", "longitude"])

###########################################################################

# num_rows = df.shape[0]
# num_null = df.loc[
#     (df["latitude"] == 0) & \
#     (df["longitude"] == 0)] \
#     .shape[0]
# pct_null = round(100 * num_null / num_rows, 2)

###########################################################################

# print(f"Out of {num_rows:,} records, missing {num_null:,} ({pct_null} %).")
#
# ### Using Nominatim :
# # Out of 20,187 records, missing 5,690 (28.19 %).
#
# ### Using Nominatim and ArcGIS :
# # Out of 20,187 records, missing 0 (0.0 %).
# # Out of 250,000 records, missing 0 (0.0 %).



# %% ######################################################################
###     b.          Temporary - Supplementing in a Geocoder             ###
###########################################################################

# import os, pandas as pd
# data_dir = os.getcwd()
#
# df_addr = pd.read_csv(
#     os.path.join(data_dir, "addr.csv"),
#     delimiter = "\t",
#     names = ["index", "address"])

###########################################################################

# gc_coder = geopy.geocoders.ArcGIS(
#     user_agent = "xufreddy9@gmail.com",
#     timeout = None)
# gc_query = rl.RateLimiter(gc_coder.geocode, min_delay_seconds = 1)
#
# f_old = open(os.path.join(data_dir, "latlon_old.csv"), "r")
# f_new = open(os.path.join(data_dir, "latlon_new.csv"), "w")
# for line in f_old:
#     line = line.strip("\n")
#     id, lat, lon = line.split(",")
#     if ((float(lat) != 0) or (float(lon) != 0)):
#         pass
#     else:
#         addr = df_addr.loc[df_addr["index"] == id]["address"].values[0]
#         addr = re.sub(",+", ",", addr)
#         loc = gc_query(addr)
#         if (loc is not None):
#             lat = loc.latitude
#             lon = loc.longitude
#     line = f"{id},{lat},{lon}\n"
#     f_new.write(line)
#     f_new.flush()
#     os.fsync(f_new.fileno())
#
# f_new.close()
# f_old.close()



# %% ######################################################################
###     c.          Temporary - Remove Processed                        ###
###########################################################################

# import os, pandas as pd
# data_dir = os.getcwd()
#
# df_addr = pd.read_csv(
#     os.path.join(data_dir, "addr_all.csv"),
#     delimiter = "\t",
#     names = ["index", "address"])
#
# df_latlon = pd.read_csv(
#     os.path.join(data_dir, "latlon_finished.csv"),
#     delimiter = ",",
#     names = ["index", "latitude", "longitude"])

###########################################################################

# df_remaining = df_addr \
#     .loc[~ df_addr["index"].isin(df_latlon["index"])]
#
# df_remaining.to_csv(
#     os.path.join(data_dir, "addr.csv"),
#     header = None, index = None, sep = "\t")

# %% ######################################################################
###                                                                     ###
###                          Table of Contents                          ###
###                                                                     ###
###     0.          Dependent Libraries                                 ###
###     1.          Variable Initialization                             ###
###     2.          Data - Raw                                          ###
###     3.          Helper Functions                                    ###
###     4.          Processing                                          ###
###                                                                     ###
###########################################################################
###                                                                     ###
###     Input file : latlon.csv                                         ###
###         Index, Latitude, Longitude                                  ###
###         No Headers                                                  ###
###     Outfile file : latlon_d2c.csv                                   ###
###         Index, Latitude, Longitude, Elevation                       ###
###         No Headers                                                  ###
###                                                                     ###
###     Unit is Miles.                                                  ###
###                                                                     ###
###     D denotes "distance between"                                    ###
###     A denotes "address point"                                       ###
###     C denotes "coast"                                               ###
###     G denotes "grid point"                                          ###
###                                                                     ###
###########################################################################
###                                                                     ###
###     Estimates distance to coast via 4 methods.                      ###
###     1.  Value of the closest known grid point.                      ###
###     2.  Average value of the 4 surrounding grid points.             ###
###     3.  Weighted average value of the 4 surrounding grid points.    ###
###         Weight is inversely proportional to distance.               ###
###     4.  Trigonometric estimation via multiple applications          ###
###         of the cosine law.                                          ###
###                                                                     ###
###########################################################################



# %% ######################################################################
###     0.          Dependent Libraries                                 ###
###########################################################################

import os
import urllib
import itertools, math, pandas as pd
import re
import geopy.distance



# %% ######################################################################
###     1.          Variable Initialization                             ###
###########################################################################

# url = r"https://oceancolor.gsfc.nasa.gov/docs/distfromcoast" \
#     r"/GMT_intermediate_coast_distance_01d.zip"
url = r"https://oceancolor.gsfc.nasa.gov/docs/distfromcoast" \
    r"/dist2coast.txt.bz2"
data_dir = os.getcwd()
loc_latlon = os.path.join(data_dir, "latlon.csv")
loc_d2c = os.path.join(data_dir,
    os.path.splitext(os.path.basename(loc_latlon))[0] + "_d2c.csv")
loc_d2c_all = os.path.join(data_dir,
    url.split("/")[-1])
loc_d2c_usa = os.path.join(data_dir,
    url.split("/")[-1].split(".")[0] + "_usa.csv")



# %% ######################################################################
###     2.          Data - Raw                                          ###
###########################################################################

if (not os.path.exists(loc_d2c_usa)):
    if (not os.path.exists(loc_d2c_all)):
        urllib.request.urlretrieve(url, loc_d2c_all)
    d2c_all = pd.read_csv(loc_d2c_all,
        delimiter = "\t",
        compression = "bz2",
        names = ["longitude", "latitude", "distance"])
    d2c_usa = d2c_all.loc[
        (25 <= d2c_all["latitude"]) &
        (d2c_all["latitude"] <= 50) &
        (-125 <= d2c_all["longitude"]) &
        (d2c_all["longitude"] <= -65)]
    d2c_usa.to_csv(loc_d2c_usa, index = False)

d2c_usa = pd.read_csv(loc_d2c_usa)

###########################################################################

lat_min = min(d2c_usa["latitude"])
lat_max = max(d2c_usa["latitude"])
lat_unq_func = len(d2c_usa["latitude"].unique())
lat_unq_calc = round(round(lat_max - lat_min, 2) / 0.04, 0) + 1
assert lat_unq_func == lat_unq_calc, "Inconsistent latitude count."

lon_min = min(d2c_usa["longitude"])
lon_max = max(d2c_usa["longitude"])
lon_unq_func = len(d2c_usa["longitude"].unique())
lon_unq_calc = round(round(lon_max - lon_min, 2) / 0.04, 0) + 1
assert lon_unq_func == lon_unq_calc, "Inconsistent longitude count."

assert lat_unq_func * lon_unq_func == d2c_usa.shape[0], \
    "Inconsistent (latitude, longitude) count."



# %% ######################################################################
###     3.          Helper Functions                                    ###
###########################################################################

def distance_latlon_pair(coord_1, coord_2):
    return(geopy.distance.distance(coord_1, coord_2).kilometers)

def km_to_mile(v):
    return(v * 0.621371)

###########################################################################

def get_grid(coord):
    ### Gets surrounding grid of a coordinate.
    ### lat_base = min(d2c_usa["latitude"])
    ### lon_base = min(d2c_usa["longitude"])
    lat_base, lon_base, increment = 25.02, -124.98, 0.04
    lat_increments = round(round(coord[0] - lat_base, 2) / increment, 0)
    lon_increments = round(round(coord[1] - lon_base, 2) / increment, 0)
    lat_1 = round(lat_base + round(lat_increments * increment, 2), 2)
    lat_2 = round(lat_1 + increment, 2)
    lon_1 = round(lon_base + round(lon_increments * increment, 2), 2)
    lon_2 = round(lon_1 + increment, 2)
    data_grid = {
        "nw" : {"coord" : (lat_2, lon_1)},
        "ne" : {"coord" : (lat_2, lon_2)},
        "sw" : {"coord" : (lat_1, lon_1)},
        "se" : {"coord" : (lat_1, lon_2)},}
    return(data_grid)

def get_d2c_exact(coord):
    d2c_exact = d2c_usa.loc[
        (d2c_usa["latitude"] == coord[0]) &
        (d2c_usa["longitude"] == coord[1])] \
        ["distance"].values[0]
    return(d2c_exact)

def get_d2c_closest(data_grid):
    ### Gets distance to coast :
    ###     value of the closest grid point.
    point_closest = min(
        data_grid.keys(),
        key = lambda v : data_grid[v]["d2a"])
    d2c = data_grid[point_closest]["d2c"]
    return(d2c)

def get_d2c_average_simple(data_grid):
    ### Gets distance to coast :
    ###     simple average of the 4 grid points.
    d2c = 0
    for gp in data_grid.keys():
        d_c_val = data_grid[gp]["d2c"]
        d_c_wgt = 1/4
        d2c += d_c_val * d_c_wgt
    return(d2c)

def get_d2c_average_weighted(data_grid):
    ### Gets distance to coast :
    ###     proximity-weighted average of the 4 grid points.
    d2c = 0
    total_weight = sum([data_grid[gp]["d2a"]
        for gp in data_grid.keys()])
    for gp in data_grid.keys():
        d_c_val = data_grid[gp]["d2c"]
        d_c_wgt = \
            (total_weight - data_grid[gp]["d2a"]) / \
            (3 * total_weight)
        d2c += d_c_val * d_c_wgt
    return(d2c)

###########################################################################

def __closest_value__(v1, v2, v):
    ### Returns the value in [v1, v2] that is closest to v.
    v_closest = v1
    if (abs(v1 - v) > abs(v2 - v)):
        v_closest = v2
    return(v_closest)

def __d2c_grid_pair__(g1_g2, g1_a, g1_c, g2_a, g2_c, base_val):
    ### Gets distance to coast :
    ###     trigonometric estimation from a grid point pair.
    ### Assume grid points and address point share closest coast point.
    ### 2 possible distances based on orientation of address point.
    ### Hence, base value is used to differentiate between the two.
    if (abs((g1_c + g1_g2 - g2_c) / g2_c) <= 10 ** -4):
        ### Case 1 : C_G1_G2 nearly forms a line.
        angle_a_g2_c = math.acos(
            ((g1_g2 ** 2) + (g2_a ** 2) - (g1_a ** 2)) /
            (2 * g1_g2 * g2_a))
        angle_a_g1_c = math.pi - math.acos(
            ((g1_g2 ** 2) + (g1_a ** 2) - (g2_a ** 2)) /
            (2 * g1_g2 * g1_a))
        a_c_1 = ((g2_a ** 2) + (g2_c ** 2) - (2 * g2_a * g2_c *
            math.cos(angle_a_g2_c))) ** 0.5
        a_c_2 = ((g1_a ** 2) + (g1_c ** 2) - (2 * g1_a * g1_c *
            math.cos(angle_a_g1_c))) ** 0.5
        a_c = (a_c_1 + a_c_2) / 2
    elif (abs((g2_c + g1_g2 - g1_c) / g1_c) <= 10 ** -4):
        ### Case 2 : C_G2_G1 nearly forms a line.
        angle_a_g1_c = math.acos(
            ((g1_g2 ** 2) + (g1_a ** 2) - (g2_a ** 2)) /
            (2 * g1_g2 * g1_a))
        angle_a_g2_c = math.pi - math.acos(
            ((g1_g2 ** 2) + (g2_a ** 2) - (g1_a ** 2)) /
            (2 * g1_g2 * g2_a))
        a_c_1 = ((g1_a ** 2) + (g1_c ** 2) - (2 * g1_a * g1_c *
            math.cos(angle_a_g1_c))) ** 0.5
        a_c_2 = ((g2_a ** 2) + (g2_c ** 2) - (2 * g2_a * g2_c *
            math.cos(angle_a_g2_c))) ** 0.5
        a_c = (a_c_1 + a_c_2) / 2
    elif (abs((g1_c + g2_c - g1_g2) / g1_g2) <= 10 ** -4):
        ### Case 3 : G1_C_G2 nearly forms a line.
        angle_a_g1_c = math.acos(
            ((g1_g2 ** 2) + (g1_a ** 2) - (g2_a ** 2)) /
            (2 * g1_g2 * g1_a))
        angle_a_g2_c = math.acos(
            ((g1_g2 ** 2) + (g2_a ** 2) - (g1_a ** 2)) /
            (2 * g1_g2 * g2_a))
        a_c_1 = ((g1_a ** 2) + (g1_c ** 2) - (2 * g1_a * g1_c *
                math.cos(angle_a_g1_c))) ** 0.5
        a_c_2 = ((g2_a ** 2) + (g2_c ** 2) - (2 * g2_a * g2_c *
                math.cos(angle_a_g2_c))) ** 0.5
        a_c = (a_c_1 + a_c_2) / 2
    elif (g1_c + g2_c < g1_g2):
        ### Case 4 : G1_G2_C cannot form a triangle.
        ### Assume Case 3 with C between G1 and G2.
        dist_short = (g1_g2 - g1_c - g2_c) / 2
        g1_c += dist_short
        g2_c += dist_short
        angle_a_g1_c = math.acos(
            ((g1_g2 ** 2) + (g1_a ** 2) - (g2_a ** 2)) /
            (2 * g1_g2 * g1_a))
        angle_a_g2_c = math.acos(
            ((g1_g2 ** 2) + (g2_a ** 2) - (g1_a ** 2)) /
            (2 * g1_g2 * g2_a))
        a_c_1 = ((g1_a ** 2) + (g1_c ** 2) - (2 * g1_a * g1_c *
                math.cos(angle_a_g1_c))) ** 0.5
        a_c_2 = ((g2_a ** 2) + (g2_c ** 2) - (2 * g2_a * g2_c *
                math.cos(angle_a_g2_c))) ** 0.5
        a_c = (a_c_1 + a_c_2) / 2
    elif (abs((g1_a + g2_a - g1_g2) / g1_g2) <= 10 ** -4):
        ### Case 5 : G1_A_G2 nearly forms a line.
        angle_a_g1_c = math.acos(
                ((g1_g2 ** 2) + (g1_c ** 2) - (g2_c ** 2)) /
                (2 * g1_g2 * g1_c))
        angle_a_g2_c = math.acos(
                ((g1_g2 ** 2) + (g2_c ** 2) - (g1_c ** 2)) /
                (2 * g1_g2 * g2_c))
        a_c_1 = ((g1_a ** 2) + (g1_c ** 2) - (2 * g1_a * g1_c *
                math.cos(angle_a_g1_c))) ** 0.5
        a_c_2 = ((g2_a ** 2) + (g2_c ** 2) - (2 * g2_a * g2_c *
                math.cos(angle_a_g2_c))) ** 0.5
        a_c = (a_c_1 + a_c_2) / 2
    else:
        angle_a_g1_g2 = math.acos(
                ((g1_g2 ** 2) + (g1_a ** 2) - (g2_a ** 2)) /
                (2 * g1_g2 * g1_a))
        angle_c_g1_g2 = math.acos(
                ((g1_g2 ** 2) + (g1_c ** 2) - (g2_c ** 2)) /
                (2 * g1_g2 * g1_c))
        angle_a_g2_g1 = math.acos(
                ((g1_g2 ** 2) + (g2_a ** 2) - (g1_a ** 2)) /
                (2 * g1_g2 * g2_a))
        angle_c_g2_g1 = math.acos(
                ((g1_g2 ** 2) + (g2_c ** 2) - (g1_c ** 2)) /
                (2 * g1_g2 * g2_c))
        a_c_1_1 = ((g1_a ** 2) + (g1_c ** 2) - (2 * g1_a * g1_c *
                math.cos(angle_a_g1_g2 + angle_c_g1_g2))) ** 0.5
        a_c_1_2 = ((g2_a ** 2) + (g2_c ** 2) - (2 * g2_a * g2_c *
                math.cos(angle_a_g2_g1 + angle_c_g2_g1))) ** 0.5
        a_c_2_1 = ((g1_a ** 2) + (g1_c ** 2) - (2 * g1_a * g1_c *
                math.cos(angle_a_g1_g2 - angle_c_g1_g2))) ** 0.5
        a_c_2_2 = ((g2_a ** 2) + (g2_c ** 2) - (2 * g2_a * g2_c *
                math.cos(angle_a_g2_g1 - angle_c_g2_g1))) ** 0.5
        a_c_1 = (a_c_1_1 + a_c_1_2) / 2
        a_c_2 = (a_c_2_1 + a_c_2_2) / 2
        a_c = __closest_value__(a_c_1, a_c_2, base_val)
    return(a_c)

def get_d2c_trig_estimation(data_grid, base_val):
    ### Gets distance to coast :
    ###     trigonometric estimation from all grid point pairs.
    trig_estimations = []
    for g1, g2 in itertools.combinations(data_grid.keys(), 2):
        d_g1_g2 = distance_latlon_pair(
            data_grid[g1]["coord"],
            data_grid[g2]["coord"])
        trig_estimations.append(
            __d2c_grid_pair__(
                d_g1_g2,
                data_grid[g1]["d2a"],
                data_grid[g1]["d2c"],
                data_grid[g2]["d2a"],
                data_grid[g2]["d2c"],
                base_val))
    d2c = sum(trig_estimations) / len(trig_estimations)
    return(d2c)

###########################################################################

def read_query_write(line):
    if (line.count(",") == 2):
        line = re.sub(" ", "", line.strip("\n"))
        id, lat, lon = line.split(",")
        lat = float(lat)
        lon = float(lon)
        data_grid = get_grid((lat, lon))
        for g in ["nw", "ne", "sw", "se"]:
            data_grid[g]["d2a"] = \
                distance_latlon_pair((lat, lon), data_grid[g]["coord"])
            data_grid[g]["d2c"] = \
                get_d2c_exact(coord = data_grid[g]["coord"])
        d2c_closest = round(km_to_mile(
            get_d2c_closest(data_grid)), 6)
        d2c_average_simple = round(km_to_mile(
            get_d2c_average_simple(data_grid)), 6)
        d2c_average_weighted = round(km_to_mile(
            get_d2c_average_weighted(data_grid)), 6)
        d2c_trig_estimation = round(km_to_mile(
            get_d2c_trig_estimation(data_grid, d2c_average_weighted)), 6)
        line = line + \
            "," + str(d2c_closest) + \
            "," + str(d2c_average_simple) + \
            "," + str(d2c_average_weighted) + \
            "," + str(d2c_trig_estimation) + \
            "\n"
    f_d2c.write(line)
    f_d2c.flush()
    os.fsync(f_d2c.fileno())
    return



# %% ######################################################################
###     4.          Processing                                          ###
###########################################################################

f_latlon = open(loc_latlon, "r")
f_d2c = open(loc_d2c, "w")
for line in f_latlon:
    read_query_write(line)
f_latlon.close()
f_d2c.close()

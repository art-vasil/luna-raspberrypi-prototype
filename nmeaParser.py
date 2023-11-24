#Source: https://pypi.org/project/pynmea2/1.8.0/
import pynmea2
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

msg = pynmea2.parse("$GPGGA,123519, 4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*67")
print("latitude=", msg.lat)
print("longitude=", msg.lon)

msg1 = pynmea2.parse("$GPGGA,184353.07,1929.045,S,02410.506,E,1,04,2.6,100.00,M,-33.9,M,,0000*6D")

gpsSpeed = haversine(float(msg.lat), float(msg.lon), float(msg1.lat), float(msg1.lon))
print("GPS speed", gpsSpeed, " km/hr")

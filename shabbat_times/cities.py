# -*- coding: utf-8 -*-
"""City list (owner decision pending; see README). 28 US cities weighted to US Jewish communities.
Coordinates: GeoNames city/town centroids (Five Towns = Cedarhurst, NY). Time zones are IANA names.
Order = display order (4:5 and 9:16 split the list in half). `region` sets the 1:1 split
(slide A = Northeast & Mid-Atlantic, slide B = Midwest, South & West).
To change the list, edit this file only; generate.py picks it up."""

CITIES = [
    # name,            state, lat,      lon,        tz,                    region
    ('Brooklyn',       'NY', 40.65010, -73.94958, 'America/New_York',    'A'),
    ('Manhattan',      'NY', 40.78343, -73.96625, 'America/New_York',    'A'),
    ('Queens',         'NY', 40.68149, -73.83652, 'America/New_York',    'A'),
    ('Five Towns',     'NY', 40.62288, -73.72430, 'America/New_York',    'A'),
    ('Monsey',         'NY', 41.11121, -74.06848, 'America/New_York',    'A'),
    ('Lakewood',       'NJ', 40.09789, -74.21764, 'America/New_York',    'A'),
    ('Passaic',        'NJ', 40.85677, -74.12848, 'America/New_York',    'A'),
    ('Teaneck',        'NJ', 40.89760, -74.01597, 'America/New_York',    'A'),
    ('Philadelphia',   'PA', 39.95233, -75.16379, 'America/New_York',    'A'),
    ('Pittsburgh',     'PA', 40.44062, -79.99589, 'America/New_York',    'A'),
    ('Baltimore',      'MD', 39.29038, -76.61219, 'America/New_York',    'A'),
    ('Washington',     'DC', 38.89511, -77.03637, 'America/New_York',    'A'),
    ('Boston',         'MA', 42.35843, -71.05977, 'America/New_York',    'A'),
    ('Cleveland',      'OH', 41.49950, -81.69541, 'America/New_York',    'B'),
    ('Detroit',        'MI', 42.33143, -83.04575, 'America/Detroit',     'B'),
    ('Chicago',        'IL', 41.85003, -87.65005, 'America/Chicago',     'B'),
    ('St. Louis',      'MO', 38.62727, -90.19789, 'America/Chicago',     'B'),
    ('Atlanta',        'GA', 33.74900, -84.38798, 'America/New_York',    'B'),
    ('Miami',          'FL', 25.77427, -80.19366, 'America/New_York',    'B'),
    ('Boca Raton',     'FL', 26.35869, -80.08310, 'America/New_York',    'B'),
    ('Dallas',         'TX', 32.78306, -96.80667, 'America/Chicago',     'B'),
    ('Houston',        'TX', 29.76328, -95.36327, 'America/Chicago',     'B'),
    ('Denver',         'CO', 39.73915, -104.98470, 'America/Denver',     'B'),
    ('Phoenix',        'AZ', 33.44838, -112.07404, 'America/Phoenix',    'B'),
    ('Las Vegas',      'NV', 36.17497, -115.13722, 'America/Los_Angeles', 'B'),
    ('Los Angeles',    'CA', 34.05223, -118.24368, 'America/Los_Angeles', 'B'),
    ('San Francisco',  'CA', 37.77493, -122.41942, 'America/Los_Angeles', 'B'),
    ('Seattle',        'WA', 47.60621, -122.33207, 'America/Los_Angeles', 'B'),
]


def cities():
    return [dict(name=n, st=s, lat=la, lon=lo, tz=tz, region=r, label='%s, %s' % (n, s), israel=False,
                 candle_min=18) for (n, s, la, lo, tz, r) in CITIES]


# International card (owner, Nov 9 2026: "add international cities"). Coordinates and time zones are exactly the
# GeoNames points Hebcal uses for these cities (read from the Hebcal API `location` object, 2026-11-09), so the
# offline times match Hebcal. Times are LOCAL to each city. Group W = around the world (Diaspora calendar),
# IL = Israel (Israel calendar: one day of Yom Tov, Israel parsha). Candle lighting = what the live Hebcal API returns
# (verified 2026-11-09, _validation/): Jerusalem 40 min, Haifa 30 min, Tel Aviv and Bnei Brak 20 min, all
# cities outside Israel 18 min.
# Display order: west to east within the world group.
INTL = [
    # name,          cc,   lat,       lon,        tz,                              group, candle_min, geonameid
    ('Toronto',      'CA', 43.65333, -79.38389, 'America/Toronto',                'W',  18, 6167865),
    ('Montreal',     'CA', 45.50884, -73.58781, 'America/Toronto',                'W',  18, 6077243),
    ('Mexico City',  'MX', 19.42847, -99.12766, 'America/Mexico_City',            'W',  18, 3530597),
    ('Buenos Aires', 'AR', -34.61315, -58.37723, 'America/Argentina/Buenos_Aires', 'W', 18, 3435910),
    ('London',       'UK', 51.50853, -0.12574,  'Europe/London',                  'W',  18, 2643743),
    ('Paris',        'FR', 48.85341, 2.3488,    'Europe/Paris',                   'W',  18, 2988507),
    ('Antwerp',      'BE', 51.22047, 4.40026,   'Europe/Brussels',                'W',  18, 2803138),
    ('Johannesburg', 'ZA', -26.20227, 28.04363, 'Africa/Johannesburg',            'W',  18, 993800),
    ('Melbourne',    'AU', -37.814,  144.96332, 'Australia/Melbourne',            'W',  18, 2158177),
    ('Jerusalem',    'IL', 31.76904, 35.21633,  'Asia/Jerusalem',                 'IL', 40, 281184),
    ('Tel Aviv',     'IL', 32.08088, 34.78057,  'Asia/Jerusalem',                 'IL', 20, 293397),
    ('Bnei Brak',    'IL', 32.08074, 34.8338,   'Asia/Jerusalem',                 'IL', 20, 295514),
    ('Haifa',        'IL', 32.81303, 34.99928,  'Asia/Jerusalem',                 'IL', 30, 294801),
]


def intl_cities():
    return [dict(name=n, st=cc, lat=la, lon=lo, tz=tz, region=g, israel=(g == 'IL'), candle_min=cm, geonameid=gid,
                 label='%s, %s' % (n, cc)) for (n, cc, la, lo, tz, g, cm, gid) in INTL]


# Brooklyn 11223 (Aleph Brick's home zip) drives the posting blackout window, per the brand rules.
BLACKOUT_LOC = dict(name='Brooklyn 11223', lat=40.5980, lon=-73.9660, tz='America/New_York')

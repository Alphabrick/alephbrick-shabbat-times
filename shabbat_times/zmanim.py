# -*- coding: utf-8 -*-
"""Offline zmanim for the Aleph Brick Shabbat-times generator. No network, no API keys.

Algorithm: NOAA solar position, two-pass, ported from the KosherJava NOAACalculator (the same algorithm
Hebcal uses through @hebcal/noaa). Sea level (Hebcal default: elevation off).
Hebcal defaults reproduced here (see README / AUTOMATION.md for sources):
  candle lighting      = sunset - 18 min (sunset seconds dropped first, as Hebcal's sunsetOffset does)
  Shabbat / Yom Tov end = tzeit, sun 8.5 deg below the horizon
  minor fast begins    = alot hashachar, sun 16.1 deg below the horizon
  fast ends            = tzeit, sun 7.083 deg below the horizon (3 medium stars)
  Tisha B'Av begins    = sunset
"""
import math, datetime as dt
from zoneinfo import ZoneInfo

GEOMETRIC_ZENITH = 90.0
REFRACTION = 34 / 60.0
SOLAR_RADIUS = 16 / 60.0
UTC = dt.timezone.utc


def _jd(y, m, d):
    if m <= 2:
        y -= 1; m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def _jc(jd):
    return (jd - 2451545.0) / 36525.0


def _geom_mean_long(t):
    return (280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360.0


def _geom_mean_anom(t):
    return 357.52911 + t * (35999.05029 - 0.0001537 * t)


def _ecc(t):
    return 0.016708634 - t * (0.000042037 + 0.0000001267 * t)


def _eq_center(t):
    m = math.radians(_geom_mean_anom(t))
    return (math.sin(m) * (1.914602 - t * (0.004817 + 0.000014 * t)) + math.sin(2 * m) * (0.019993 - 0.000101 * t)
            + math.sin(3 * m) * 0.000289)


def _app_long(t):
    true_long = _geom_mean_long(t) + _eq_center(t)
    omega = 125.04 - 1934.136 * t
    return true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))


def _obliq(t):
    secs = 21.448 - t * (46.8150 + t * (0.00059 - t * 0.001813))
    e0 = 23.0 + (26.0 + secs / 60.0) / 60.0
    return e0 + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * t))


def _decl(t):
    return math.degrees(math.asin(math.sin(math.radians(_obliq(t))) * math.sin(math.radians(_app_long(t)))))


def _eq_time(t):
    eps = _obliq(t); l0 = _geom_mean_long(t); e = _ecc(t); m = _geom_mean_anom(t)
    y = math.tan(math.radians(eps) / 2.0) ** 2
    s2l0 = math.sin(2 * math.radians(l0)); sm = math.sin(math.radians(m))
    c2l0 = math.cos(2 * math.radians(l0)); s4l0 = math.sin(4 * math.radians(l0)); s2m = math.sin(2 * math.radians(m))
    et = y * s2l0 - 2 * e * sm + 4 * e * y * sm * c2l0 - 0.5 * y * y * s4l0 - 1.25 * e * e * s2m
    return math.degrees(et) * 4.0


def _hour_angle(lat, decl, zenith, rising):
    lr = math.radians(lat); dr = math.radians(decl)
    x = math.cos(math.radians(zenith)) / (math.cos(lr) * math.cos(dr)) - math.tan(lr) * math.tan(dr)
    if x > 1 or x < -1:
        return None
    ha = math.acos(x)
    return ha if rising else -ha


def _solar_noon_utc(jd, lon_w):
    t = _jc(jd + lon_w / 360.0)
    eq = _eq_time(t)
    noon = lon_w * 4 - eq
    t2 = _jc(jd + noon / 1440.0)
    return 720 + lon_w * 4 - _eq_time(t2)


def _event_utc_minutes(jd, lat, lon_w, zenith, rising):
    noon = _solar_noon_utc(jd, lon_w)
    t = _jc(jd + noon / 1440.0)
    ha = _hour_angle(lat, _decl(t), zenith, rising)
    if ha is None:
        return None
    utc = 720 + 4 * (lon_w - math.degrees(ha)) - _eq_time(t)
    t2 = _jc(jd + utc / 1440.0)
    ha = _hour_angle(lat, _decl(t2), zenith, rising)
    if ha is None:
        return None
    return 720 + 4 * (lon_w - math.degrees(ha)) - _eq_time(t2)


def _adjust(zenith):
    return zenith + SOLAR_RADIUS + REFRACTION if zenith == GEOMETRIC_ZENITH else zenith


def event(date, lat, lon, tzid, degrees_below, rising):
    """Exact (unrounded) local datetime when the sun is `degrees_below` the horizon (0 = sunrise/sunset with
    refraction and semidiameter), on the local civil `date`."""
    z = _adjust(GEOMETRIC_ZENITH + degrees_below)
    mins = _event_utc_minutes(_jd(date.year, date.month, date.day), lat, -lon, z, rising)
    if mins is None:
        return None
    base = dt.datetime(date.year, date.month, date.day, tzinfo=UTC)
    tz = ZoneInfo(tzid)
    t = (base + dt.timedelta(minutes=mins)).astimezone(tz)
    # A west-of-Greenwich evening event can land on the next UTC day; a morning one can come out a day off for
    # far-east zones. Re-anchor so the local date matches the requested civil date.
    if t.date() != date:
        shift = (date - t.date()).days
        base2 = base + dt.timedelta(days=shift)
        mins = _event_utc_minutes(_jd(base2.year, base2.month, base2.day), lat, -lon, z, rising)
        t = (base2 + dt.timedelta(minutes=mins)).astimezone(tz)
    return t


def round_nearest(t):
    t2 = t.replace(second=0, microsecond=0)
    return t2 + dt.timedelta(minutes=1) if t.second >= 30 else t2


def sunset(date, c):
    return event(date, c['lat'], c['lon'], c['tz'], 0, False)


def candle_lighting(date, c, mins=18):
    s = sunset(date, c).replace(second=0, microsecond=0)
    return s - dt.timedelta(minutes=mins)


def tzeit(date, c, deg=8.5):
    return round_nearest(event(date, c['lat'], c['lon'], c['tz'], deg, False))


def alot(date, c, deg=16.1):
    return round_nearest(event(date, c['lat'], c['lon'], c['tz'], deg, True))


def sunset_rounded(date, c):
    return round_nearest(sunset(date, c))


def sunset_plus(date, c, mins):
    """Hebcal-style fixed-minute havdalah (e.g. 72 min): sunset rounded up if >= 30 s, then + mins."""
    s = sunset(date, c)
    extra = 1 if s.second >= 30 else 0
    return s.replace(second=0, microsecond=0) + dt.timedelta(minutes=mins + extra)

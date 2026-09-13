#!/usr/bin/python
# << CODE BY HUNX04
# << MAU RECODE ??? IZIN DULU LAH,  MINIMAL TAG AKUN GITHUB MIMIN YANG MENGARAH KE AKUN INI, LEBIH GAMPANG SI PAKE FORK
# << KALAU DI ATAS TIDAK DI IKUTI MAKA AKAN MENDAPATKAN DOSA KARENA MIMIN GAK IKHLAS
# “Wahai orang-orang yang beriman! Janganlah kamu saling memakan harta sesamamu dengan jalan yang batil,” (QS. An Nisaa': 29). Rasulullah SAW juga melarang umatnya untuk mengambil hak orang lain tanpa izin.
# << Maintained fork (v2.3): bug fixes, error handling, HTTPS, timeouts, DE-friendly phone lookup
#    Original by HunxByts (https://github.com/HunxByts/GhostTrack) — all credit to the original author.

# IMPORT MODULE

import json
import requests
import time
import os
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from sys import stderr

Bl = '\033[30m'  # VARIABLE BUAT WARNA CUYY
Re = '\033[1;31m'
Gr = '\033[1;32m'
Ye = '\033[1;33m'
Blu = '\033[1;34m'
Mage = '\033[1;35m'
Cy = '\033[1;36m'
Wh = '\033[1;37m'

REQUEST_TIMEOUT = 10  # seconds — never hang forever on a dead site
BROWSER_HEADERS = {
    # Some social sites return 4xx/redirects to bots without a UA header,
    # which caused false "username not found" results.
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


# utilities

def safe_get(data, *keys, default="N/A"):
    """Safely read nested keys from an API response without crashing."""
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current if current not in (None, "") else default


# decorator for attaching run_banner to a function
def is_option(func):
    def wrapper(*args, **kwargs):
        run_banner()
        func(*args, **kwargs)

    return wrapper


# FUNCTIONS FOR MENU
@is_option
def IP_Track():
    ip = input(f"{Wh}\n Enter IP target : {Gr}")  # INPUT IP ADDRESS
    print()
    print(f' {Wh}============= {Gr}SHOW INFORMATION IP ADDRESS {Wh}=============')
    try:
        req_api = requests.get(f"https://ipwho.is/{ip}", timeout=REQUEST_TIMEOUT)  # API IPWHOIS.IS (HTTPS)
        ip_data = json.loads(req_api.text)
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"{Re}\n [ ! ] Failed to reach ipwho.is: {e}")
        return

    if not ip_data.get("success", False):
        print(f"{Re}\n [ ! ] Lookup failed: {safe_get(ip_data, 'message', default='unknown IP or API error')}")
        return

    lat = ip_data.get("latitude")
    lon = ip_data.get("longitude")
    time.sleep(1)
    print(f"{Wh}\n IP target       :{Gr}", ip)
    print(f"{Wh} Type IP         :{Gr}", safe_get(ip_data, "type"))
    print(f"{Wh} Country         :{Gr}", safe_get(ip_data, "country"))
    print(f"{Wh} Country Code    :{Gr}", safe_get(ip_data, "country_code"))
    print(f"{Wh} City            :{Gr}", safe_get(ip_data, "city"))
    print(f"{Wh} Continent       :{Gr}", safe_get(ip_data, "continent"))
    print(f"{Wh} Continent Code  :{Gr}", safe_get(ip_data, "continent_code"))
    print(f"{Wh} Region          :{Gr}", safe_get(ip_data, "region"))
    print(f"{Wh} Region Code     :{Gr}", safe_get(ip_data, "region_code"))
    print(f"{Wh} Latitude        :{Gr}", lat)
    print(f"{Wh} Longitude       :{Gr}", lon)
    # keep full float precision so the map link points at the exact spot
    print(f"{Wh} Maps            :{Gr}", f"https://www.google.com/maps/@{lat},{lon},8z" if lat is not None and lon is not None else "N/A")
    print(f"{Wh} EU              :{Gr}", safe_get(ip_data, "is_eu"))
    print(f"{Wh} Postal          :{Gr}", safe_get(ip_data, "postal"))
    print(f"{Wh} Calling Code    :{Gr}", safe_get(ip_data, "calling_code"))
    print(f"{Wh} Capital         :{Gr}", safe_get(ip_data, "capital"))
    print(f"{Wh} Borders         :{Gr}", safe_get(ip_data, "borders"))
    print(f"{Wh} Country Flag    :{Gr}", safe_get(ip_data, "flag", "emoji"))
    print(f"{Wh} ASN             :{Gr}", safe_get(ip_data, "connection", "asn"))
    print(f"{Wh} ORG             :{Gr}", safe_get(ip_data, "connection", "org"))
    print(f"{Wh} ISP             :{Gr}", safe_get(ip_data, "connection", "isp"))
    print(f"{Wh} Domain          :{Gr}", safe_get(ip_data, "connection", "domain"))
    print(f"{Wh} ID              :{Gr}", safe_get(ip_data, "timezone", "id"))
    print(f"{Wh} ABBR            :{Gr}", safe_get(ip_data, "timezone", "abbr"))
    print(f"{Wh} DST             :{Gr}", safe_get(ip_data, "timezone", "is_dst"))
    print(f"{Wh} Offset          :{Gr}", safe_get(ip_data, "timezone", "offset"))
    print(f"{Wh} UTC             :{Gr}", safe_get(ip_data, "timezone", "utc"))
    print(f"{Wh} Current Time    :{Gr}", safe_get(ip_data, "timezone", "current_time"))


@is_option
def phoneGW():
    User_phone = input(
        f"\n {Wh}Enter phone number target {Gr}Ex [+4915112345678] {Wh}: {Gr}")  # INPUT NUMBER PHONE
    default_region = input(f" {Wh}Default region code (Enter = DE) {Gr}: {Gr}") or "DE"

    try:
        parsed_number = phonenumbers.parse(User_phone, default_region)  # VARIABLE PHONENUMBERS
    except phonenumbers.NumberParseException as e:
        print(f"{Re}\n [ ! ] Invalid phone number: {e}")
        return

    region_code = phonenumbers.region_code_for_number(parsed_number)
    jenis_provider = carrier.name_for_number(parsed_number, "en")
    location = geocoder.description_for_number(parsed_number, "en")
    is_valid_number = phonenumbers.is_valid_number(parsed_number)
    is_possible_number = phonenumbers.is_possible_number(parsed_number)
    formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    formatted_number_for_mobile = phonenumbers.format_number_for_mobile_dialing(parsed_number, default_region,
                                                                                with_formatting=True)
    number_type = phonenumbers.number_type(parsed_number)
    timezone1 = timezone.time_zones_for_number(parsed_number)
    timezoneF = ', '.join(timezone1)

    print(f"\n {Wh}========== {Gr}SHOW INFORMATION PHONE NUMBERS {Wh}==========")
    print(f"\n {Wh}Location             :{Gr} {location}")
    print(f" {Wh}Region Code          :{Gr} {region_code}")
    print(f" {Wh}Timezone             :{Gr} {timezoneF}")
    print(f" {Wh}Operator             :{Gr} {jenis_provider}")
    print(f" {Wh}Valid number         :{Gr} {is_valid_number}")
    print(f" {Wh}Possible number      :{Gr} {is_possible_number}")
    print(f" {Wh}International format :{Gr} {formatted_number}")
    print(f" {Wh}Mobile format        :{Gr} {formatted_number_for_mobile}")
    print(f" {Wh}Original number      :{Gr} {parsed_number.national_number}")
    print(
        f" {Wh}E.164 format         :{Gr} {phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)}")
    print(f" {Wh}Country code         :{Gr} {parsed_number.country_code}")
    print(f" {Wh}Local number         :{Gr} {parsed_number.national_number}")
    if number_type == phonenumbers.PhoneNumberType.MOBILE:
        print(f" {Wh}Type                 :{Gr} This is a mobile number")
    elif number_type == phonenumbers.PhoneNumberType.FIXED_LINE:
        print(f" {Wh}Type                 :{Gr} This is a fixed-line number")
    else:
        print(f" {Wh}Type                 :{Gr} This is another type of number")


@is_option
def TrackLu():
    username = input(f"\n {Wh}Enter Username : {Gr}")
    results = {}
    social_media = [
        {"url": "https://www.facebook.com/{}", "name": "Facebook"},
        {"url": "https://www.twitter.com/{}", "name": "Twitter"},
        {"url": "https://www.instagram.com/{}", "name": "Instagram"},
        {"url": "https://www.linkedin.com/in/{}", "name": "LinkedIn"},
        {"url": "https://www.github.com/{}", "name": "GitHub"},
        {"url": "https://www.pinterest.com/{}", "name": "Pinterest"},
        {"url": "https://www.tumblr.com/{}", "name": "Tumblr"},
        {"url": "https://www.youtube.com/@", "name": "Youtube"},
        {"url": "https://soundcloud.com/{}", "name": "SoundCloud"},
        {"url": "https://www.snapchat.com/add/{}", "name": "Snapchat"},
        {"url": "https://www.tiktok.com/@{}", "name": "TikTok"},
        {"url": "https://www.behance.net/{}", "name": "Behance"},
        {"url": "https://medium.com/@{}", "name": "Medium"},
        {"url": "https://www.quora.com/profile/{}", "name": "Quora"},
        {"url": "https://www.flickr.com/people/{}", "name": "Flickr"},
        {"url": "https://www.twitch.tv/{}", "name": "Twitch"},
        {"url": "https://www.dribbble.com/{}", "name": "Dribbble"},
        {"url": "https://www.producthunt.com/@{}", "name": "Product Hunt"},
        {"url": "https://t.me/{}", "name": "Telegram"},
    ]
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)

    for site in social_media:
        url = site['url'].format(username)
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=False)
            found = response.status_code == 200
        except requests.RequestException:
            found = None  # network error / site down — unknown, not "not found"
        results[site['name']] = url if found else (None if found is False else "?")

    print(f"\n {Wh}========== {Gr}SHOW INFORMATION USERNAME {Wh}==========")
    print()
    for site, url in results.items():
        if url:
            print(f" {Wh}[ {Gr}+ {Wh}] {site} : {Gr}{url}")
        elif url == "?":
            print(f" {Wh}[ {Ye}? {Wh}] {site} : {Ye}unreachable / unknown")
        else:
            print(f" {Wh}[ {Re}- {Wh}] {site} : {Ye}Username not found !")


@is_option
def showIP():
    try:
        respone = requests.get('https://api.ipify.org/', timeout=REQUEST_TIMEOUT)
        Show_IP = respone.text
    except requests.RequestException as e:
        print(f"{Re}\n [ ! ] Failed to reach api.ipify.org: {e}")
        return

    print(f"\n {Wh}========== {Gr}SHOW INFORMATION YOUR IP {Wh}==========")
    print(f"\n {Wh}[{Gr} + {Wh}] Your IP Adrress : {Gr}{Show_IP}")
    print(f"\n {Wh}==============================================")


# OPTIONS
options = [
    {
        'num': 1,
        'text': 'IP Tracker',
        'func': IP_Track
    },
    {
        'num': 2,
        'text': 'Show Your IP',
        'func': showIP

    },
    {
        'num': 3,
        'text': 'Phone Number Tracker',
        'func': phoneGW
    },
    {
        'num': 4,
        'text': 'Username Tracker',
        'func': TrackLu
    },
    {
        'num': 0,
        'text': 'Exit',
        'func': exit
    }
]


def clear():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
    # for mac and linux
    else:
        _ = os.system('clear')


def is_in_options(num):
    for opt in options:
        if opt['num'] == num:
            return True
    return False


def option_text():
    text = ''
    for opt in options:
        text += f'{Wh}[ {opt["num"]} ] {Gr}{opt["text"]}\n'
    return text


def option():
    # BANNER TOOLS
    clear()
    stderr.writelines(rf"""
       ________               __      ______                __
      / ____/ /_  ____  _____/ /_    /_  __/________ ______/ /__
     / / __/ __ \/ __ \/ ___/ __/_____/ / / ___/ __ `/ ___/ //_/
    / /_/ / / / / /_/ (__  ) /_/_____/ / / /  / /_/ / /__/ ,<
    \\____/_/ /_/\\____/____/\\__/     /_/ /_/   \\__,_/\\___/_/|_|

              {Wh}[ + ]  C O D E   B Y  H U N X  [ + ]
    """)

    stderr.writelines(f"\n\n\n{option_text()}")


def run_banner():
    clear()
    stderr.writelines(rf"""{Wh}
         .-.
       .'   `.          {Wh}--------------------------------
       :g g   :         {Wh}| {Gr}GHOST - TRACKER - IP ADDRESS {Wh}|
       : o    `.        {Wh}|       {Gr}@CODE BY HUNXBYTS      {Wh}|
      :         ``.     {Wh}--------------------------------
     :             `.
    :  :         .   `.
    :   :          ` . `.
     `.. :            `. ``;
        `:;             `:'
           :              `.
            `.              `.     .
              `'`'`'`---..,___`;.-'
        """)


def main():
    while True:
        clear()
        option()
        try:
            opt = int(input(f"{Wh}\n [ + ] {Gr}Select Option : {Wh}"))
        except ValueError:
            print(f'\n{Wh}[ {Re}! {Wh}] {Re}Please input number')
            time.sleep(2)
            continue

        if not is_in_options(opt):
            print(f'\n{Wh}[ {Re}! {Wh}] {Re}Option not found')
            time.sleep(2)
            continue

        for opt_item in options:
            if opt_item['num'] == opt:
                try:
                    opt_item['func']()
                except KeyboardInterrupt:
                    print(f'\n{Wh}[ {Re}! {Wh}] {Re}Exit')
                    time.sleep(2)
                    exit()
                input(f'\n{Wh}[ {Gr}+ {Wh}] {Gr}Press enter to continue')
                break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\n{Wh}[ {Re}! {Wh}] {Re}Exit')
        time.sleep(2)
        exit()

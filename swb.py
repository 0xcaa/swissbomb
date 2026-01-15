#!/usr/bin/env python3

from specific import weightedgrade
from specific import cypher
from specific import format_response
import helpers

import sys, argparse, random, time, subprocess, string, socket, json, os, tempfile
from pathlib import Path


import requests
from bs4 import BeautifulSoup
import urllib.parse
from urllib.parse import urljoin, urlencode, urlparse
from urllib3.util.retry import Retry

##Todo
# robots.txt vuln checker function
# git repository finder function
# pass wordlist as filename to exploit function

def check_robots(result: dict):
    """
    Check for robots.txt files on the main URL and all subdomains found
    """
    # Get the base URL and subdomains
    base_url = result.get("url", "")
    domain = result.get("hostname", "")
    subdomains = result.get("Subdomains", [])

    # Create a list of URLs to check for robots.txt
    urls_to_check = [base_url]

    # Add all subdomains to the list
    for subdomain in subdomains:
        urls_to_check.append(subdomain)

    # Store results in the results dictionary
    if "Robots_txt_results" not in result:
        result["Robots_txt_results"] = {}

    # Check each URL for robots.txt
    for url in urls_to_check:
        try:
            # Construct the robots.txt URL
            if url.endswith('/'):
                robots_url = url + "robots.txt"
            else:
                robots_url = url + "/robots.txt"

            # Send request to robots.txt
            response = requests.get(
                robots_url,
                verify=False,
                allow_redirects=True,
                timeout=5
            )

            # Store the result
            result["Robots_txt_results"][robots_url] = {
                "status_code": response.status_code,
                "content_length": len(response.content),
                "headers": dict(response.headers)
            }

            # Print status
            if response.status_code == 200:
                print(f"{GREEN}200{RESET} robots.txt found at {robots_url}")
            else:
                print(f"{RED}{response.status_code}{RESET} robots.txt not found at {robots_url}")

        except Exception as e:
            print(f"{RED}Error checking {robots_url}: {e}{RESET}")
            result["Robots_txt_results"][robots_url] = {
                "error": str(e)
            }

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
        if result.get("Subdomain_wildcard_detected", False):
            if 200 <= status < 300:
                print(f"{RED}{status}{RESET} {target} {location} * wildcard detected{RESET}")
                return True
            else:
                result["Subdomain_wildcard_detected"] = False
                return False
        #detect redirect
        if status in (301, 302, 307, 308):
            print(f"{BLUE}{status}{RESET} {target} -> {location}{RESET}")
            return False
        elif 200 <= status < 300:
            print(f"{GREEN}{status}{RESET} {target} exists!{RESET}")
            # Store the hostname in result dictionary for 200 responses
            if "Successful_Hostnames" not in result:
                result["Successful_Hostnames"] = []
            result["Successful_Hostnames"].append(target)
            return True
        elif 300 <= status < 400:
            print(f"{BLUE}{status}{RESET} {target} {location}{RESET}")
            return False
        elif 400 <= status < 500:
            print(f"{RED}{status}{RESET} {target} {location}{RESET}")
            return False
        else:
            print(f"{RED}{status}{RESET} {target}{RESET}")
            return False
    except requests.exceptions.HTTPError as e:
        print(RED)
        print(f"{target}")
        print(e)
        print(RESET)
    except requests.RequestException as e:
        print(RED)
        print(f"{target}")
        print(e)
        print(RESET)

    return False


def enumerate_subdomains(result: dict, timeout: int = 5):
    """
    Modified to only take result dictionary and store all info there
    """
    # Get values from result dictionary
    url = result.get("url", "")
    domain = result.get("hostname", "")
    ip = result.get("IP", "")
    HTTPS = result.get("HTTPS", False)
    speed = result.get("speed", 0.1)

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
        test_target = f"https://{random_header}"
        result["Target"] = test_target
        if send_request(random_target, random_header, result, timeout):
            print("This domain uses wildcard")
            return
        result["Target"] = f"{url}"
        if result.get("Subdomain_wildcard_detected", False):
            return
    else:
        test_target = f"http://{random_header}"
        result["Target"] = test_target
        if send_request(random_target, random_header, result, timeout):
            print("This domain uses wildcard")
            return
        result["Target"] = f"{url}"
        if result.get("Subdomain_wildcard_detected", False):
            result["Target"] = f"https://{random_header}"
            return

    # loop through wordlist of subdomains
    with open("wordlist.txt") as f:
        for word in f:
            word = word.strip()
            header = f"{word}.{domain}"
            if HTTPS:
                test_target = f"https://{word}.{domain}"
                result["Target"] = test_target
                if send_request(target, header, result, timeout):
                    # Store successful subdomain in result dictionary
                    if "Subdomains" not in result:
                        result["Subdomains"] = []
                    result["Subdomains"].append(test_target)
            else:
                test_target = f"http://{word}.{domain}"
                result["Target"] = test_target
                if send_request(target, header, result, timeout):
                    # Store successful subdomain in result dictionary
                    if "Subdomains" not in result:
                        result["Subdomains"] = []
                    result["Subdomains"].append(test_target)

            time.sleep(speed)
        result["Target"] = f"{url}"

    return result


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

    # Initialize result dictionary with all needed values
    result = {"Target": url,
              "IP": ip,
              "url": url,
              "hostname": hostname,
              "speed": speed  # Store speed in result for enumerate_subdomains
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

    # Better HTTPS recognition - check if scheme is https or if port 443 is used
    if parsed_url.scheme == "https" or parsed_url.port == 443:
        HTTPS = True
        print(GREEN + "HTTPS:", str(HTTPS) + RESET)
        result["HTTPS"] = HTTPS  # Store in result dictionary
    else:
        HTTPS = False
        print(YELLOW + "HTTPS:", str(HTTPS) + RESET)
        result["HTTPS"] = HTTPS  # Store in result dictionary

    print('Target:', url)
    time.sleep(2)


#   resume from last scan
    if not args.newscan:
        load_log(output_file, result)

# select function to run
    if result["Enumerate_subdomain"]:
        enumerate_subdomains(result, timeout)  # Pass only result dictionary
        write_current_state(output_file, result)

    if result["Check_robots"]:
        check_robots(result)
        write_current_state(output_file, result)

    sys.exit()

#    cypher(url)
#    sys.exit()
#    weightedgrade()
#    sys.exit()

if __name__=="__main__":
    main()



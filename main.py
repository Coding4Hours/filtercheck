import json
import re
import requests
from bs4 import BeautifulSoup

# Load blocked list
with open("blocked.json") as f:
    blocked_list = json.load(f)

def is_blocked(cat: str, filter_name: str) -> bool:
    f_dat = blocked_list.get(filter_name, [])
    for item in f_dat:
        if re.search(item.lower(), cat.lower()):
            return True
    return False

# Lightspeed
def lightspeed_categorize(num: int) -> str | int:
    with open("lightspeed.json") as f:
        cat_json = json.load(f)
    for item in cat_json:
        if item["CategoryNumber"] == num:
            cat = item["CategoryName"]
            cat_block = is_blocked(cat, "lightspeed")
            return f"{cat} ({'Likely **Blocked**' if cat_block else 'Likely **Unblocked**'})"
    return num

def lightspeed(url: str) -> list[str | int]:
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'authority': 'production-archive-proxy-api.lightspeedsystems.com',
        'content-type': 'application/json',
        'origin': 'https://archive.lightspeedsystems.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'x-api-key': 'onEkoztnFpTi3VG7XQEq6skQWN3aFm3h'
    }
    body = {
        "query": "\nquery getDeviceCategorization($itemA: CustomHostLookupInput!, $itemB: CustomHostLookupInput!){\n  a: custom_HostLookup(item: $itemA) { cat}\n  b: custom_HostLookup(item: $itemB) { cat }\n}",
        "variables": {
            "itemA": {"hostname": url},
            "itemB": {"hostname": url}
        }
    }
    try:
        res = requests.post("https://production-archive-proxy-api.lightspeedsystems.com/archiveproxy", headers=headers, json=body)
        body_json = res.json()
        cat = [body_json["data"]["a"]["cat"], body_json["data"]["b"]["cat"]]
        return [lightspeed_categorize(cat[0]), lightspeed_categorize(cat[1])]
    except Exception as e:
        return [f"Error: {e}"]

# FortiGuard
def fortiguard(url: str) -> str:
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://www.fortiguard.com',
        'Referer': 'https://www.fortiguard.com/services/sdns',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Cookie': 'cookiesession1=678A3E0F33B3CB9D7BEECD2B8A5DD036; privacy_agreement=true'
    }
    body = {"value": url, "version": 9}
    try:
        res = requests.post("https://www.fortiguard.com/learnmore/dns", headers=headers, json=body)
        r_json = res.json()
        cat = r_json["dns"]["categoryname"]
        cat_block = is_blocked(cat, "fortiguard")
        return f"{cat} ({'Likely **Blocked**' if cat_block else 'Likely **Unblocked**'})"
    except Exception as e:
        return f"Error: {e}"

# Palo Alto
def palo(domain: str) -> list[str] | str:
    try:
        res = requests.get(f"https://urlfiltering.paloaltonetworks.com/single_cr/?url={domain}")
        soup = BeautifulSoup(res.text, "html.parser")
        cat_arr = [
            soup.select('*[for="id_new_category"]')[2].parent.find(class_="form-text").text.strip(),
            soup.select('*[for="id_new_category"]')[1].parent.find(class_="form-text").text.strip()
        ]
        cat = cat_arr[0]
        cat_block = is_blocked(cat, "palo")
        return [f"{cat} ({'Likely **Blocked**' if cat_block else 'Likely **Unblocked**'})", cat_arr[1]]
    except Exception as e:
        return f"Error: {e}"

# Blocksi
def blocksi_categorize(num: int) -> str | int:
    with open("blocksi.json") as f:
        cat_json = json.load(f)
    for cat in cat_json.values():
        for subcat_num, subcat_name in cat.items():
            if str(num) == str(subcat_num):
                cat_block = is_blocked(subcat_name, "blocksi")
                return f"{subcat_name} ({'Likely **Blocked**' if cat_block else 'Likely **Unblocked**'})"
    return num

def blocksi(domain: str) -> str | int:
    try:
        r = requests.get(f"https://service1.blocksi.net/getRating.json?url={domain}").json()
        if "Category" in r:
            return blocksi_categorize(int(r["Category"]))
        return "No category found"
    except Exception as e:
        return f"Error: {e}"

# Unified function
def check_url_blocking(url: str) -> dict:
    return {
        "lightspeed": lightspeed(url),
        "fortiguard": fortiguard(url),
        "palo_alto": palo(url),
        "blocksi": blocksi(url)
    }

# Example usage
if __name__ == "__main__":
    url = "wardellcurry.franchisecandidates.com"
    results = check_url_blocking(url)
    print(json.dumps(results, indent=2))


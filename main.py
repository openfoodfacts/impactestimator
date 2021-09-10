from fastapi import FastAPI
from impacts_estimation.impacts_estimation import estimate_impacts

import requests
import threading
import argparse
import logging
import uvicorn
import sys
import json
import time
import re
import urllib
                    

estimation_version = 1
impact_categories = ["EF single score",
                     "Climate change"]


logging = logging.getLogger("uvicorn.info")

parser = argparse.ArgumentParser(description="Start the impact estimator service.")
parser.add_argument("--productopener_base_url", help="Base URL to the productopener service")
parser.add_argument("--productopener_username", help="Username for the productopener service")
parser.add_argument("--productopener_password", help="Password for the productopener service")
parser.add_argument("--productopener_host_header", help="Host header in requests to avoid extra redirects in the responses")
args = parser.parse_args()

logging.info(f"Service starting with productopener_base_url {args.productopener_base_url}")


app = FastAPI()

stats = {
  "status": "off",
  "seen": 0,
  "estimate_impacts_success": 0,
  "estimate_impacts_failure": 0,
  "update_extended_data_success": 0,
  "update_extended_data_failure": 0,
  "errors": {},
}

def add_error(s):
    if not s in stats["errors"]:
        stats["errors"][s] = 0
    stats["errors"][s] += 1

def get_impact(barcode: str):
    product = get_product(barcode=barcode)["product"]

    impact_estimation_result = estimate_impacts(
            product=product,
            distributions_as_result=True,
            total_mass_used=100,
            impact_names=impact_categories)
    return impact_estimation_result

@app.get("/")
def read_root():
    return stats

@app.get("/impact/{barcode}")
def product_impact(barcode: str):
    return get_impact(barcode)

def prod_desc(prod):
    result = "(unnamed)"
    if "product_name" in prod:
        result = prod["product_name"].split("\n")[0]
    if "code" in prod:
        result = result + f" ({prod['code']})"
    return result

def get_products():
    url = (args.productopener_base_url +
            "api/v2/search?states_tags=en:ingredients-completed," +
            "en:nutrition-facts-completed&" +
            f"misc_tags=-en:ecoscore-extended-data-version-{estimation_version}&" +
            "fields=code,ingredients,nutriments,product_name&" +
            "page_size=20")
    logging.info(f"Looking for products using '{url}'")
    response = requests.get(url, headers={"Accept": "application/json", "Host": args.productopener_host_header})
    if response.status_code != 200:
        raise Exception(f"{url} -> {response.status_code}")
    js = json.loads(response.text)
    return js["products"]

def bsonify(m):
    res = {}
    for k in m:
        v = m[k]
        if isinstance(v, dict):
            v = bsonify(v)
        k = k.replace(".", "_").replace("$", "_")
        res[k] = v
    return res

def update_product(prod, decoration):
    decoration = bsonify(decoration)
    url = args.productopener_base_url + "cgi/product_jqm_multilingual.pl"
    params = {
        "user_id": args.productopener_username,
        "password": args.productopener_password,
        "code": prod["code"],
        "ecoscore_extended_data": json.dumps(decoration),
        "ecoscore_extended_data_version": estimation_version,
        }
    #logging.info(f'curl -v -H "Accept: application/json" -XPOST "{url}" --data-raw "{urllib.parse.urlencode(params)}"')
    response = requests.post(url, data=params, headers={"Accept": "application/json", "Host": args.productopener_host_header})
    if response.status_code == 200:
        try:
            js = json.loads(response.text)
            if js["status"] != 1:
                raise Exception(response.text)
        except json.JSONDecodeError:
            if response.text.find("Incorrect user name or password"):
                raise Exception("Incorrect user name or password")
            else:
                raise Exception("Response not valid JSON!")
    else:
        logging.info(f"Storing decoration for {prod_desc(prod)}: {response.text}!")
        logging.info(f"Problematic decoration: {decoration}")
        raise Exception(f"Status {response.status_code}")

def run_update_loop():
    stats["status"] = "on"
    try:
        logging.info("run_update_loop()")
        while True:
            products = get_products()
            logging.info(f"❤️  Found {len(products)} products to decorate")
            for prod in products:
                stats["seen"] += 1
                logging.info(f"Looking at {prod_desc(prod)}")
                decoration = {}
                try:
                    impact = estimate_impacts(
                            product=prod,
                            distributions_as_result=True,
                            total_mass_used=100,
                            impact_names=impact_categories)
                    logging.info(f"❤️  Computed {impact['impacts_geom_means']}") 
                    decoration["impact"] = impact
                    stats["estimate_impacts_success"] += 1
                except Exception as e:
                    error_desc = f"{e.__class__.__name__}: {e}"
                    logging.info(f"💀 get_impact([{prod_desc(prod)}]): {error_desc}")
                    decoration["error"] = error_desc
                    stats["estimate_impacts_failure"] += 1
                    add_error(error_desc)
                try:
                    update_product(prod, decoration)
                    logging.info(f"❤️  Stored decoration for {prod_desc(prod)}")
                    stats["update_extended_data_success"] += 1
                except Exception as e:
                    error_desc = f"{e.__class__.__name__}: {e}"
                    logging.info(f"💀 update_product(...): {error_desc}")
                    stats["update_extended_data_failure"] += 1
                    add_error(error_desc)
            time.sleep(30)
    finally:
        stats["status"] = "off"



@app.on_event("startup")
def startup():
    thread = threading.Thread(target=run_update_loop, args=())
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)


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
                    

estimation_version = 1
impact_categories = ["EF single score",
                     "Climate change"]


logging = logging.getLogger("uvicorn.info")

parser = argparse.ArgumentParser(description="Start the impact estimator service.")
parser.add_argument("--productopener_base_url", help="Base URL to the productopener service")
parser.add_argument("--productopener_username", help="Username for the productopener service")
parser.add_argument("--productopener_password", help="Password for the productopener service")
args = parser.parse_args()

logging.info(f"Service starting with productopener_base_url {args.productopener_base_url}")


app = FastAPI()

stats = {
  "seen": 0,
  "estimate_impacts_success": 0,
  "estimate_impacts_failure": 0,
  "update_extended_data_success": 0,
  "update_extended_data_failure": 0,
  "errors": {},
}

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
    return {
            "status": "running",
            "stats": stats,
            }

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

def run_update_loop():
    logging.info("run_update_loop()")
    while True:
        try:
            url = (args.productopener_base_url +
                    "api/v2/search?states=en:ingredients-completed," +
                    "en:nutrition-facts-completed&" +
                    f"misc_tags=-en:ecoscore-extended-data-version-{estimation_version}&fields=code,ingredients,nutriments,product_name")
            response = requests.get(url, headers={"Accept": "application/json"})
            if response.status_code != 200:
                raise Exception(f"{url} -> {response.status_code}")
            js = json.loads(response.text)
            logging.info(f"Found {len(js['products'])} products to decorate")
            for prod in js["products"]:
                stats["seen"] += 1
                logging.info(f"Found product {prod_desc(prod)}")
                decoration = {}
                try:
                    impact = estimate_impacts(
                            product=prod,
                            distributions_as_result=True,
                            total_mass_used=100,
                            impact_names=impact_categories)
                    logging.info(f"Found {impact['impacts_geom_means']}") 
                    decoration["impact"] = impact
                    stats["estimate_impacts_success"] += 1
                except Exception as e:
                    logging.info(f"get_impact([{prod_desc(prod)}]): {e}")
                    decoration["error"] = str(e)
                    stats["estimate_impacts_failure"] += 1
                    if not str(e) in stats["errors"]:
                        stats["errors"][str(e)] = 0
                    stats["errors"][str(e)] += 1
                url = args.productopener_base_url + "cgi/product_jqm_multilingual.pl"
                response = requests.post(url, data={
                    "user_id": args.productopener_username,
                    "password": args.productopener_password,
                    "code": prod["code"],
                    "ecoscore_extended_data": json.dumps(decoration),
                    "ecoscore_extended_data_version": estimation_version,
                    })
                if response.status_code == 200:
                    logging.info(f"Stored decoration for {prod_desc(prod)}")
                    stats["update_extended_data_success"] += 1
                else:
                    logging.info(f"Storing decoration for {prod_desc(prod)}: {response}!")
                    stats["update_extended_data_failure"] += 1
        except Exception as e:
            logging.info(f"run_update_loop(): {e}")
        time.sleep(30)


@app.on_event("startup")
def startup():
    thread = threading.Thread(target=run_update_loop, args=())
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)


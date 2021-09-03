from typing import Optional
from fastapi import FastAPI
from impacts_estimation.impacts_estimation import estimate_impacts
from openfoodfacts import get_product

import asyncio
import aiohttp
import argparse
import logging
import uvicorn
import sys
import json
                    

estimation_version = 1
impact_categories = ['EF single score',
                     'Climate change']


logging = logging.getLogger("uvicorn.info")

parser = argparse.ArgumentParser(description='Start the impact estimator service.')
parser.add_argument('--productopener_base_url', help='Base URL to the productopener service')
args = parser.parse_args()

logging.info(f"Service starting with productopener_base_url {args.productopener_base_url}")


app = FastAPI()


def get_impact(barcode: str):
    product = get_product(barcode=barcode)['product']

    impact_estimation_result = estimate_impacts(
            product=product,
            distributions_as_result=True,
            total_mass_used=100,
            impact_names=impact_categories)
    return impact_estimation_result

@app.get("/")
def read_root():
    return {"status": "running"}

@app.get("/impact/{barcode}")
def product_impact(barcode: str):
    return get_impact(barcode)

async def start_update_loop():
        logging.info("start_update_loop()")
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(args.productopener_base_url +
                            "/api/v2/search?states=en:ingredients-completed," +
                            "en:nutrition-facts-completed&" +
                            f"misc_tags=-en:ecoscore-extended-data-version-{estimation_version}&fields=code",
                            ssl=args.productopener_base_url.startswith("https")) as response:
                        text = await response.text()
                        js = json.loads(text)
                        for prod in js['products']:
                            logging.info(f"found product {prod['code']}")
                            impact = get_impact(prod['code'])
                            logging.info(f"Found {impact['impacts_geom_means']}") 
            except Exception as e:
                logging.info(f"start_update_loop(): {e}")
            await asyncio.sleep(30)


@app.on_event("startup")
def startup():
    asyncio.create_task(start_update_loop())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)


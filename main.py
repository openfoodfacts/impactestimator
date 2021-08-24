from typing import Optional
from fastapi import FastAPI
from impacts_estimation.impacts_estimation import estimate_impacts
from openfoodfacts import get_product


app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "running"}


@app.get("/impact/{barcode}")
def read_item(barcode: str):
    product = get_product(barcode=barcode)['product']
    impact_categories = ['EF single score',
                         'Climate change']

    impact_estimation_result = estimate_impacts(
            product=product,
            impact_names=impact_categories)
    return impact_estimation_result

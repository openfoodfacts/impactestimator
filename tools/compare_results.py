from impacts_estimation.impacts_estimation import estimate_impacts
from urllib.request import urlopen
import numpy as np
import json
import argparse
import sys
import progressbar


parser = argparse.ArgumentParser(description="Compare different results from impactestimator with ProductOpener default values.")
parser.add_argument("num_products", type=int, nargs="?", default=100, help="Number of top products to compare.")
args = parser.parse_args()

impact_categories = ['EF single score',
                     'Climate change']

top100 = json.loads(urlopen(f"https://world.openfoodfacts.org/api/v2/search?fields=code,product_name,ingredients,nutriments,ecoscore_data&page_size={args.num_products}").read())

result = []
for seen, prod in progressbar.progressbar(enumerate(top100["products"])):
    if "ecoscore_data" in prod:
        if "ingredients" in prod and len(prod["ingredients"]) > 0:
            if "agribalyse" in prod["ecoscore_data"]:
                agridata = prod["ecoscore_data"]["agribalyse"]
                if "name_en" in agridata:
                    po_ingredients_ary = []
                    for ingredient in prod["ingredients"]:
                        po_ingredients_ary.append(f"{ingredient['text']} ({ingredient['percent_estimate']}%)")
                    prod_result = {
                            "name": agridata["name_en"],
                            "po_ef_total": agridata["ef_total"],
                            "po_co2_total": agridata["co2_total"],
                            "po_ingredients": ", ".join(po_ingredients_ary),
                    }
                    try:
                        impact_estimation_result = estimate_impacts(
                                product=prod,
                                distributions_as_result=True,
                                impact_names=impact_categories)
                        prod_result["impes_mean_ef_total"] = impact_estimation_result["impacts_geom_means"]["EF single score"]
                        prod_result["impes_mean_co2_total"] = impact_estimation_result["impacts_geom_means"]["Climate change"]
                        likeliest_index = np.argmax(impact_estimation_result["confidence_score_distribution"])
                        prod_result["impes_likely_ef_total"] = impact_estimation_result["impact_distributions"]["EF single score"][likeliest_index]
                        prod_result["impes_likely_co2_total"] = impact_estimation_result["impact_distributions"]["Climate change"][likeliest_index]
                        impes_likely_ingredients_ary = []
                        for item in sorted(impact_estimation_result["recipes"][likeliest_index].items(), key=lambda item: item[1], reverse=True):
                            impes_likely_ingredients_ary.append(f"{item[0]} ({item[1]}%)")
                        prod_result["impes_likely_ingredients"] = ", ".join(impes_likely_ingredients_ary)
                    except Exception as e:
                        prod_result["impes_error"] = str(e)
                                
                    result.append(prod_result)

print(json.dumps(result, indent=4, sort_keys=True))


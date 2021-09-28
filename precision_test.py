import unittest

from impacts_estimation.impacts_estimation import estimate_impacts
import numpy as np
import json
import copy

PRODUCTS = [
        # https://ciqual.anses.fr/#/aliments/31032
        # https://agribalyse.ademe.fr/app/aliments/31032
        # https://world.openfoodfacts.org/api/v0/product/3017620422003.json?fields=code,product_name,ingredients,nutriments,ecoscore_data
        {
            "name": "Nutella",
            "prod": {
                "ingredients": [
                    {
                        "mass": 37.8,
                        "id": "en:condensed-milk",
                        "percent": 37.8,
                        "rank": 1
                    },
                    {
                        "mass": 28.7,
                        "id": "en:dark-chocolate",
                        "percent": 28.7,
                        "rank": 2
                    },
                    {
                        "mass": 18.8,
                        "id": "en:butter",
                        "percent": 18.8,
                        "rank": 3
                    },
                    {
                        "mass": 14.7,
                        "id": "en:beans",
                        "percent": 14.7,
                        "rank": 4
                    }
                ],
                "nutriments": {
                    "proteins_100g": 5.02,
                    "carbohydrates_100g": 57.9,
                    "fat_100g": 32.4,
                    "fiber_100g": 3.23,
                    "salt_100g": 0.12,
                    "sugars_100g": 56.2,
                    "saturated-fat_100g": 9.18
                },
            },
            "truth": {
                "impacts": {
                    "ef": 0.61477708,
                    "co2": 8.7770996,
                },
            },
        },
        # https://ciqual.anses.fr/#/aliments/11168/aioli-sauce-(garlic-and-olive-oil-mayonnaise)-prepacked
        # https://agribalyse.ademe.fr/app/aliments/11168
        # https://world.openfoodfacts.org/api/v0/product/3660603004828.json?fields=code,product_name,ingredients,nutriments,ecoscore_data
        {
            "name": "Aioli",
            "prod": {
                "ingredients": [
                    {
                        "mass": 72.8,
                        "id": "en:olive-oil",
                        "percent": 73.00441235459286,
                        "rank": 1
                    },
                    {
                        "mass": 10.8,
                        "id": "en:garlic",
                        "percent": 10.830324909747292,
                        "rank": 2
                    },
                    {
                        "mass": 8.290000000000001,
                        "id": "en:egg-yolk",
                        "percent": 8.313277176093061,
                        "rank": 3
                    },
                    {
                        "mass": 7.829999999999999,
                        "id": "en:lemon-juice",
                        "percent": 7.851985559566786,
                        "rank": 4
                    }
                ],
                "nutriments": {
                    "proteins_100g": 1.13,
                    "carbohydrates_100g": 4.7,
                    "fat_100g": 41.0,
                    "fiber_100g": 0.42,
                    "salt_100g": 1.85,
                    "sugars_100g": 3.14
                },
            },
            "truth": {
                "impacts": {
                    "ef": 0.4800103,
                    "co2": 1.1042559,
                },
            },
        },
]

DEFAULT_FORCE_TOTAL_MASS_USED=False
DEFAULT_USE_PERCENTAGES=False
DEFAULT_BREAK_FIRST_INGREDIENT=False

class TestPrecision(unittest.TestCase):
    def printPrecision(self, force_total_mass_used=DEFAULT_FORCE_TOTAL_MASS_USED, use_percentages=DEFAULT_USE_PERCENTAGES, break_first_ingredient=DEFAULT_BREAK_FIRST_INGREDIENT):
        for product in PRODUCTS:
            product_copy = copy.deepcopy(product)
            true_ingredients = {}
            for ingredient in product_copy["prod"]["ingredients"]:
                true_ingredients[ingredient["id"]] = ingredient["percent"]

            for idx, ingredient in enumerate(product_copy["prod"]["ingredients"]):
                if break_first_ingredient and idx == 0:
                    ingredient["id"] = "en:unicorn-droppings"
                if not use_percentages:
                    del ingredient["percent"]

            impact_categories = ['EF single score',
                    'Climate change']
            total_mass_used = None
            if force_total_mass_used:
                total_mass_used = 100
            impact_estimation_result = estimate_impacts(
                    seed=1,
                    product=product_copy["prod"],
                    distributions_as_result=True,
                    total_mass_used=total_mass_used,
                    impact_names=impact_categories)

            best_mixture_error_sum = 0.0
            best_mixture_idx = np.argmax(impact_estimation_result["confidence_score_distribution"])
            for ingredient, percentage in impact_estimation_result["recipes"][best_mixture_idx].items():
                error = percentage
                if ingredient in true_ingredients:
                    error = percentage - true_ingredients[ingredient]
                best_mixture_error_sum = error * error
            best_mixture_l2_error = best_mixture_error_sum ** 0.5
            # 10 * since impact_estimation_result is for 100g while the AgriBalyse impacts are for 1000g.
            estimated_ef = 10 * impact_estimation_result['impact_distributions']['EF single score'][best_mixture_idx]
            estimated_co2 = 10 * impact_estimation_result['impact_distributions']['Climate change'][best_mixture_idx]
            ef_error = abs(estimated_ef - product_copy['truth']['impacts']['ef']) / product_copy['truth']['impacts']['ef']
            co2_error = abs(estimated_co2 - product_copy['truth']['impacts']['co2']) / product_copy['truth']['impacts']['co2']
            print(f"   * Product: {product['name']}")
            print(f"     * Likeliest mixture L2: {best_mixture_l2_error}")
            print(f"     * Likeliest mixture EF error ratio: {ef_error}")
            print(f"     * Likeliest mixture CO2 error ratio: {co2_error}")

    def testSynthesisAndImpacts(self):
        print(f"Percentages: {DEFAULT_USE_PERCENTAGES}, first ingredient unknown: {DEFAULT_BREAK_FIRST_INGREDIENT}")
        for force_total_mass_used in [True, False]:
            print(f" * Force total mass used to 100g: {force_total_mass_used}")
            self.printPrecision(force_total_mass_used=force_total_mass_used)
        print(f"First ingredient unknown: {DEFAULT_BREAK_FIRST_INGREDIENT}, force total mass used to 100g: {DEFAULT_FORCE_TOTAL_MASS_USED}")
        for use_percentages in [True, False]:
            print(f" * Percentages: {use_percentages}")
            self.printPrecision(use_percentages=use_percentages)
        print(f"Force total mass used to 100g: {DEFAULT_FORCE_TOTAL_MASS_USED}, percentages: {DEFAULT_USE_PERCENTAGES}")
        for break_first_ingredient in [True, False]:
            print(f" * First ingredient unknown: {break_first_ingredient}")
            self.printPrecision(break_first_ingredient=break_first_ingredient)


if __name__ == '__main__':
    unittest.main()

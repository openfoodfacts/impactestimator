import unittest

from impacts_estimation.impacts_estimation import estimate_impacts
import numpy as np
import json


class TestEstimation(unittest.TestCase):
    for testCase in [
            # https://ciqual.anses.fr/#/aliments/11168/aioli-sauce-(garlic-and-olive-oil-mayonnaise)-prepacked
            # https://agribalyse.ademe.fr/app/aliments/11168#Sauce_a%C3%AFoli,_pr%C3%A9emball%C3%A9e
            {
                "name": "Aioli with ingredients with percentages",
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
                        },
                    ],
                    "impacts": {
                        "co2": 0.59,
                        "ef": 1.97,
                    },
                },
            },
            # https://ciqual.anses.fr/#/aliments/11168/aioli-sauce-(garlic-and-olive-oil-mayonnaise)-prepacked
            # https://agribalyse.ademe.fr/app/aliments/11168#Sauce_a%C3%AFoli,_pr%C3%A9emball%C3%A9e
            {
                "name": "Aioli with ingredients without percentages",
                "prod": {
                    "ingredients": [
                        {
                            "mass": 72.8,
                            "id": "en:olive-oil",
                            "rank": 1
                        },
                        {
                            "mass": 10.8,
                            "id": "en:garlic",
                            "rank": 2
                        },
                        {
                            "mass": 8.290000000000001,
                            "id": "en:egg-yolk",
                            "rank": 3
                        },
                        {
                            "mass": 7.829999999999999,
                            "id": "en:lemon-juice",
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
                        },
                    ],
                    "impacts": {
                        "co2": 0.59,
                        "ef": 1.97,
                    },
                },
            },
        ]:
        true_ingredients = {}
        for ingredient in testCase["truth"]["ingredients"]:
            true_ingredients[ingredient["id"]] = ingredient["percent"]

        impact_categories = ['EF single score',
                'Climate change']
        impact_estimation_result = estimate_impacts(
                product=testCase["prod"],
                distributions_as_result=True,
                total_mass_used=100,
                impact_names=impact_categories)

        best_mixture_error_sum = 0.0
        best_mixture_idx = np.argmax(impact_estimation_result["confidence_score_distribution"])
        for ingredient, percentage in impact_estimation_result["recipes"][best_mixture_idx].items():
            error = percentage
            if ingredient in true_ingredients:
                error = percentage - true_ingredients[ingredient]
            best_mixture_error_sum = error * error
        print(f"*** {testCase['name']} ***")
        print(f"ingredient L2 error: {best_mixture_error_sum ** 0.5}")
        print("real")
        print(json.dumps(true_ingredients, indent=4, sort_keys=True))
        print("estimated")
        print(json.dumps(impact_estimation_result["recipes"][best_mixture_idx], indent=4, sort_keys=True))
        # 10 * since impact_estimation_result is for 100g while the AgriBalyse impacts are for 1000g.
        estimated_ef = 10 * impact_estimation_result['impact_distributions']['EF single score'][best_mixture_idx]
        estimated_co2 = 10 * impact_estimation_result['impact_distributions']['Climate change'][best_mixture_idx]
        print(f"abs(estimated ef {estimated_ef} - true ef {testCase['truth']['impacts']['ef']}) = {abs(estimated_ef - testCase['truth']['impacts']['ef'])}")
        print(f"abs(estimated co2 {estimated_co2} - true co2 {testCase['truth']['impacts']['co2']}) = {abs(estimated_co2 - testCase['truth']['impacts']['co2'])}")
            



if __name__ == '__main__':
    unittest.main()

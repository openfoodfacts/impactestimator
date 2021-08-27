import unittest

from impacts_estimation.impacts_estimation import estimate_impacts
import numpy as np
import json


class TestEstimation(unittest.TestCase):
    def testSynthesisAndImpacts(self):
        for test_case in [
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
                            "ef": 0.4800103,
                            "co2": 1.1042559,
                        },
                    },
                },
        ]:
            for use_percentages in [True, False]:
                true_ingredients = {}
                for ingredient in test_case["truth"]["ingredients"]:
                    true_ingredients[ingredient["id"]] = ingredient["percent"]

                if not use_percentages:
                    for ingredient in test_case["prod"]["ingredients"]:
                        del ingredient["percent"]

                impact_categories = ['EF single score',
                        'Climate change']
                impact_estimation_result = estimate_impacts(
                        product=test_case["prod"],
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
                best_mixture_l2_error = best_mixture_error_sum ** 0.5
                # 10 * since impact_estimation_result is for 100g while the AgriBalyse impacts are for 1000g.
                estimated_ef = 10 * impact_estimation_result['impact_distributions']['EF single score'][best_mixture_idx]
                estimated_co2 = 10 * impact_estimation_result['impact_distributions']['Climate change'][best_mixture_idx]
                ef_error = abs(estimated_ef - test_case['truth']['impacts']['ef']) / test_case['truth']['impacts']['ef']
                co2_error = abs(estimated_co2 - test_case['truth']['impacts']['co2']) / test_case['truth']['impacts']['co2']
                if use_percentages:
                    self.assertLess(best_mixture_l2_error, 0.01)
                    self.assertLess(ef_error, 0.1)
                    self.assertLess(co2_error, 0.1)
                else:
                    self.assertLess(best_mixture_l2_error, 50.0)
                    self.assertLess(ef_error, 0.5)
                    self.assertLess(co2_error, 0.5)


if __name__ == '__main__':
    unittest.main()

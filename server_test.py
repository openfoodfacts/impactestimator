from fastapi import FastAPI, Request

import uvicorn
import unittest
import threading
import time
import logging
import requests

import server


mock = FastAPI()

logging=logging.getLogger("uvicorn.info")

search_responses = []
updated_products = []
expected_host_header = "a_host_header"
expected_username = "a_username"
expected_password = "a_password"

@mock.get("/api/v2/search")
def api_v2_search(request: Request):
    global expected_host_header
    global search_responses
    if request.headers["host"] != expected_host_header:
        raise Exception("Wrong host header")
    if len(search_responses) == 0:
        return {
                "products": [],
                }
    else:
        resp = search_responses.pop(0)
        return {
                "products": resp,
                }

@mock.post("/cgi/product_jqm_multilingual.pl")
async def product_jqm_multilingual(request: Request):
    global updated_products
    global expected_host_header
    global expected_username
    global expected_password
    if request.headers["host"] != expected_host_header:
        raise Exception("Wrong host header")
    form = await request.form()
    if form["user_id"] != expected_username:
        raise Exception("Wrong username")
    if form["password"] != expected_password:
        raise Exception("Wrong password")
    if not "code" in form:
        raise Exception("Missing code")
    if not "ecoscore_extended_data" in form:
        raise Exception("Missing ecoscore_extended_data")
    if not "ecoscore_extended_data_version" in form:
        raise Exception("Missing ecoscore_extended_data_version")
    updated_products.append(form["code"])
    return {"status": 1}


@mock.get("/started")
def started():
    return True

class TestServer(unittest.TestCase):

    def testUpdateLoop(self):
        global search_responses
        global updated_products
        serv = server.Server(
                productopener_base_url="http://localhost:8000/",
                productopener_host_header=expected_host_header,
                productopener_username=expected_username,
                productopener_password=expected_password)
        search_responses = [[
	{
		"code": "3920291118574",
		"ingredients": [
			{
				"id": "en:milk",
				"origins": "en:france",
				"percent_estimate": 56.25,
				"percent_max": 100,
				"percent_min": 12.5,
				"text": "lait",
				"vegan": "no",
				"vegetarian": "yes"
			},
			{
				"id": "en:cow",
				"percent_estimate": 21.875,
				"percent_max": 50,
				"percent_min": 0,
				"processing": "en:pasteurised",
				"text": "de vache"
			},
			{
				"id": "en:salt",
				"percent_estimate": 10.9375,
				"percent_max": 33.3333333333333,
				"percent_min": 0,
				"text": "sel",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:ferment",
				"percent_estimate": 5.46875,
				"percent_max": 25,
				"percent_min": 0,
				"text": "ferments",
				"vegan": "maybe",
				"vegetarian": "maybe"
			},
			{
				"id": "fr:colorant-de-la-croute",
				"ingredients": [
					{
						"id": "fr:Grasse 29 annatto",
						"percent_estimate": 2.734375,
						"percent_max": 20,
						"percent_min": 0,
						"text": "Grasse 29 annatto"
					}
				],
				"percent_estimate": 2.734375,
				"percent_max": 20,
				"percent_min": 0,
				"text": "colorants de croûte"
			},
			{
				"id": "en:e150",
				"percent_estimate": 1.3671875,
				"percent_max": 16.6666666666667,
				"percent_min": 0,
				"text": "caramel",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "fr:Croûte consommable",
				"percent_estimate": 0.68359375,
				"percent_max": 14.2857142857143,
				"percent_min": 0,
				"text": "Croûte consommable"
			},
			{
				"id": "fr:saturés 21 Conditionné sous atmosphère protectrice",
				"percent_estimate": 0.68359375,
				"percent_max": 12.5,
				"percent_min": 0,
				"text": "saturés 21 Conditionné sous atmosphère protectrice"
			}
		],
		"nutriments": {
			"carbohydrates": 0.5,
			"carbohydrates_100g": 0.5,
			"carbohydrates_unit": "",
			"carbohydrates_value": 0.5,
			"energy": 1510,
			"energy-kcal": 361,
			"energy-kcal_100g": 361,
			"energy-kcal_unit": "kcal",
			"energy-kcal_value": 361,
			"energy_100g": 1510,
			"energy_unit": "kcal",
			"energy_value": 361,
			"fat": 29,
			"fat_100g": 29,
			"fat_unit": "",
			"fat_value": 29,
			"fruits-vegetables-nuts-estimate-from-ingredients_100g": 0,
			"nova-group": 4,
			"nova-group_100g": 4,
			"nova-group_serving": 4,
			"proteins": 25,
			"proteins_100g": 25,
			"proteins_unit": "",
			"proteins_value": 25,
			"salt": 1.4,
			"salt_100g": 1.4,
			"salt_unit": "",
			"salt_value": 1.4,
			"saturated-fat": 21,
			"saturated-fat_100g": 21,
			"saturated-fat_unit": "",
			"saturated-fat_value": 21,
			"sodium": 0.56,
			"sodium_100g": 0.56,
			"sodium_unit": "g",
			"sodium_value": 0.56,
			"sugars": 0.5,
			"sugars_100g": 0.5,
			"sugars_unit": "",
			"sugars_value": 0.5
		},
		"product_name": "Extra fines classic"
	},
	{
		"code": "3925359000501",
		"ingredients": [
			{
				"id": "en:water",
				"percent_estimate": 63.25,
				"percent_max": 85,
				"percent_min": 41.5,
				"text": "eau",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:concentrated-juice",
				"ingredients": [
					{
						"id": "fr:citron 35,5 % et",
						"percent_estimate": 20.875,
						"percent_max": 45,
						"percent_min": 5,
						"text": "citron 35.5% et"
					}
				],
				"percent_estimate": 20.875,
				"percent_max": 45,
				"percent_min": 5,
				"text": "jus à base de concentré"
			},
			{
				"id": "en:orange",
				"percent": 4.5,
				"percent_estimate": 4.5,
				"percent_max": 4.5,
				"percent_min": 5,
				"text": "orange",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:lemon-pulpe",
				"percent": 5,
				"percent_estimate": 5,
				"percent_max": 4.5,
				"percent_min": 5,
				"text": "pulpe de citron",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:acid",
				"ingredients": [
					{
						"id": "en:e330",
						"percent_estimate": 2.25,
						"percent_max": 4.5,
						"percent_min": 0,
						"text": "acide citrique",
						"vegan": "yes",
						"vegetarian": "yes"
					},
					{
						"id": "fr:extrait-naturel-de-citron",
						"percent_estimate": 4.125,
						"percent_max": 2.25,
						"percent_min": 0,
						"text": "extrait naturel de citron",
						"vegan": "yes",
						"vegetarian": "yes"
					}
				],
				"percent_estimate": 6.375,
				"percent_max": 4.5,
				"percent_min": 0,
				"text": "acidifiant"
			}
		],
		"nutriments": {
			"carbohydrates": 1.6,
			"carbohydrates_100g": 1.6,
			"carbohydrates_unit": "",
			"carbohydrates_value": 1.6,
			"carbon-footprint-from-known-ingredients_100g": 5.1,
			"energy": 96,
			"energy-kcal": 23,
			"energy-kcal_100g": 23,
			"energy-kcal_unit": "kcal",
			"energy-kcal_value": 23,
			"energy_100g": 96,
			"energy_unit": "kcal",
			"energy_value": 23,
			"fat": 0,
			"fat_100g": 0,
			"fat_unit": "",
			"fat_value": 0,
			"fruits-vegetables-nuts-estimate-from-ingredients_100g": 9.5,
			"nova-group": 1,
			"nova-group_100g": 1,
			"nova-group_serving": 1,
			"nutrition-score-fr": 5,
			"nutrition-score-fr_100g": 5,
			"proteins": 0.2,
			"proteins_100g": 0.2,
			"proteins_unit": "",
			"proteins_value": 0.2,
			"salt": 0.01,
			"salt_100g": 0.01,
			"salt_unit": "",
			"salt_value": 0.01,
			"saturated-fat": 0,
			"saturated-fat_100g": 0,
			"saturated-fat_unit": "",
			"saturated-fat_value": 0,
			"sodium": 0.004,
			"sodium_100g": 0.004,
			"sodium_unit": "g",
			"sodium_value": 0.004,
			"sugars": 0.8,
			"sugars_100g": 0.8,
			"sugars_unit": "",
			"sugars_value": 0.8
		},
		"product_name": "Pulco citron"
	},
	{
		"code": "3927783004056",
		"ingredients": [
			{
				"id": "en:All flavors contain",
				"ingredients": [
					{
						"id": "en:sugar",
						"percent_estimate": 52.3809523809524,
						"percent_max": 100,
						"percent_min": 4.76190476190476,
						"text": "sugar",
						"vegan": "yes",
						"vegetarian": "yes"
					}
				],
				"percent_estimate": 52.3809523809524,
				"percent_max": 100,
				"percent_min": 4.76190476190476,
				"text": "All flavors contain"
			},
			{
				"id": "en:additionally",
				"ingredients": [
					{
						"id": "en:original",
						"percent_estimate": 23.8095238095238,
						"percent_max": 50,
						"percent_min": 0,
						"text": "original"
					}
				],
				"percent_estimate": 23.8095238095238,
				"percent_max": 50,
				"percent_min": 0,
				"text": "additionally"
			},
			{
				"id": "en:gum-base",
				"percent_estimate": 11.9047619047619,
				"percent_max": 33.3333333333333,
				"percent_min": 0,
				"text": "gum base"
			},
			{
				"id": "en:glucose-syrup",
				"percent_estimate": 5.95238095238095,
				"percent_max": 25,
				"percent_min": 0,
				"text": "glucose syrup",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:natural &artificial flavors",
				"percent_estimate": 2.97619047619047,
				"percent_max": 20,
				"percent_min": 0,
				"text": "natural &artificial flavors"
			},
			{
				"id": "en:glycerine citric acid",
				"percent_estimate": 1.48809523809524,
				"percent_max": 16.6666666666667,
				"percent_min": 0,
				"text": "glycerine citric acid"
			},
			{
				"id": "en:e171",
				"percent_estimate": 0.74404761904762,
				"percent_max": 14.2857142857143,
				"percent_min": 0,
				"text": "titanium dioxide",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e321",
				"ingredients": [
					{
						"id": "en:preservative",
						"percent_estimate": 0.37202380952381,
						"percent_max": 12.5,
						"percent_min": 0,
						"text": "preservative"
					}
				],
				"percent_estimate": 0.37202380952381,
				"percent_max": 12.5,
				"percent_min": 0,
				"text": "bht",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e129",
				"percent_estimate": 0.186011904761905,
				"percent_max": 11.1111111111111,
				"percent_min": 0,
				"text": "red 40 lake",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e129",
				"percent_estimate": 0.093005952380949,
				"percent_max": 10,
				"percent_min": 0,
				"text": "red 40",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:blue raspberry",
				"ingredients": [
					{
						"id": "en:glucose-syrup",
						"percent_estimate": 0.0465029761904745,
						"percent_max": 9.09090909090909,
						"percent_min": 0,
						"text": "glucose syrup",
						"vegan": "yes",
						"vegetarian": "yes"
					}
				],
				"percent_estimate": 0.0465029761904745,
				"percent_max": 9.09090909090909,
				"percent_min": 0,
				"text": "blue raspberry"
			},
			{
				"id": "en:gum-base",
				"percent_estimate": 0.0232514880952408,
				"percent_max": 8.33333333333333,
				"percent_min": 0,
				"text": "gum base"
			},
			{
				"id": "en:artificial-flavouring",
				"percent_estimate": 0.0116257440476204,
				"percent_max": 7.69230769230769,
				"percent_min": 0,
				"text": "artificial flavors",
				"vegan": "maybe",
				"vegetarian": "maybe"
			},
			{
				"id": "en:e330",
				"percent_estimate": 0.0058128720238102,
				"percent_max": 7.14285714285714,
				"percent_min": 0,
				"text": "citric acid",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e422",
				"percent_estimate": 0.0029064360119051,
				"percent_max": 6.66666666666667,
				"percent_min": 0,
				"text": "glycerine",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e296",
				"percent_estimate": 0.001453218005949,
				"percent_max": 6.25,
				"percent_min": 0,
				"text": "malic acid",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e951",
				"percent_estimate": 0.000726609002974499,
				"percent_max": 5.88235294117647,
				"percent_min": 0,
				"text": "aspartame",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e133",
				"percent_estimate": 0.000363304501490802,
				"percent_max": 5.55555555555556,
				"percent_min": 0,
				"text": "blue 1 lake",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e950",
				"percent_estimate": 0.000181652250745401,
				"percent_max": 5.26315789473684,
				"percent_min": 0,
				"text": "acesulfame potassium",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e171",
				"percent_estimate": 0.0000908261253727005,
				"percent_max": 5,
				"percent_min": 0,
				"text": "titanium dioxide",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:e321",
				"ingredients": [
					{
						"id": "en:preservative",
						"percent_estimate": 0.0000908261253727005,
						"percent_max": 4.76190476190476,
						"percent_min": 0,
						"text": "preservative"
					}
				],
				"percent_estimate": 0.0000908261253727005,
				"percent_max": 4.76190476190476,
				"percent_min": 0,
				"text": "bht",
				"vegan": "yes",
				"vegetarian": "yes"
			}
		],
		"nutriments": {
			"carbohydrates": 83.33,
			"carbohydrates_100g": 83.33,
			"carbohydrates_serving": 5,
			"carbohydrates_unit": "g",
			"carbohydrates_value": 83.33,
			"energy": 1393,
			"energy-kcal": 333,
			"energy-kcal_100g": 333,
			"energy-kcal_serving": 20,
			"energy-kcal_unit": "kcal",
			"energy-kcal_value": 333,
			"energy_100g": 1393,
			"energy_serving": 83.6,
			"energy_unit": "kcal",
			"energy_value": 333,
			"fat": 0,
			"fat_100g": 0,
			"fat_serving": 0,
			"fat_unit": "g",
			"fat_value": 0,
			"fruits-vegetables-nuts-estimate-from-ingredients_100g": 0,
			"nova-group": 4,
			"nova-group_100g": 4,
			"nova-group_serving": 4,
			"proteins": 0,
			"proteins_100g": 0,
			"proteins_serving": 0,
			"proteins_unit": "g",
			"proteins_value": 0,
			"salt": 0,
			"salt_100g": 0,
			"salt_serving": 0,
			"salt_unit": "mg",
			"salt_value": 0,
			"sodium": 0,
			"sodium_100g": 0,
			"sodium_serving": 0,
			"sodium_unit": "mg",
			"sodium_value": 0,
			"sugars": 66.67,
			"sugars_100g": 66.67,
			"sugars_serving": 4,
			"sugars_unit": "g",
			"sugars_value": 66.67,
			"trans-fat": 0,
			"trans-fat_100g": 0,
			"trans-fat_serving": 0,
			"trans-fat_unit": "g",
			"trans-fat_value": 0
		},
		"product_name": "Bubble Gum, Original & Blue Razz"
	},
	{
		"code": "3933420002521",
		"ingredients": [
			{
				"id": "fr:YAOURT NATURE",
				"percent": 125,
				"percent_estimate": 100,
				"percent_max": 100,
				"percent_min": 125,
				"text": "YAOURT NATURE"
			}
		],
		"nutriments": {
			"carbohydrates": 5.3,
			"carbohydrates_100g": 5.3,
			"carbohydrates_unit": "",
			"carbohydrates_value": 5.3,
			"energy": 192,
			"energy-kcal": 46,
			"energy-kcal_100g": 46,
			"energy-kcal_unit": "kcal",
			"energy-kcal_value": 46,
			"energy_100g": 192,
			"energy_unit": "kcal",
			"energy_value": 46,
			"fat": 1,
			"fat_100g": 1,
			"fat_unit": "",
			"fat_value": 1,
			"fruits-vegetables-nuts-estimate-from-ingredients_100g": 0,
			"proteins": 4,
			"proteins_100g": 4,
			"proteins_unit": "",
			"proteins_value": 4,
			"salt": 0.15,
			"salt_100g": 0.15,
			"salt_unit": "",
			"salt_value": 0.15,
			"saturated-fat": 0.6,
			"saturated-fat_100g": 0.6,
			"saturated-fat_unit": "",
			"saturated-fat_value": 0.6,
			"sodium": 0.06,
			"sodium_100g": 0.06,
			"sodium_unit": "g",
			"sodium_value": 0.06,
			"sugars": 5.3,
			"sugars_100g": 5.3,
			"sugars_unit": "",
			"sugars_value": 5.3
		},
		"product_name": "Yaourt nature"
	},
	{
		"code": "3946220363310",
		"ingredients": [
			{
				"id": "en:potato",
				"origins": "en:france",
				"percent": 64,
				"percent_estimate": 64,
				"percent_max": 64,
				"percent_min": 64,
				"text": "Pommes de terre",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"from_palm_oil": "no",
				"id": "en:sunflower-oil",
				"percent": 34,
				"percent_estimate": 34,
				"percent_max": 34,
				"percent_min": 34,
				"text": "huile de tournesol",
				"vegan": "yes",
				"vegetarian": "yes"
			},
			{
				"id": "en:salt",
				"percent_estimate": 2,
				"percent_max": 2,
				"percent_min": 2,
				"text": "sel",
				"vegan": "yes",
				"vegetarian": "yes"
			}
		],
		"nutriments": {
			"carbohydrates": 5.1,
			"carbohydrates_100g": 5.1,
			"carbohydrates_unit": "g",
			"carbohydrates_value": 5.1,
			"carbon-footprint-from-known-ingredients_100g": 126.8,
			"energy": 2310,
			"energy-kcal": 552,
			"energy-kcal_100g": 552,
			"energy-kcal_unit": "kcal",
			"energy-kcal_value": 552,
			"energy_100g": 2310,
			"energy_unit": "kcal",
			"energy_value": 552,
			"fat": 35,
			"fat_100g": 35,
			"fat_unit": "g",
			"fat_value": 35,
			"fiber": 4.2,
			"fiber_100g": 4.2,
			"fiber_unit": "g",
			"fiber_value": 4.2,
			"fruits-vegetables-nuts-estimate-from-ingredients_100g": 0,
			"nova-group": 3,
			"nova-group_100g": 3,
			"nova-group_serving": 3,
			"nutrition-score-fr": 9,
			"nutrition-score-fr_100g": 9,
			"proteins": 6.2,
			"proteins_100g": 6.2,
			"proteins_unit": "g",
			"proteins_value": 6.2,
			"salt": 1.1,
			"salt_100g": 1.1,
			"salt_unit": "g",
			"salt_value": 1.1,
			"saturated-fat": 3.2,
			"saturated-fat_100g": 3.2,
			"saturated-fat_unit": "g",
			"saturated-fat_value": 3.2,
			"sodium": 0.44,
			"sodium_100g": 0.44,
			"sodium_unit": "g",
			"sodium_value": 0.44,
			"sugars": 0.7,
			"sugars_100g": 0.7,
			"sugars_unit": "g",
			"sugars_value": 0.7
		},
		"product_name": "Chips paysannes nature"
	}]]
        product_codes = {}
        for prod in search_responses[0]:
            product_codes[prod["code"]] = True
        num_products = len(search_responses[0])
        serv.start_update_loop()
        while len(updated_products) < num_products:
            time.sleep(0.2)
        serv.stop_update_loop()
        for code in updated_products:
            del(product_codes[code])
        assert(len(product_codes) == 0)


if __name__ == "__main__":
    thread = threading.Thread(target=uvicorn.run, args=(mock,), kwargs={"host": "0.0.0.0", "port": 8000, "log_level": "info", "reload": False})
    thread.daemon = True
    thread.start()
    started = False
    while not started:
        try:
            requests.get("http://localhost:8000/started")
            started = True
        except:
            time.sleep(0.2)
    unittest.main()

import requests
import logging
import sys
import json
import time
import re
import urllib
import threading
import multiprocessing
import queue
import numpy as np
                    
ctx = multiprocessing.get_context("forkserver")

class Server:
    def __init__(self,
                 logging=logging.getLogger("uvicorn.info"),
                 productopener_base_url=None,
                 productopener_host_header=None,
                 productopener_basic_auth_username="",
                 productopener_basic_auth_password="",
                 productopener_username=None,
                 productopener_password=None):
        self.logging = logging
        self.productopener_base_url = productopener_base_url
        self.productopener_host_header = productopener_host_header
        self.productopener_username = productopener_username
        self.productopener_password = productopener_password
        self.auth = None
        if productopener_basic_auth_username != "" and productopener_basic_auth_password != "":
            self.auth = requests.auth.HTTPBasicAuth(productopener_basic_auth_username, productopener_basic_auth_password)
        self.estimation_version = 4
        self.impact_categories = ["EF single score",
                                  "Climate change"]
        self.stats = {
                "status": "off",
                "seen": 0,
                "estimate_impacts_success": 0,
                "estimate_impacts_failure": 0,
                "update_extended_data_success": 0,
                "update_extended_data_failure": 0,
                "errors": {},
                }

    def _add_error(self, s):
        if not s in self.stats["errors"]:
            self.stats["errors"][s] = 0
        self.stats["errors"][s] += 1

    def _prod_desc(self, prod):
        result = "(unnamed)"
        if "product_name" in prod:
            result = prod["product_name"].split("\n")[0]
        if "code" in prod:
            result = result + f" ({prod['code']})"
        return result

    def _get_products(self):
        url = (self.productopener_base_url +
                "api/v2/search?states_tags=en:ingredients-completed," +
                "en:nutrition-facts-completed&" +
                f"misc_tags=-en:ecoscore-extended-data-version-{self.estimation_version}&" +
                "fields=code,ingredients,nutriments,product_name&" +
                "page_size=20&" +
                "sort_by=nothing&" +
                "no_count=1&" +
                "no_cache=1")
        if self.auth is not None:
            self.logging.info(f"Looking for products using '{url}' with [{self.auth.username}/{self.auth.password[:2]}...]")
        else:
            self.logging.info(f"Looking for products using '{url}'")
        headers = {"Accept": "application/json"}
        if self.productopener_host_header not in ["-", ""]:
            headers["Host"] = self.productopener_host_header
        response = requests.get(url, headers=headers, auth=self.auth)
        if response.status_code != 200:
            raise Exception(f"{url} -> {response.status_code}")
        js = json.loads(response.text)
        return js["products"]

    def _bsonify(self, m):
        if isinstance(m, dict):
            res = {}
            for k in m:
                v = self._bsonify(m[k])
                k = re.sub(r'[^:-_a-zA-Z0-9]', '_', k)
                res[k] = v
            return res
        elif isinstance(m, list):
            res = []
            for e in m:
                res.append(self._bsonify(e))
            return res
        elif isinstance(m, tuple):
            res = []
            for e in m:
                res.append(self._bsonify(e))
            return tuple(res)
        else:
            return m
            

    def _update_product(self, prod, decoration):
        decoration = self._bsonify(decoration)
        url = self.productopener_base_url + "cgi/product_jqm_multilingual.pl"
        params = {
                "user_id": self.productopener_username,
                "password": self.productopener_password,
                "code": prod["code"],
                "ecoscore_extended_data": json.dumps(decoration),
                "ecoscore_extended_data_version": self.estimation_version,
                }
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        if self.productopener_host_header not in ["-", ""]:
            headers["Host"] = self.productopener_host_header
        response = requests.post(url, data=params, headers=headers, auth=self.auth)
        if response.status_code == 200:
            try:
                js = json.loads(response.text)
                if js["status"] != 1:
                    raise Exception(response.text)
            except json.JSONDecodeError:
                if response.text.find("Incorrect user name or password") != -1:
                    raise Exception(f"Incorrect user name or password ({self.productopener_username}/{self.productopener_password[:2]}...)")
                else:
                    raise Exception("Response not valid JSON!")
        else:
            self.logging.info(f"Storing decoration for {self._prod_desc(prod)}: {response.text}")
            self.logging.info(f"Problematic decoration: {decoration}")
            raise Exception(f"Status {response.status_code}")

    def stop_update_loop(self):
        self.stats["status"] = "stopping"

    def start_update_loop(self):
        thread = threading.Thread(target=self._run_update_loop, args=())
        thread.daemon = True
        thread.start()

    def _estimate_outside_process(self, product, queue):
        """This function runs in a separate process, and communicates with the parent
        through the provided queue. The queue must get a tuple of (result, exception-string)
        when this function terminates."""
        try:
            from impacts_estimation.impacts_estimation import estimate_impacts
            impact = estimate_impacts(
                    ignore_unknown_ingredients=False,
                    product=product,
                    distributions_as_result=True,
                    impact_names=self.impact_categories)
            queue.put((impact, None))
        except Exception as e:
            queue.put((None, f"{e.__class__.__name__}: {e}"))

    def _estimate_with_deadline(self, product, deadline=600):
        """This function starts _estimate_outside_process in a separate process, giving
        it a queue to return a (result, exception-string) through.
        The process can time out, and the queue can be empty - both need to provide
        exceptions in addition to anything received via the queue."""
        q = ctx.Queue(1)
        p = ctx.Process(target=self._estimate_outside_process, args=(product, q))
        results = (None, "no results yet")
        try:
            p.start()
            self.logging.info(f"🍴 Forked {p.pid} to compute estimation")
            try:
                results = q.get(block=True, timeout=deadline)
                if results[1]:
                    raise Exception(f"estimation process got exception: {results[1]}")
                return results[0]
            except queue.Empty:
                raise Exception(f"estimation process timed out after {deadline} seconds")
            except Exception as e:
                raise Exception(f"estimation queue read: {e.__class__.__name__}: {e}")
        finally:
            p.kill()
            p.join()
            p.close()


    def _run_update_loop(self):
        self.stats["status"] = "on"
        try:
            self.logging.info("run_update_loop()")
            while self.stats["status"] == "on":
                try:
                    products = self._get_products()
                    self.logging.info(f"❤️  Found {len(products)} products to decorate")
                    for prod in products:
                        self.stats["seen"] += 1
                        self.logging.info(f"Looking at {self._prod_desc(prod)}")
                        decoration = {}
                        try:
                            impact = self._estimate_with_deadline(prod)
                            self.logging.info(f"❤️  Computed {impact['impacts_geom_means']}") 
                            max_confidence_idx = np.argmax(impact['confidence_score_distribution'])
                            decoration["impact"] = {
                                    "likeliest_recipe": impact['recipes'][max_confidence_idx],
                                    "likeliest_impacts": {
                                        "Climate change": impact['impact_distributions']['Climate change'][max_confidence_idx],
                                        "EF single score": impact['impact_distributions']['EF single score'][max_confidence_idx],
                                    },
                                    "ef_single_score_log_stddev": np.std(np.log(impact['impact_distributions']['EF single score'])),
                                    "mass_ratio_uncharacterized": impact['uncharacterized_ingredients_mass_proportion']['impact'],
                                    "uncharacterized_ingredients": impact['uncharacterized_ingredients'],
                                    "uncharacterized_ingredients_mass_proportion": impact['uncharacterized_ingredients_mass_proportion'],
                                    "uncharacterized_ingredients_ratio": impact['uncharacterized_ingredients_ratio'],
                                    "warnings": impact['warnings'],
                            }
                            self.stats["estimate_impacts_success"] += 1
                        except Exception as e:
                            error_desc = f"{e.__class__.__name__}: {e}"
                            self.logging.info(f"💀 get_impact([{self._prod_desc(prod)}]): {error_desc}")
                            decoration["error"] = error_desc
                            self.stats["estimate_impacts_failure"] += 1
                            self._add_error(error_desc)
                        try:
                            self._update_product(prod, decoration)
                            self.logging.info(f"❤️  Stored decoration for {self._prod_desc(prod)}")
                            self.stats["update_extended_data_success"] += 1
                        except Exception as e:
                            error_desc = f"{e.__class__.__name__}: {e}"
                            self.logging.info(f"💀 update_product(...): {error_desc}")
                            self.stats["update_extended_data_failure"] += 1
                            self._add_error(error_desc)
                    time.sleep(30)
                except Exception as e:
                    self.logging.info(f"💀 update loop got error: {e}\nSleeping a few minutes and retrying.")
                    time.sleep(600)
        except Exception as e:
            self.logging.info(f"💀 update loop terminates: {e}")
        finally:
            self.stats["status"] = "off"



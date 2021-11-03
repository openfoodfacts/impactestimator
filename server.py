from impacts_estimation.impacts_estimation import estimate_impacts

import requests
import logging
import sys
import json
import time
import re
import urllib
import threading
import multiprocessing
                    

class Server:
    def __init__(self,
                 logging=logging.getLogger("uvicorn.info"),
                 productopener_base_url=None,
                 productopener_host_header=None,
                 productopener_basic_auth_username=None,
                 productopener_basic_auth_password=None,
                 productopener_username=None,
                 productopener_password=None):
        self.logging = logging
        self.productopener_base_url = productopener_base_url
        self.productopener_host_header = productopener_host_header
        self.productopener_username = productopener_username
        self.productopener_password = productopener_password
        self.auth = None
        if productopener_basic_auth_username is not None and productopener_basic_auth_password is not None:
            self.auth = requests.auth.HTTPBasicAuth(productopener_basic_auth_username, productopener_basic_auth_password)
        self.estimation_version = 2
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
        if self.auth:
            self.logging.info(f"Looking for products using '{url}' with [{self.auth.username}/{self.auth.password}]")
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
        res = {}
        for k in m:
            v = m[k]
            if isinstance(v, dict):
                v = self._bsonify(v)
            k = k.replace(".", "_").replace("$", "_")
            res[k] = v
        return res

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
                    raise Exception(f"Incorrect user name or password ({self.productopener_username}/{self.productopener_password})")
                else:
                    raise Exception("Response not valid JSON!")
        else:
            self.logging.info(f"Storing decoration for {self._prod_desc(prod)}: {response.text}!")
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
            impact = estimate_impacts(
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
        q = multiprocessing.Queue(1)
        p = multiprocessing.Process(target=self._estimate_outside_process, args=(product, q))
        try:
            p.start()
            p.join(deadline)
            if p.is_alive():
                raise Exception(f"estimation process timed out after {deadline} seconds")
        finally:
            p.kill()
            p.join()
            p.close()
        try:
            results = q.get(block=False)
            if results[1]:
                raise Exception(f"estimation process got exception: {results[1]}")
            return results[0]
        except Exception as e:
            raise Exception(f"estimation queue read: {e.__class__.__name__}: {e}")


    def _run_update_loop(self):
        self.stats["status"] = "on"
        try:
            self.logging.info("run_update_loop()")
            while self.stats["status"] == "on":
                products = self._get_products()
                self.logging.info(f"❤️  Found {len(products)} products to decorate")
                for prod in products:
                    self.stats["seen"] += 1
                    self.logging.info(f"Looking at {self._prod_desc(prod)}")
                    decoration = {}
                    try:
                        impact = self._estimate_with_deadline(prod)
                        self.logging.info(f"❤️  Computed {impact['impacts_geom_means']}") 
                        decoration["impact"] = impact
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
            self.logging.info(f"💀 update loop terminates: {e}")
        finally:
            self.stats["status"] = "off"



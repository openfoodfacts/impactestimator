from fastapi import FastAPI

import argparse
import uvicorn
import os

import server


parser = argparse.ArgumentParser(description="Start the impact estimator service.")
parser.add_argument("--productopener_base_url", help="Base URL to the productopener service", default=os.environ.get("PRODUCT_OPENER_URL"))
parser.add_argument("--productopener_username", help="Username for the productopener service", default=os.environ.get("PRODUCT_OPENER_USERNAME"))
parser.add_argument("--productopener_password", help="Password for the productopener service", default=os.environ.get("PRODUCT_OPENER_PASSWORD"))
parser.add_argument("--productopener_host_header", help="Host header in requests to avoid extra redirects in the responses", default=os.environ.get("PRODUCT_OPENER_HOST_HEADER"))
parser.add_argument("--productopener_basic_auth_username", help="Basic auth username for the productopener service", default=os.environ.get("PRODUCT_OPENER_BASIC_AUTH_USERNAME"))
parser.add_argument("--productopener_basic_auth_password", help="Basic auth password for the productopener service", default=os.environ.get("PRODUCT_OPENER_BASIC_AUTH_PASSWORD"))
args = parser.parse_args()

serv = server.Server(
        productopener_base_url=args.productopener_base_url,
        productopener_host_header=args.productopener_host_header,
        productopener_basic_auth_username=args.productopener_basic_auth_username,
        productopener_basic_auth_password=args.productopener_basic_auth_password,
        productopener_username=args.productopener_username,
        productopener_password=args.productopener_password)


serv.logging.info(f"Service starting with productopener_base_url {args.productopener_base_url}")

app = FastAPI()

@app.get("/")
def stats():
    return serv.stats

@app.on_event("startup")
def startup():
    serv.start_update_loop()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


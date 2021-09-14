from fastapi import FastAPI

import threading
import argparse
import uvicorn

import server


parser = argparse.ArgumentParser(description="Start the impact estimator service.")
parser.add_argument("--productopener_base_url", help="Base URL to the productopener service")
parser.add_argument("--productopener_username", help="Username for the productopener service")
parser.add_argument("--productopener_password", help="Password for the productopener service")
parser.add_argument("--productopener_host_header", help="Host header in requests to avoid extra redirects in the responses")
args = parser.parse_args()

serv = server.Server(
        productopener_base_url=args.productopener_base_url,
        productopener_host_header=args.productopener_host_header,
        productopener_username=args.productopener_username,
        productopener_password=args.productopener_password)


serv.logging.info(f"Service starting with productopener_base_url {args.productopener_base_url}")

app = FastAPI()

@app.get("/")
def read_root():
    return serv.stats

@app.on_event("startup")
def startup():
    thread = threading.Thread(target=serv.run_update_loop, args=())
    thread.daemon = True
    thread.start()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)


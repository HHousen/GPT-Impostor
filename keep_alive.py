import os
import requests
from flask import Flask
from threading import Thread, Timer

app = Flask(__name__)


@app.route("/")
def index():
    return "Running"


def run():
    app.run(host="0.0.0.0", port=36302)


def log_uptime():
    Timer(60, log_uptime).start()
    try:
        requests.get(os.environ["UPTIME_CHECK_URL"], timeout=10)
    except requests.RequestException as e:
        print("Ping failed: %s" % e)


def keep_alive():
    if "UPTIME_CHECK_URL" in os.environ.keys():
        log_uptime()
    t = Thread(target=run)
    t.start()

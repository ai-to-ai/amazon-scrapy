import subprocess
from datetime import datetime
from flask import Flask, render_template, request
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
import config

app = Flask(__name__)


@app.route('/')
def scrape():
    """
    Run spider in another process and store items in file. Simply issue command:

    > scrapy crawl spidername

    wait for  this command to finish, and read output.json to client.
    """
    try:
        spider_name = "Amazon"
        subprocess.run(['scrapy', 'crawl', spider_name])
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    return ""


if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)

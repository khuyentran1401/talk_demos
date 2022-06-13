from prefect_slack import SlackWebhook
from prefect_slack.messages import send_incoming_webhook_message
from prefect.tasks import task_input_hash
from prefect.flow_runners import SubprocessFlowRunner
from prefect import flow, task

import requests
import re
from bs4 import BeautifulSoup
import time
from datetime import timedelta

import requests
import re
from bs4 import BeautifulSoup
from autoscraper import AutoScraper
from prefect import flow, task


@task(retries=3, retry_delay_seconds=10)
def get_shoes_link():
    url = "https://www.nike.com/w/womens-shoes-5e1x6zy7ok"
    scraper = AutoScraper()
    wanted_list = [
        "https://www.nike.com/t/air-force-1-07-womens-shoes-GCkPzr/DD8959-100"
    ]
    urls = scraper.build(url, wanted_list)
    return urls


@task(retries=3, retry_delay_seconds=10)
def find_nike_price(urls: list):
    prices = []
    for url in urls:
        k = requests.get(url).text
        soup = BeautifulSoup(k, "html.parser")
        price_string = soup.find("div", {"class": "product-price"}).text
        price_string = price_string.replace(" ", "")
        price = int(re.search("[0-9]+", price_string).group(0))
        prices.append(price)
    return prices


@task
def get_cheap_prices(prices: list, budget: int):
    return [price for price in prices if price <= budget]


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def summarize(prices: list, budget: int):
    num_cheap_shoes = len(prices)
    if num_cheap_shoes > 0:
        return f"There are {num_cheap_shoes} shoes under ${budget}. Come back and shop"
    else:
        return "Sorry, there are no cheap shoes."


@flow
def nike_flow(budget: int):
    shoes_urls = get_shoes_link()
    prices = find_nike_price(shoes_urls)
    cheap_prices = get_cheap_prices(prices, budget)
    message = summarize(cheap_prices, budget).result()
    slack_token = "https://hooks.slack.com/services/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"
    send_incoming_webhook_message(
        slack_webhook=SlackWebhook(slack_token), text=f"{message}"
    )


budget = 120
nike_flow(budget)

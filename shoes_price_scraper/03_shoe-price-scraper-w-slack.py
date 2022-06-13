from prefect_slack import SlackWebhook
from prefect_slack.messages import send_incoming_webhook_message
from prefect.tasks import task_input_hash
from prefect import flow, task
import re
from datetime import timedelta

from autoscraper import AutoScraper
from prefect import flow, task


@task(retries=3, retry_delay_seconds=10)
def get_shoes_prices():
    url = "https://www.nike.com/w/womens-shoes-5e1x6zy7ok"
    scraper = AutoScraper()
    wanted_list = ["$100"]
    urls = scraper.build(url, wanted_list)
    return urls


@task(retries=3, retry_delay_seconds=10)
def process_nike_price(prices: list):
    processed_prices = []
    for price_string in prices:
        price_string = price_string.replace(" ", "")
        price = int(re.search("[0-9]+", price_string).group(0))
        processed_prices.append(price)
    return processed_prices


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
    str_prices = get_shoes_prices()
    prices = process_nike_price(str_prices)
    cheap_prices = get_cheap_prices(prices, budget)
    message = summarize(cheap_prices, budget).result()
    slack_token = "https://hooks.slack.com/services/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"
    send_incoming_webhook_message(
        slack_webhook=SlackWebhook(slack_token), text=f"{message}"
    )


budget = 120
nike_flow(budget)

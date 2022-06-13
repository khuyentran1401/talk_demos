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


@task(retries=3, retry_delay_seconds=10)
def find_nike_price(url):
    k = requests.get(url).text
    soup = BeautifulSoup(k, "html.parser")
    price_string = soup.find("div", {"class": "product-price"}).text
    price_string = price_string.replace(" ", "")
    price = int(re.search("[0-9]+", price_string).group(0))
    return price


@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def compare_price(price, budget):
    if price <= budget:
        return f"Buy the shoes! Good deal!"
    else:
        return f"Don't buy the shoes. They're too expensive"


@flow(name="Shoe Price Notification")
def nike_flow(url: str, budget: int):
    price = find_nike_price(url)
    message = compare_price(price, budget).result()
    slack_token = "https://hooks.slack.com/services/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"
    send_incoming_webhook_message(
        slack_webhook=SlackWebhook(slack_token), text=f"{message}"
    )


url = "https://www.nike.com/t/air-max-270-womens-shoes-Pgb94t/AH6789-601"
budget = 120
nike_flow(url, budget)

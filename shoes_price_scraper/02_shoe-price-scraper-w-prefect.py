import re
from autoscraper import AutoScraper
from prefect import task, flow 

@task 
def get_shoes_prices():
    url = "https://www.nike.com/w/womens-shoes-5e1x6zy7ok"
    scraper = AutoScraper()
    wanted_list = ["$100"]
    urls = scraper.build(url, wanted_list)
    return urls

@task 
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

@task
def summarize(prices: list, budget: int):
    num_cheap_shoes = len(prices)
    if num_cheap_shoes > 0:
        print(f"There are {num_cheap_shoes} shoes under ${budget}. Come back and shop")
    else:
        print("Sorry, there are no cheap shoes.")

@flow
def nike_flow(budget: int):
    str_prices = get_shoes_prices()
    prices = process_nike_price(str_prices)
    cheap_prices = get_cheap_prices(prices, budget)
    summarize(cheap_prices, budget)


budget = 120
nike_flow(budget)

import os

import dotenv

dotenv.load_dotenv()

appId = 1
# database details where products, categories, etc. are stored
db_name = "tasks_db"
products_table = "products"
products_category_table = "productCategory"
products_sellers_table = "productSellers"
product_price_history_table = "productPriceHistory"
app_settings_table = "appSettings"

mongodb_user = "david"
mongodb_password = "YAFV68dBmBQhoNJs"
mongodb_cluster = "uhrfxiy"

# refer to https://www.scraperapi.com/documentation/python/#getting-started to learn more about the ScraperAPI
# get proxy from ScraperAPI
def get_proxy():
    scraperAPI = os.getenv('SCRAPER_API_KEY')
    proxies = f"http://scraperapi.country_code=us.device_type=desktop:{scraperAPI}@proxy-server.scraperapi.com:8001 "
    return proxies


# User agents to experiment with

# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
#                   'Chrome/71.0.3578.98 Safari/537.36',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#     'Accept-Language': 'en-US,en;q=0.5',
#     'Accept-Encoding': 'gzip',
#     'DNT': '1',  # Do Not Track Request Header
#     'Connection': 'close'
# }

# headers = {"User-Agent": "Mozilla/5.0",
#            "Accept-Language": "en-US,en;q=0.9"}


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
                  'Safari/537.36 OPR/91.0.4516.95',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip',
    'Referer': 'https://www.google.com/',
    'DNT': '1',  # Do Not Track Request Header
    'Connection': 'close'
}

# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
#                   'Chrome/105.0.0.0 Safari/537.36 OPR/91.0.4516.95',
#     'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
#               'application/signed-exchange;v=b3',
#     'Accept-Encoding': 'gzip',
#     'Referer': 'https://www.google.com/',
#     'Upgrade-Insecure-Requests': '1'
# }

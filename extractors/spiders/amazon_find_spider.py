import scrapy
from pymongo import MongoClient
import re
from scrapy.utils.project import get_project_settings

from ..items import MarketItem
from ..utils import getCategoryName, getElement, getRandomUAgents
from ..selectors.amazon import selectors

from dataclasses import asdict
from itemadapter import ItemAdapter
from urllib.parse import urlencode
from urllib.parse import urljoin
from urllib.parse import unquote
import copy

import random

settings = get_project_settings()

class AmazonSpider(scrapy.Spider):
    name = "Amazon"

    baseUrl = "https://www.amazon.com"


    def start_requests(self):
        '''
            This method is to get content of given category url.
        
        '''

        # request with  category url
        # self.custom_request(url=self.categoryUrl, callback=self.parse_category)
        yield scrapy.Request(url=self.categoryUrl, callback=self.parse_category, headers = getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')), meta=self.meta)

    def parse_category(self, response):
        '''
            This method is to extract product pages from given category
        
        '''

        # check if the Captcha exists.
        if response.css('#captchacharacters').extract_first():
            self.log("Captcha found")

        # get products from the category
        products = getElement(selectors["products"], response).getall()

        for productLink in products:
           
           # get asin
            if re.search(r'dp\/(.*)\/', productLink):
                asin = re.search(r'dp\/(.*)\/', productLink).group(1)
            else:
                asin = ""

            # get current link
            productUrl = urljoin(self.baseUrl, productLink)

            # get rid of unnecessary query params
            if re.search(r'https:\/\/[^\/]+\/[^\/]+\/dp\/[^\/]+',productUrl):
                realProductlink = re.search(r'https:\/\/[^\/]+\/[^\/]+\/dp\/[^\/]+',productUrl).group(0)
            else:
                realProductlink = ""

            # get product page
            if asin:
                if asin not in self.productLists:
                    self.productLists.append(asin)
                    customMeta = copy.deepcopy(self.meta)
                    customMeta['asin'] = asin
                    yield scrapy.Request(url=realProductlink, callback=self.parse_product,headers = getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')), meta=customMeta)

        # get next page url
        nextPage = getElement(selectors["nextPage"], response).extract_first(default="NA")
        if nextPage:
            nextUrl = urljoin(self.baseUrl, nextPage)
            yield scrapy.Request(url=nextUrl, callback=self.parse_category, headers = getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')), meta=self.meta)

    def parse_product(self, response):
        '''
            This method is to extract data from product page.
        '''

        # try: 
        #     with open('response.html', 'w', encoding='utf-8') as file:
        #         file.write(response.body.decode('utf-8'))
        #     file.close()
        # except Exception:
        #     print(Exception)

        # check if the recaptcha exists.
        if response.css('#captchacharacters').extract_first():
            self.log("Captcha found ")

        # initialize the item
        Item = MarketItem()

        # Asin
        Item["productLocalId"] = response.meta['asin']

        # brand
        tempBrand = getElement(selectors["brand"], response).extract_first(default="NA")

        if tempBrand is not None and "Visit the" in tempBrand:
            tempBrand = re.search(r'Visit the (.*?) Store', tempBrand).group(1)
        elif tempBrand is not None and "Brand:" in tempBrand:
            tempBrand = tempBrand.replace('Brand: ', "")

        Item["productBrand"] = tempBrand

        # description
        productDescription = getElement(selectors["description"], response).getall()

        ## get rid of blank rows.
        while '' in productDescription:
            productDescription.remove('')
        while ' ' in productDescription:
            productDescription.remove(' ')
        while '\n' in productDescription:
            productDescription.remove('\n')

        Item["productDescription"] = "\n".join(productDescription)

        # sellername
        Item["sellerName"] = "NA"
        # Item["sellerName"] = getElement(selectors["sellerName"], response).extract_first(default="NA")

        # imagelinks
        ScriptText = getElement(selectors["imageLink"], response).extract_first(default="NA")

        tempList = []
        temp = re.findall(r'"large":"[^"]*"', ScriptText)

        for row in temp:
            row = row.replace('"large":"', "")
            row = row.rstrip('"')
            tempList.append(row)

        Item["imageLink"] = tempList

        # productLink
        Item["productLink"] = response.url

        # productTitle
        Item["productTitle"] = getElement(selectors["productTitle"], response).extract_first(default="NA").strip()

        # StockStatus and StockCount: out of stock 0, in stock 1, low stock 2
        stockStatusDesc = getElement(selectors["stockStatusDesc"], response).extract_first(default="NA")
        stockStatusCode = 1
        stockCount = 0

        if stockStatusDesc != "NA":
            if 'Currently unavailable' in stockStatusDesc or 'Temporarily out of stock' in stockStatusDesc:
                stockStatusCode = 0
            elif "left in stock - order soon" in stockStatusDesc:
                stockStatusCode = 2
                match = re.search(r'Only (.*?) left in stock', stockStatusDesc)
                if match:
                    stockCount = match.group(1)

        Item["stockStatus"] = {
            "stockStatus": int(stockStatusCode),
            "stockCount": 0
            # "stockCount": int(stockCount)
        }

        # userRating
        userRatingCount = getElement(selectors["userRatingCount"], response).extract_first()

        if userRatingCount is not None:
            userRatingCount = re.sub('[^0-9]', '', userRatingCount)
        else:
            userRatingCount = 0

        userRatingStars = getElement(selectors["userRatingStar"], response).extract_first()
        if userRatingStars is not None:
            match = re.search(r'(.*?) out of (.*?) stars', userRatingStars)
            if match is not None:
                userRatingStars = match.group(1) + ':' + match.group(2)
        else:
            userRatingStars = "0:0"

        Item["userRating"] = {
            "ratingStars": userRatingStars,
            "ratingCount": int(userRatingCount)
        }

        # price
        Item["price"] = getElement(selectors["price"], response).extract_first(default = "NA")
        Item["oldPrice"] = getElement(selectors["oldPrice"], response).extract_first(default = "NA")

        #productPricessTime
        Item["productProcessTime"] = round(response.meta.get('download_latency'),2)
        # print(download_latency)

        #productProcessSize
        Item["productProcessSize"] = round(len(response.body)/1024,2)

        yield Item

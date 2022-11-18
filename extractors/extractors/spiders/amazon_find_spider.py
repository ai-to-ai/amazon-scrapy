import scrapy
from pymongo import MongoClient 
import re
from scrapy.utils.project import get_project_settings

from ..items import MarketItem
from ..utils import getCategoryName, AmazonSelectors as Selectors, getElement
from dataclasses import asdict
from itemadapter import ItemAdapter
from urllib.parse import urlencode
from urllib.parse import urljoin

class AmazonSpider(scrapy.Spider):
    name = "Amazon"

    baseUrl = "https://www.amazon.com"

    def start_requests(self):

        # request with  category url
        yield scrapy.Request(url=self.categoryUrl, callback=self.parse_category)

    def parse_category(self, response):

        # check if the Captcha exists.
        if response.css('#captchacharacters').extract_first():
            self.log("Captcha found")

        #get products from the category
        products = getElement(Selectors["products"], response)

        for product in products:
            asin = getElement(Selectors["asin"], product).extract_first(default="NA")
            if asin:
                product_url = f"https://www.amazon.com/dp/{asin}"
                yield scrapy.Request(url=product_url, callback=self.parse_product, meta={'asin': asin})

        #get next page url
        nextPage = getElement(Selectors["nextPage"],response).extract_first(default="NA")
        if nextPage:
            nextUrl = urljoin(self.baseUrl,nextPage)
            yield scrapy.Request(url=nextUrl, callback=self.parse_category)

    def parse_product(self, response):

        if response.css('#captchacharacters').extract_first():
            self.log("Captcha found ")

        Item = MarketItem()

        #Asin
        Item["productLocalId"] = response.meta['asin']

        #brand
        tempBrand = getElement(Selectors["brand"], response).extract_first(default="NA")

        if tempBrand != None and "Visit the" in tempBrand:
            tempBrand = re.search(r'Visit the (.*?) Store', tempBrand).group(1)
        elif tempBrand != None and "Brand:" in tempBrand:
            tempBrand = tempBrand.replace('Brand: ', "")
        tempBrand = tempBrand.title()

        Item["productBrand"] = tempBrand

        #description
        productDescription = getElement(Selectors["description"], response).getall()

        while '' in productDescription:
            productDescription.remove('')
        while ' ' in productDescription:
            productDescription.remove(' ')
        while '\n' in productDescription:
            productDescription.remove('\n')

        Item["productDescription"] = "\n".join(productDescription)

        #sellername
        Item["sellerName"] = getElement(Selectors["sellerName"], response).extract_first(default="NA")

        #imagelinks
        ScriptText = getElement(Selectors["imageLink"],response).extract_first(default="NA") 

        tempList = []
        temp = re.findall(r'"large":"[^"]*"',ScriptText)

        for row in temp:
            row = row.replace('"large":"',"")
            row = row.rstrip('"')
            tempList.append(row)

        Item["imageLink"] = tempList
        Item["productLink"] = response.url
        Item["productTitle"] = getElement(Selectors["productTitle"], response).extract_first(default="NA").strip()

        #StockStatus and StockCount: out of stock 0, in stock 1, low stock 2
        stockStatusDesc = getElement(Selectors["stockStatusDesc"],response).extract_first(default="NA")
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
                                "stockStatus":int(stockStatusCode),
                                "stockCount": int(stockCount)
                            }

        #userRating
        userRatingCount = getElement(Selectors["userRatingCount"],response).extract_first()
        
        if userRatingCount is not None: 
            userRatingCount = re.sub('[^0-9]','', userRatingCount) 
        else: userRatingCount = 0 

        userRatingStars = getElement(Selectors["userRatingStar"], response).extract_first()
        if userRatingStars != None:
            match = re.search(r'(.*?) out of (.*?) stars', userRatingStars)
            if match != None:
                userRatingStars = match.group(1) + ':' + match.group(2)
        else : userRatingStars = "0:0"

        Item["userRating"] = {
            "ratingStars":userRatingStars,
            "ratingCount": int(userRatingCount)
        }

        #price
        Item["price"] = getElement(Selectors["price"], response).extract_first()
        Item["oldPrice"] = getElement(Selectors["oldPrice"],response).extract_first()

        yield Item

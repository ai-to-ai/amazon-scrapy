import scrapy
from pymongo import MongoClient
import re
from scrapy.utils.project import get_project_settings

from extractors.items import MarketItem
from extractors.utils import getCategoryName, getElement, getRandomUAgents, cleanUrl
from extractors.selectors.amazon import selectors

from dataclasses import asdict
from itemadapter import ItemAdapter
from urllib.parse import urlencode
from urllib.parse import urljoin
from urllib.parse import unquote
import copy
import uuid

import random

settings = get_project_settings()


class AmazonSpider(scrapy.Spider):
    name = "Amazon"

    baseUrl = "https://www.amazon.com"

    env = "dev"
    # env = "prod"

    # custom_settings = {
    #      'CONCURRENT_REQUESTS':30,
    #      'DOWNLOAD_DELAY': requestInterval
    # }

    def start_requests(self):
        """
            This method is to get content of given category url.

        """
        test_urls = [
            'https://www.amazon.com/DreamController-Original-Controller-Compatible-Wireless/dp/B09V37CLLR?th=1',
            'https://www.amazon.com/Razer-Universal-Quick-Charging-Xbox-S/dp/B09DHSJ4SZ',
            'https://www.amazon.com/CableMod-CM-PCSR-FKIT-NKW-R-Cable-Kit-White/dp/B089KPWW3J?th=1',
            'https://www.amazon.com/Azzaro-Most-Wanted-Parfum-Fragrance/dp/B09VN2FCDF/?_encoding=UTF8&pd_rd_w=jVQKE&content-id=amzn1.sym.aa5d5fb8-9ab9-46ea-8709-d60f551faa80&pf_rd_p=aa5d5fb8-9ab9-46ea-8709-d60f551faa80&pf_rd_r=F2CTCZ402NYW0D04S2DQ&pd_rd_wg=7duSD&pd_rd_r=f5ad392d-c089-448e-afc3-213f9cefcfc3&ref_=pd_gw_deals_gi'

        ]
        if self.env == "dev":
            for url in test_urls:
                # self.meta["asin"] = "B08WC2SMSN"
                asin = re.search(r'\/[0-9A-Z]{10}',url).group(0)
                asin = asin[1:]
                self.meta['asin'] = asin
                self.productLists = []
                # request with  category url
                yield scrapy.Request(url=cleanUrl(url), callback=self.parse_product,
                                     headers=getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')), meta=self.meta, cb_kwargs={"isProduct":True})
        else:
            yield scrapy.Request(url=cleanUrl(self.categoryUrl), callback=self.parse_category, headers = getRandomUAgents(
            settings.get('UAGENTS'), settings.get('HEADERS')), meta=self.meta)

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
                    yield scrapy.Request(url=realProductlink, callback=self.parse_product,headers = getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')),meta=customMeta, cb_kwargs = {"isProduct":True})

        # get next page url 
        nextPage = getElement(selectors["nextPage"], response).extract_first(default="NA") 
        if nextPage: 
            nextUrl = urljoin(self.baseUrl, nextPage)
            yield scrapy.Request(url=cleanUrl(nextUrl), callback=self.parse_category, headers = getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')),meta=self.meta)

    def parse_product(self, response, isProduct = False):
        """
            This method is to extract data from product page.
        """

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

        # get rid of blank rows.
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
        Item["price"] = getElement(selectors["price"], response).extract_first(default="NA")
        Item["oldPrice"] = getElement(selectors["oldPrice"], response).extract_first(default="NA")
        discountTypeList = getElement(selectors["discountType"], response).getall()
        
        if Item["price"] != "NA" and Item["oldPrice"] != "NA":

            if len(discountTypeList) > 1:
                discountType = discountTypeList[1]
            else:
                discountType = "Fixed"
        else:
            discountType = "NA"
        if '%' in discountType:
            discountType = "Percent"
        
        Item["discountType"] = discountType

        # productProcessTime
        Item["productProcessTime"] = round(response.meta.get('download_latency'), 2)
        # print(download_latency)

        # productProcessSize
        Item["productProcessSize"] = round(len(response.body) / 1024, 2)

        # other variants

        if isProduct:
            variantId = str(uuid.uuid5(uuid.NAMESPACE_DNS, response.meta['asin']))
        else:
            variantId = response.meta["variantId"]

        variantGroups = getElement(selectors["variantGroups"], response)

        variants = getElement(selectors["variants"], response).getall()

        variantPrices = getElement(selectors["variantPrice"], response).getall()

        if len(variantPrices) <2 and len(variantGroups) < 2:
            variantId = "NA"
            print('HERE?????')
            print(len(variantPrices))
            print(len(variantGroups))

        #variantId
        try:
            if response.meta["variantId"] != "NA":
                Item["variant"] = {
                    "variantId": response.meta["variantId"],
                    "variantName": response.meta["variantName"]
                }
        except Exception as inst:
            if len(variantPrices) > 1:
                variantName = response.xpath('//li[@data-defaultasin="'+Item['productLocalId']+'"]' + selectors["variantName"][0]).get()
                Item["variant"] = {
                    "variantId": variantId,
                    "variantName": variantName
                }
            if len(variantGroups) > 1:
                variantName = "Many Variants"
                Item["variant"] = {
                    "variantId": variantId,
                    "variantName": variantName
                }
        for temp_variant in variants:
            r = re.search(r'\/[A-Z0-9]{10}\/',temp_variant)
            if r is not None:
                variant = r.group(0)
                variant = variant[1:-1]
            else:
                r = re.search(r',[A-Z0-9]{10}',temp_variant)
                if r is not None:
                    variant = r.group(0)
                    variant = variant[1:]
                else:
                    variant = ""

            if variant != "" and variant != response.meta['asin']:
                if variant not in self.productLists:
                    self.productLists.append(variant)
                    customMeta = copy.deepcopy(self.meta)
                    customMeta['asin'] = variant

                    if len(variantGroups) > 1:
                        variantName = "Many Variants"
                    else:
                        variantName = response.xpath('//li[@data-defaultasin="'+variant+'"]' + selectors["variantName"][0]).get(default = "NA")
                        if variantName == "NA":
                            variantName = response.xpath('//option[contains(@value,"'+variant+'")]' + selectors["variantName"][1]).get(default = "NA")
                    
                    customMeta["variantId"] = variantId
                    customMeta["variantName"] = variantName
                    url = re.sub(r'\/[0-9A-Z]{10}','/'+variant, response.url)

                    yield scrapy.Request(url=cleanUrl(url), callback=self.parse_product,
                                         headers=getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')),
                                         meta=customMeta)

        yield Item

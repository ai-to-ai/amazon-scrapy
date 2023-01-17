import time

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

    count = 0

    # custom_settings = {
    #      'CONCURRENT_REQUESTS':30,
    #      'DOWNLOAD_DELAY': requestInterval
    # }

    def is_product_exist(self, productASIN):
        productASINStatus = self.productCollection.find_one({"productLocalId": productASIN})
        if productASINStatus is None:
            # Product is not existed in db
            return False
        else:
            # Product already existed in db
            return True

    def start_requests(self):
        """
            This method is to get content of given category url.

        """
        test_urls = [
            # 'https://www.amazon.com/DreamController-Original-Controller-Compatible-Wireless/dp/B09V37CLLR', # with collapsible variant group(s)
            # 'https://www.amazon.com/Razer-Universal-Quick-Charging-Xbox-S/dp/B09DHSJ4SZ', # with variant group(s)
            # 'https://www.amazon.com/CableMod-CM-PCSR-FKIT-NKW-R-Cable-Kit-White/dp/B089KPWW3J', # with collapsible variant group(s)
            # 'https://www.amazon.com/Azzaro-Most-Wanted-Parfum-Fragrance/dp/B09VN2FCDF', # with variant(s) without variant group(s)
            # 'https://www.amazon.com/Bose-Soundbar-Built-Bluetooth-connectivity/dp/B094YN85V2', # with variant(s) without variant group(s)
            # 'https://www.amazon.com/Akai-Professional-MPC-One-Controller/dp/B0842VQ2JY', # with variant(s) without variant group(s)
            # 'https://www.amazon.com/Logitech-Handheld-Long-Battery-Touchscreen-Lightweight-Tablet/dp/B09T9FHZLH', # without variant(s)
            # 'https://www.amazon.com/Valve-Handheld-Console-No-Operating-System/dp/B0BBQRYN9M', # without variant(s)
            # 'https://www.amazon.com/gp/product/B0BJ34P723/', # with variants without variant(s) group
            # 'https://www.amazon.com/Charger-Anker-Adapter-Supported-Foldable/dp/B08T5QVTKW' # without variant(s)
            # 'https://www.amazon.com/Purifiers-AMEIFU-Aromatherapy-Allergies-California/dp/B09XJW5VPY', # with variants, coupon-based product
            'https://www.amazon.com/AIRYOMI-Professional-Brushless-Diffuser-0-83Pound/dp/B0B49GXJ3B' # without variant, with coupon
            # 'https://www.amazon.com/SHRATE-Professional-Negative-FastDrying-Temperature/dp/B08621GBMF', # with variants, with discount, with coupon, with price details
            # 'https://www.amazon.com/Dyson-Hair-Dryer-Limited-Gift/dp/B0BQWVYH6D', # with variants, with discount, without coupon
            # 'https://www.amazon.com/Azzaro-Wanted-1-7-Toilette-Spray/dp/B078P7YZ3L', # with variants, with price details
            # 'https://www.amazon.com/Loris-Azzaro-Chrome-Toilette-Spray/dp/9790781261' # with variant groups, with price details
        ]
        if self.env == "dev":
            print('######### App running in developer mode #########')
            for url in test_urls:
                asin = re.search(r'/[0-9A-Z]{10}', url).group(0)
                asin = asin[1:]
                self.meta['asin'] = asin
                print('Product URL ASIN Is: ', asin)
                # self.productLists = []
                # request with category url
                if self.is_product_exist(asin) is False:
                    print('ASIN Not Found In DB')
                    yield scrapy.Request(url=cleanUrl(url), callback=self.parse_product, headers=getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')), meta=self.meta, cb_kwargs={"isProduct":True})
                else:
                    print('This Product Already Is In DB')
        else:
            yield scrapy.Request(url=cleanUrl(self.categoryUrl), callback=self.parse_category, headers = getRandomUAgents(
            settings.get('UAGENTS'), settings.get('HEADERS')), meta=self.meta)

    def parse_category(self, response):
        """
            This method is to extract product pages URL from given category

        """
        print('######################## Check If The Recaptcha Exists ########################')
        if response.css('#captchacharacters').extract_first():
            # self.log("Captcha found")
            print('Captcha Found')
        else:
            print('Captcha Not Found')

        print('######################## Extract Products From The Category ########################')
        products = getElement(selectors["products"], response).getall()
        print('Total Products Detected From Current Page is:', len(products))

        for productLink in products:

            print('######################## Get ASIN Of Current Product ########################')
            if re.search(r'dp/(.*)/', productLink):
                asin = re.search(r'dp/(.*)/', productLink).group(1)
            # elif re.search(r'gp/product/(.*)', productLink):
            #     asin = re.search(r'gp/product/(.*)', productLink).group(1)
            else:
                asin = ""
            print('ASIN Of Current Product Is:', asin)

            print('######################## Get Product Raw Link ########################')
            productUrl = urljoin(self.baseUrl, productLink)
            print('Product Raw URL Is:', productUrl)

            print('######################## Get Rid Of Unnecessary Query Params From Product Raw Link ########################')
            if re.search(r'https://[^/]+/[^/]+/dp/[^/]+', productUrl):
                realProductlink = re.search(r'https://[^/]+/[^/]+/dp/[^/]+', productUrl).group(0)
            # elif re.search(r'https://[^/]+/gp/product/[^/]+', productUrl):
            #     realProductlink = re.search(r'https://[^/]+/gp/product/[^/]+', productUrl).group(0)
            else:
                realProductlink = ""
            print('Cleaned Product Link Is:', realProductlink)

            print('######################## Go To Product Page ########################')
            if asin: 
                if self.is_product_exist(asin) is False:
                    customMeta = copy.deepcopy(self.meta) 
                    customMeta['asin'] = asin 
                    yield scrapy.Request(url=realProductlink, callback=self.parse_product,headers = getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')),meta=customMeta, cb_kwargs = {"isProduct":True})

        print('######################## Get Next Page URL ########################')
        nextPage = getElement(selectors["nextPage"], response).extract_first(default="NA")
        if nextPage:
            nextUrl = urljoin(self.baseUrl, nextPage)
            print('Next Page URL Is:', cleanUrl(nextUrl))
            yield scrapy.Request(url=cleanUrl(nextUrl), callback=self.parse_category, headers = getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')),meta=self.meta)

    def parse_product(self, response, isProduct = False):
        """
            This method is to extract data from product page.
        """
        self.count = self.count + 1
        print('######################## Check If The Recaptcha Exists ########################')
        if response.css('#captchacharacters').extract_first():
            #self.log("Captcha found")
            print('Captcha Found')
        else:
            print('Captcha Not Found')

        print('######################## Initialize The Item Model ########################')
        Item = MarketItem()

        print('######################## Retrieve Asin From Meta ########################')
        Item["productLocalId"] = response.meta['asin']
        print('Product Asin Received By Scrapy Meta is:', response.meta['asin'])

        print('######################## Detect Brand Name ########################')
        productBrand = getElement(selectors["brand"], response).extract_first(default="NA")

        if productBrand is not None and "Visit the" in productBrand:
            productBrand = re.search(r'Visit the (.*?) Store', productBrand).group(1)
        elif productBrand is not None and "Brand:" in productBrand:
            productBrand = productBrand.replace('Brand: ', "")

        Item["productBrand"] = productBrand
        print('Brand Name Is:',productBrand)

        print('######################## Extract Product Description ########################')
        productDescription = getElement(selectors["description"], response).getall()

        # get rid of blank rows.
        while '' in productDescription:
            productDescription.remove('')
        while ' ' in productDescription:
            productDescription.remove(' ')
        while '\n' in productDescription:
            productDescription.remove('\n')

        Item["productDescription"] = "\n".join(productDescription).strip()
        print('Product Description is:', "\n".join(productDescription).strip()[0: 50])

        print('######################## Extract Seller Name ########################')
        sellerName = getElement(selectors["sellerName"], response).extract_first(default="NA").strip()
        Item["sellerName"] = sellerName
        print('Seller Name is:', sellerName)

        print('######################## Extract Images Links ########################')
        ScriptText = getElement(selectors["imageLink"], response).extract_first(default="NA")

        imgList = []
        temp = re.findall(r'"large":"[^"]*"', ScriptText)

        for temp_variant in temp:
            temp_variant = temp_variant.replace('"large":"', "")
            temp_variant = temp_variant.rstrip('"')
            imgList.append(temp_variant)

        Item["imageLink"] = imgList
        print('Product Has:',len(imgList),'Images')

        print('######################## Extract Product Link ########################')
        Item["productLink"] = response.url
        print('Product Link is:', response.url)

        print('######################## Extract Product Title ########################')
        productTitle = getElement(selectors["productTitle"], response).extract_first(default="NA").strip()
        Item["productTitle"] = productTitle
        print('Product Title is:', productTitle)

        print('######################## StockStatus and StockCount: out of stock 0, in stock 1, low stock 2 ########################')
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
            "stockCount": int(stockCount)
        }

        print('Stock Status is:', stockStatusCode)
        print('Stock Count is:', stockCount)

        print('######################## Detect User Rating ########################')
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

        print('User Rating Stars:', userRatingStars)
        print('User Rating Count is:', userRatingCount)

        print('######################## Detect Free Delivery ########################')
        freeDelivery = getElement(selectors["freeDelivery"], response).extract_first(default="NA").strip()
        if 'FREE delivery' in freeDelivery:
            Item["shippingFee"] = freeDelivery
            print('Product Eligible For Free Delivery')
        else:
            Item["shippingFee"] = "NA"
            print("Delivery Details Not Detected")

        print('######################## Detect Price Details ########################')
        priceDetails = getElement(selectors["priceDetails"], response).extract_first(default="NA")
        if priceDetails != "NA":
            if priceDetails.startswith('<span'):
                print(priceDetails)
                if re.search(r'.+\(.+\$[0-9]+\.*[0-9]*.+\s+/\s+[a-zA-Z0-9.]+\).+', priceDetails).group(0):
                    print('String Matched RegEx')
                    startPart = priceDetails[priceDetails.find('('):priceDetails.find('(') + 1]
                    middlePart = priceDetails[priceDetails.find('$'): priceDetails.find('</span>', priceDetails.find('$'))]
                    # endPart = priceDetails[priceDetails.find(' / Count)'):priceDetails.find('</span>', priceDetails.find(' / Count)'))]
                    endPart = priceDetails[priceDetails.find('Count'):priceDetails.find('</span>', priceDetails.find('Count'))]
                    # priceDetails = startPart+middlePart+endPart
                    priceDetails = {
                        'price': middlePart,
                        'unit': endPart
                    }
                    Item["priceDetails"] = priceDetails
                    print('Product Price Details is:', priceDetails)
            elif re.search(r'\(\$[0-9]+\.*[0-9]*.*/.*[A-Za-z0-9.]+\)', priceDetails):
                priceDetails = re.search(r'\(\$[0-9]+\.*[0-9]*.*/.*[A-Za-z0-9.]+\)', priceDetails).group(0)
                if '($' in priceDetails:
                    Item["priceDetails"] = priceDetails
                    print('Product Price Details is:', priceDetails)
            else:
                Item["priceDetails"] = "NA"
        else:
            Item["priceDetails"] = "NA"

        print('######################## Start Price Processing Including Discount And Coupon ########################')
        productPrice = getElement(selectors["price"], response).extract_first(default="NA")
        Item["price"] = productPrice
        print('Product Price Is:', productPrice)

        productOldPrice = getElement(selectors["oldPrice"], response).extract_first(default="NA")
        Item["oldPrice"] = productOldPrice
        print('Product Old Price Is:', productOldPrice)

        discountTypeList = getElement(selectors["discountType"], response).extract_first(default="NA")
        print('Product Discount Value is:', discountTypeList)

        ######################## Detect Coupon Discount ########################
        couponDiscount = getElement(selectors["couponBadge"], response).extract_first(default="NA").strip()
        couponValue = getElement(selectors["couponValue"], response).extract_first(default="NA").strip()
        discountType = "NA"

        if Item["price"] != "NA" and Item["oldPrice"] != "NA":
            print("in this case product has discount without coupon")
            productPriceType = "Discounted"
            if '%' in discountTypeList:
                discountType = "Percent"
                print('Product Price Discount Type is: Percent')
            else:
                discountType = "Fixed"
                print('Product Price Discount Type is: Fixed')

        elif Item["price"] != "NA" and 'Coupon' in couponDiscount:
            print("in this case product has no any discount but coupon")
            productPriceType = "Coupon"
            if '%' in couponValue:
                discountType = "Percent"
                print('Product Eligible For', couponValue, 'Discount')
            elif '$' in couponValue:
                discountType = "Fixed"
                print('Product Eligible For', couponValue, 'Discount')
            extractNumberFromCouponValueText = re.search(r'[0-9]+\.*[0-9]*', couponValue).group(0)
            # extractNumberFromCouponValueText = ''.join(filter(lambda i: i.isdecimal(), couponValue))
            couponValue = int(extractNumberFromCouponValueText)
            print('couponValue:', couponValue)

        else:
            print("in this case product has no any discount or coupon")
            productPriceType = "Regular"
            discountType = "NA"
            couponValue = "NA"
            print('Product Price Discount Type is: NA')

        Item["productPriceType"] = productPriceType
        Item["couponValue"] = couponValue
        Item["discountType"] = discountType

        print('######################## Calculate Product Processing Time ########################')
        productProcessingTime = round(response.meta.get('download_latency'), 2)
        Item["productProcessTime"] = productProcessingTime
        print('Product Processing Time:', productProcessingTime)

        print('######################## Calculate Product Process Size ########################')
        productProcessedSize = round(len(response.body) / 1024, 2)
        Item["productProcessSize"] = productProcessedSize
        print('Product Processed Size is:', productProcessedSize)

        print('######################## Start Variants Processing ########################')
        if isProduct:
            variantId = str(uuid.uuid5(uuid.NAMESPACE_DNS, response.meta['asin']))
        else:
            variantId = response.meta["variantId"]

        variantGroups = getElement(selectors["variantGroups"], response)

        variantText = getElement(selectors["variants"], response).get()

        variants = []
        temp_variants = re.findall(r'"asin":"[^"]*"', variantText)

        for temp_variant in temp_variants:
            temp_variant = temp_variant.replace('"asin":"', "")
            temp_variant = temp_variant.rstrip('"')
            variants.append(temp_variant)

        variantGroupsNames = getElement(selectors['variantGroupsNames'], response).getall()
        variantGroupsNames = [re.sub(r'[^A-Za-z0-9]+','', variantGroupName) for variantGroupName in variantGroupsNames ]
        while '' in variantGroupsNames:
            variantGroupsNames.remove('')
        print('Variant Groups Are: ', variantGroupsNames)
        
        variantDetails = {}

        Item['priceUnit'] = getElement(selectors['priceUnit'],response).get(default = "NA")
        print('Price Unit is: ', Item['priceUnit'])

        # print(getElement(['$x('//a[contains(@aria-label,"Selected")]/@aria-label]))
        tempVariantDesc = getElement(selectors['variantDesc'],response).getall()

        if len(variantGroupsNames) > 0:
            print('This Product Has Variant Group')
            for variantGroupName in variantGroupsNames:
                print('Variant Group Name Is:', variantGroupName)

                variantNameSelectors = [
                        f'//div[contains(@class,"a-row") and label[@class="a-form-label" and contains(text(),"{variantGroupName}")]]/span[@class="selection"]/text()',
                        f'//div[contains(@class,"a-row") and label[@class="a-form-label" and contains(text(),"{variantGroupName}")]]/following-sibling::span//span[@class="a-dropdown-prompt"]/text()',
                        f'//div[contains(@class,"a-section") and span[contains(@class,"a-color-secondary") and contains(text(),"{variantGroupName}")]]/following-sibling::span[contains(@id,"inline-twister-expanded-dimension")]/text()'
                ]
                variantName = getElement(variantNameSelectors, response).get(default="NA").strip()
                variantName = variantName.replace('\n','')
                variantName = variantName.replace('\r','')
                print('Variant Name Is:', variantName)

                if variantName != "NA" and variantName != "":
                    variantDetails[variantGroupName] = variantName
                    print('Variant Details Contains:', variantDetails)
                else:
                    for variantDesc in tempVariantDesc:
                        print('Variant Extracting From Description...')
                        result = re.search(r'Selected (.*) is (.*)\. Tap to collapse\.',variantDesc)
                        print('Variant Description Is:', result)
                        try:
                            variantGroupName = result.group(1)
                            print('Variant Group Name is: ', variantGroupName)
                            variantName = result.group(2)
                            print('Variant Name Is:', variantName)
                            variantDetails[variantGroupName] =variantName
                            print('Variant Details Contains:', variantDetails)
                        except:
                            pass
                    break

        else:
            for variantDesc in tempVariantDesc:
                print('Variant Extracting From Description...')
                result = re.search(r'Selected (.*) is (.*)\. Tap to collapse\.',variantDesc)
                print('Variant Description Is:', result)
                try:
                    variantGroupName = result.group(1)
                    print('Variant Group Name is:', variantGroupName)
                    variantName = result.group(2)
                    print('Variant Name Is:', variantName)
                    variantDetails[variantGroupName] =variantName
                    print('Variant Details Contains:', variantDetails)
                except:
                    pass


        variantPrices = getElement(selectors["variantPrice"], response).getall()

        if variantDetails != {} and variantId !="NA":
            Item['variant'] = {
                'variantId': variantId,
                "variantDetails": variantDetails
            }
        print('==== Finished Product Data Extracting ====')

        yield Item

        if isProduct:
            for variant in variants:
                if variant != "" and variant != response.meta['asin']:
                    print('Product Variant ASIN is: '+variant+' Which Need To Process')
                    if self.is_product_exist(variant) is False:
                        print('It is unique product')
                        # self.productLists.append(variant)
                        customMeta = copy.deepcopy(self.meta)
                        customMeta['asin'] = variant

                        customMeta["variantId"] = variantId
                        customMeta["variantDetails"] = variantDetails
                        url = re.sub(r'/[0-9A-Z]{10}','/'+variant, response.url)

                        yield scrapy.Request(url=cleanUrl(url), callback=self.parse_product,
                                             headers=getRandomUAgents(settings.get('UAGENTS'), settings.get('HEADERS')),
                                             meta=customMeta)



import scrapy
from pymongo import MongoClient 
import re
from scrapy.utils.project import get_project_settings

from ..items import AmazonItem
from ..utils import getCategoryName
from dataclasses import asdict
from itemadapter import ItemAdapter
from urllib.parse import urlencode
from urllib.parse import urljoin

class AmazonSpider(scrapy.Spider):
    name = "Amazon"

    def start_requests(self):

        for url in self.categoryUrls:
            yield scrapy.Request(url=url, callback=self.parse_category)

    def parse_category(self, response):

        baseUrl = "https://www.amazon.com"

        # check if the Captcha exists.
        if response.css('#captchacharacters').extract_first():
            print("Captcha found ")

        #get products from the category
        products = response.xpath('//*[@data-asin]')
        print(products)

        for product in products:
            asin = product.xpath('@data-asin').extract_first(default="NA")
            if asin:
                product_url = f"https://www.amazon.com/dp/{asin}"
                yield scrapy.Request(url=product_url, callback=self.parse_product, meta={'asin': asin})

        #get next page url
        next_page = response.xpath('//a[contains(@class,"s-pagination-next")]/@href').extract_first(default="NA")
        if next_page:
            next_url = urljoin(baseUrl,next_page)
            print(next_url)
            yield scrapy.Request(url=next_url, callback=self.parse_category)

        # self.log(linkSelectors)
    def parse_product(self, response):

        if response.css('#captchacharacters').extract_first():
            print("Captcha found ")

        Item = AmazonItem()

        #Asin
        Item["productLocalId"] = response.meta['asin']

        #brand
        # brandSelector = '//tr[contains(@class, "po-brand")]/td[2]/span/text()'
        brandSelector = '//a[@id="bylineInfo"]/text()'
        
        # brandSelector = '//div[@id="productOverview_feature_div"]/div/table/tr[1]/td[2]/span/text()'
        tempBrand = response.xpath(brandSelector).extract_first(default="NA")
        if tempBrand != None and "Visit the" in tempBrand:
            tempBrand = re.search(r'Visit the (.*?) Store', tempBrand).group(1)
        elif tempBrand != None and "Brand:" in tempBrand:
            tempBrand = tempBrand.replace('Brand: ', "")
        tempBrand = tempBrand.title()
        Item["productBrand"] = tempBrand

        #description
        productDescriptionSelector = '//div[@id="feature-bullets"]/ul/li/span/text()'
        productDescription = response.xpath(productDescriptionSelector).getall()

        while '' in productDescription:
            productDescription.remove('')
        while ' ' in productDescription:
            productDescription.remove(' ')
        while '\n' in productDescription:
            productDescription.remove('\n')

        Item["productDescription"] = "\n".join(productDescription)

        #sellername
        sellerNameSelector = '//a[@id="sellerProfileTriggerId"]/text()'
        sellerNameExceptionSelector = '//div[@tabular-attribute-name="Sold by"]/div[@class="tabular-buybox-text a-spacing-none"]/span/text()'
        Item["sellerName"] = response.xpath(sellerNameSelector).extract_first(default="NA")
        if Item["sellerName"] == "NA":
            Item["sellerName"] = response.xpath(sellerNameExceptionSelector).extract_first(default="NA")

        #imagelinks
        imageLinkSelector = "//script[contains(., 'ImageBlockATF')]/text()"
        ScriptText = response.xpath(imageLinkSelector).extract_first(default="NA") 

        tempList = []
        temp = re.findall(r'"large":"[^"]*"',ScriptText)
        for row in temp:
            row = row.replace('"large":"',"")
            row = row.rstrip('"')
            tempList.append(row)

        Item["imageLink"] = tempList
        # Item["imageLink"] = re.search('"large":".*?"',response.text).groups()
        #productlink
        Item["productLink"] = response.url

        #productTitle
        productTitleSelector = '//span[@id="productTitle"]/text()' 
        Item["productTitle"] = response.xpath(productTitleSelector).extract_first(default="NA").strip()

        #stockstatus
        # stockStatusDescSelector = '//div[@id="availability_feature_div"]/div/span/text()' 
        # stockStatusDesc = response.xpath(stockStatusDescSelector).extract_first(default="NA")

        stockStatusDescSelector = '//div[@id="availabilityInsideBuyBox_feature_div"]/div/div[@id="availability"]/span/text()'
        stockStatusDesc = response.xpath(stockStatusDescSelector).extract_first(default="NA")
        print(stockStatusDesc)
        # out of stock 0, in stock 1, low stock 2
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
        userRatingCountSelector = '//span[@id="acrCustomerReviewText"]/text()'
        userRatingCount = response.xpath(userRatingCountSelector).extract_first()
        
        if userRatingCount is not None: 
            userRatingCount = re.sub('[^0-9]','', userRatingCount) 
        else: userRatingCount = 0 

        userRatingStarSelector = '//span[@id="acrPopover"]/@title'
        userRatingStars = response.xpath(userRatingStarSelector).extract_first()
        if userRatingStars != None:
            match = re.search(r'(.*?) out of (.*?) stars', userRatingStars)
            if match != None:
                userRatingStars = match.group(1) + ':' + match.group(2)
        else : userRatingStars = "0:0"
        Item["userRating"] = {
            "ratingStars":userRatingStars,
            "ratingCount": int(userRatingCount)
        }

        

        print(len(response.text))
        yield Item
        print("================")

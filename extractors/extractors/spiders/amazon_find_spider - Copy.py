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
    name = "ad"

    def __init__(self):
        settings = get_project_settings()

        # get settings from default setting.
        appId = settings.get('APP_ID') 
        mongoDBName = settings.get('DB_NAME')
        categoryCollection = settings.get('PRODUCT_CATEGORY_COLLECTION')
        productCollection = settings.get('PRODUCT_COLLECTION')
        mongoURI = settings.get('MONGODB_URI')

        # get db instance.
        self.client = MongoClient(mongoURI) 
        self.db = self.client[mongoDBName]
        self.categoryCollection = self.db[categoryCollection]
        self.productCollection = self.db[productCollection]

        categoryUrl = self.categoryCollection.find_one({"appId":appId})

        # get category url from db by appId.
        if categoryUrl is not None:
            self.categoryUrls =[categoryUrl[getCategoryName(self.name)]]
        else:
            self.categoryUrls = []

        # get products list to find new product.
        productLists = self.productCollection.find({"sellerName":self.name})
        self.productLists = list(map(lambda product: product['productLink'], productLists))

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
            asin = product.xpath('@data-asin').extract_first()
            if asin:
                product_url = f"https://www.amazon.com/dp/{asin}"
                yield scrapy.Request(url=product_url, callback=self.parse_product, meta={'asin': asin})

        # linkSelectors = response.xpath('//div[@class="a-section a-spacing-base"]/div/span/a/@href').extract()
        # for product in linkSelectors:
        #     if (baseUrl + product) not in self.productLists:
        #         yield scrapy.Request(url= baseUrl + product, callback=self.parse_product)

        #get next page url
        next_page = response.xpath('//a[contains(@class,"s-pagination-next")]/@href').extract_first()
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
        
        brandSelector = '//div[@id="productOverview_feature_div"]/div/table/tr[1]/td[2]/span/text()'
        Item["productBrand"] = response.xpath(brandSelector).extract_first() or "NA"
        if Item["productBrand"] == "NA":
            yield scrapy.Request(url=next_url, callback=self.parse_category)

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
        Item["sellerName"] = response.xpath(sellerNameSelector).extract_first() or "NA"

        #imagelinks
        imageLinkSelector = "//script[contains(., 'ImageBlockATF')]/text()"
        ScriptText = response.xpath(imageLinkSelector).extract_first() 

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
        Item["productTitle"] = response.xpath(productTitleSelector).get().strip() or "NA"

        #stockstatus
        stockStatusDescSelector = '//div[@id="availability_feature_div"]/div/span/text()' 
        stockStatusDesc = response.xpath(stockStatusDescSelector).get()

        # cannot find 0, available 1, temporarily out of stock 2, currently unavaiable 3,
        stockStatusCode = 0

        if stockStatusDesc is not None:
            if 'Currently unavailable' in stockStatusDesc:
                stockStatusCode = 3
            elif 'Temporarily out of stock' in stockStatusDesc:
                stockStatusCode = 2
            elif stockStatusDesc != "" and stockStatusDesc.isspace() is False :
                stockStatusCode = 1

        if stockStatusDesc is not None: 
           stockCount = re.sub('[^0-9]','', stockStatusDesc)
        else:
            stockCount = 0

        Item["stockStatus"] = {
                        "stockStatus":stockStatusCode,
                        "stockCount": stockCount
                    }

        #userRating
        userRatingCountSelector = '//span[@id="acrCustomerReviewText"]/text()'
        userRatingCount = response.xpath(userRatingCountSelector).get() or 0
        userRatingCount = re.sub('[^0-9]','', userRatingCount) 

        userRatingStarSelector = '//span[@id="acrPopover"]/@title'
        userRatingStars = response.xpath(userRatingStarSelector).get() or 0

        Item["userRating"] = {
            "ratingStars":userRatingStars,
            "ratingCount": userRatingCount
        }

        #price
        # priceSelector = '//span[@class="a-price"]/span/text()'
        # Item["price"] = response.xpath(priceSelector).get()

        item_dict = ItemAdapter(Item).asdict()

        # self.productCollection.insert_one(item_dict)
        print(len(response.text))
        yield Item
        print("================")

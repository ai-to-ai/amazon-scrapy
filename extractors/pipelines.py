# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import MarketItem
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient
from .utils import getCategoryName
from datetime import datetime
import copy
from decimal import Decimal
from re import sub


class MongoDBPipeline:

    def open_spider(self, spider):
        settings = get_project_settings()
        print('==========')

        # get db instance.
        self.client = MongoClient(settings.get('MONGODB_URI'))
        self.db = self.client[settings.get('DB_NAME')]
        self.categoryCollection = self.db[settings.get('PRODUCT_CATEGORY_COL')]
        self.productCollection = self.db[settings.get('PRODUCT_COL')]
        self.productSellersCollection = self.db[settings.get('PRODUCT_SELLER_COL')]
        self.productPriceHistoryCollection = self.db[settings.get('PRODUCT_PRICE_HISTORY_COL')]
        self.appSettings = self.db[settings.get('APP_SETTING_COL')]

        self.category = self.categoryCollection.find_one({"appId": settings.get('APP_ID')})
        
        #get proxy status
        spider.meta = {}
        seller = self.productSellersCollection.find_one({"sellerName":spider.name})
        if seller and seller["useProxy"] ==  1:
            spider.meta["proxy"] =  settings.get('PROXY')
            

        # get category url from db by appId.
        if self.category is not None:
            spider.categoryUrl = self.category[getCategoryName(spider.name)]
        else:
            spider.categoryUrl = ""

        # get products list to find new product.
        productLists = self.productCollection.find({"productCategoryId":self.category["_id"]})
        spider.productLists = list(map(lambda product: product['productLocalId'], productLists))

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if isinstance(item, MarketItem):
            product = ItemAdapter(item).asdict()

            if product == "NA":
                return item

            # define the data to save to database.
            productToSave = {}

            productToSave["productBrand"] = product["productBrand"]
            productToSave["productDescription"] = product["productDescription"]
            productToSave["sellerName"] = product["sellerName"]
            productToSave["imageLink"] = product["imageLink"]
            productToSave["productLink"] = product["productLink"]
            productToSave["productTitle"] = product["productTitle"]
            productToSave["stockStatus"] = product["stockStatus"]
            productToSave["userRating"] = product["userRating"]
            productToSave["productLocalId"] = product["productLocalId"]
            productToSave["productProcessTime"] = product["productProcessTime"]
            productToSave["productProcessSize"] = product["productProcessSize"]

            # add necessary data related to collections.
            productToSave["lastUpdate"] = datetime.timestamp(datetime.now())
            productSeller = self.productSellersCollection.find_one({"sellerName": spider.name})
            productToSave["sellerId"] = productSeller["_id"]
            productToSave["productCategoryId"] = self.category["_id"]
            productToSave["updateStatus"] = 0
            productToSave["aggregationId"] = 0

            # product saved and get object id and save price.
            price = {}
            productId = self.productCollection.insert_one(productToSave).inserted_id
            price["productId"] = productId
            price["sellerId"] = productToSave["sellerId"]
            price["priceUpdateTime"] = productToSave["lastUpdate"]

            try:
                price["productPrice"] = float(sub(r'[^\d.]', '', product["price"]))
            except:
                price["productPrice"] = float(format(0, '.2f'))

            price["productShippingFee"] = float(format(0, '.2f'))  # currently set to 0.
            productOldPrice = product["oldPrice"]

            if productOldPrice is None:
                price["productPriceType"] = "Regular"
                self.productPriceHistoryCollection.insert_one(price)
            else:
                price["productPriceType"] = "Discounted"
                try:
                    oldPrice = float(sub(r'[^\d.]', '', product["oldPrice"]))
                    currentPrice = float(sub(r'[^\d.]', '', product["price"]))
                    discountValue = 100 - currentPrice * 100 / oldPrice or 0
                    price["productDiscountValue"] = float(f'{discountValue:.2f}')
                    price["productOldPrice"] = oldPrice
                except Exception as inst:
                    print(inst)
                    price["productOldPrice"] = float(format(0, '.2f'))
                    price["productDiscountValue"] = float(format(0, '.2f'))

                self.productPriceHistoryCollection.insert_one(price)
        return item
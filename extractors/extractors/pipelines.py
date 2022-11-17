# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient 
from .utils import getCategoryName
from datetime import datetime

class ExtractorsPipeline:
    def process_item(self, item, spider):
        return item

class MongoDBPipeline:

    def open_spider(self, spider):
        settings = get_project_settings()

        # get settings from default setting.
        appId = settings.get('APP_ID') 
        mongoDBName = settings.get('DB_NAME')
        categoryCollection = settings.get('PRODUCT_CATEGORY_COLLECTION')
        productCollection = settings.get('PRODUCT_COLLECTION')
        productSellersCollection = settings.get('PRODUCT_SELLER_COLLECTION')
        productPriceHistoryCollection = settings.get('PRODUCT_PRICE_HISTORY_COLLECTION')
        appSettings = settings.get('APP_SETTING_COLLECTION')
        mongoURI = settings.get('MONGODB_URI')

        # get db instance.
        self.client = MongoClient(mongoURI) 
        self.db = self.client[mongoDBName]
        self.categoryCollection = self.db[categoryCollection]
        self.productCollection = self.db[productCollection]
        self.productSellersCollection = self.db[productSellersCollection]
        self.productPriceHistoryCollection = self.db[productPriceHistoryCollection]
        self.appSettings = self.db[appSettings]

        self.category = self.categoryCollection.find_one({"appId":appId})

        # get category url from db by appId.
        if self.category is not None:
            spider.categoryUrls =[self.category[getCategoryName(spider.name)]]
        else:
            spider.categoryUrls = []

        # get products list to find new product.
        productLists = self.productCollection.find({"sellerName":spider.name.title()})
        spider.productLists = list(map(lambda product: product['productLink'], productLists))

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        item_dict = ItemAdapter(item).asdict()
        item_dict["lastUpdate"] = datetime.timestamp(datetime.now())
        productSeller = self.productSellersCollection.find_one({"sellerName":spider.name})
        if productSeller:
            item_dict["sellerId"] = productSeller["_id"]
        else:
            item_dict["sellerId"] =  ""
        if self.category:
            item_dict["productCategoryId"] = self.category["_id"]
        else :
            item_dict["productCategoryId"] = "" 

        item_dict["updateStatus"] = 0
        item_dict["aggregationId"] = 0
        self.productCollection.insert_one(item_dict)
        return item
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.utils.project import get_project_settings
from pymongo import MongoClient 
from .utils import getCategoryName

class ExtractorsPipeline:
    def process_item(self, item, spider):
        return item

class MongoDBPipeline:

    collection = 'scrapy_items'

    def open_spider(self, spider):
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
            spider.categoryUrls =[categoryUrl[getCategoryName(spider.name)]]
        else:
            spider.categoryUrls = []

        # get products list to find new product.
        productLists = self.productCollection.find({"sellerName":spider.name.title()})
        spider.productLists = list(map(lambda product: product['productLink'], productLists))

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        item_dict = ItemAdapter(item).asdict()
        # self.productCollection.insert_one(item_dict)
        return item
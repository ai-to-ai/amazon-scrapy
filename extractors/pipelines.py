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

        # get db instance.
        self.client = MongoClient(settings.get('MONGODB_URI'))
        self.db = self.client[settings.get('DB_NAME')]
        self.categoryCollection = self.db[settings.get('PRODUCT_CATEGORY_COL')]
        self.productCollection = self.db[settings.get('PRODUCT_COL')]
        self.productSellersCollection = self.db[settings.get('PRODUCT_SELLER_COL')]
        self.productPriceHistoryCollection = self.db[settings.get('PRODUCT_PRICE_HISTORY_COL')]
        self.appSettings = self.db[settings.get('APP_SETTING_COL')]

        self.category = self.categoryCollection.find_one({"appId": settings.get('APP_ID')})

        # get proxy status
        spider.meta = {}
        seller = self.productSellersCollection.find_one({"sellerName": spider.name})
        if seller and seller["useProxy"] == 1:
            spider.meta["proxy"] = settings.get('PROXY')

        # get requestInterval
        appSettings = self.appSettings.find_one({})
        if appSettings:
            spider.requestInterval = appSettings["requestInterval"]

        # get category url from db by appId.
        if self.category is not None:
            spider.categoryUrl = self.category[getCategoryName(spider.name)]
        else:
            spider.categoryUrl = ""

        # get products list to find new product.
        # productLists = self.productCollection.find({"productCategoryId": self.category["_id"]})
        # spider.productLists = list(map(lambda product: product['productLocalId'], productLists))
        spider.productCollection = self.productCollection


    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):

        # product object contains all data that filled and transfer from spider to pipeline for process and save to db.
        print('==== Item processing to save data to db ======')
        if isinstance(item, MarketItem):
            product = ItemAdapter(item).asdict()

            if product["price"] == "NA":
                print('Product NOT Saved To DB Because Price Not Available')
                return item

            productASINStatus = self.productCollection.find_one({"productLocalId": product["productLocalId"]})
            if productASINStatus is None:
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
                try:
                    productToSave["productVariants"] = product["variant"]
                except Exception as error:
                    print("This Product Has No Variant(s).")

                print('######################## add necessary data related to collections. ########################')
                productToSave["lastUpdate"] = datetime.timestamp(datetime.now())
                productSeller = self.productSellersCollection.find_one({"sellerName": spider.name})
                productToSave["sellerId"] = productSeller["_id"]
                productToSave["productCategoryId"] = self.category["_id"]
                productToSave["updateStatus"] = 0
                productToSave["aggregationId"] = 0

                print('######################## product saved and get object id and save price. ########################')
                price = {}
                productId = self.productCollection.insert_one(productToSave).inserted_id
                price["productId"] = productId
                price["sellerId"] = productToSave["sellerId"]
                price["priceUpdateTime"] = productToSave["lastUpdate"]

                try:
                    price["productPrice"] = float(sub(r'[^\d.]', '', product["price"]))
                except Exception as ex:
                    print(ex)
                    price["productPrice"] = float(format(0, '.2f'))

                print('######################## save product shipping fee/free delivery. ########################')
                price["productShippingFee"] = product["shippingFee"]

                print('######################## save price details if available. ########################')
                price["priceDetails"] = product["priceDetails"]

                if product["productPriceType"] == "Regular":
                    # in this condition product has regular price
                    price["productPriceType"] = "Regular"
                    self.productPriceHistoryCollection.insert_one(price)

                elif product["productPriceType"] == "Discounted":
                    # in this condition product has discounted price
                    price["productPriceType"] = "Discounted"
                    try:
                        oldPrice = float(sub(r'[^\d.]', '', product["oldPrice"]))
                        currentPrice = float(sub(r'[^\d.]', '', product["price"]))
                        if product["discountType"] == "Percent":
                            discountValue = 100 - currentPrice * 100 / oldPrice or 0
                        elif product["discountType"] == "Fixed":
                            discountValue = oldPrice - currentPrice

                        discountValue = int(discountValue)

                        price["productDiscount"] = {
                            "productDiscountValue" : discountValue,
                            "productDiscountType" : product["discountType"]
                        }
                        price["productOldPrice"] = oldPrice
                    except Exception as inst:
                        print(inst)
                        price["productOldPrice"] = float(format(0, '.2f'))
                        price["productDiscount"] = {}
                    self.productPriceHistoryCollection.insert_one(price)

                elif product["productPriceType"] == "Coupon":
                    # in this condition product has no discount but has coupon
                    price["productPriceType"] = "Coupon"
                    try:
                        discountValue = product["couponValue"]
                        price["productDiscount"] = {
                            "productDiscountValue" : int(discountValue),
                            "productDiscountType" : product["discountType"]
                        }
                    except Exception as inst:
                        print(inst)
                        price["productDiscount"] = {}
                    self.productPriceHistoryCollection.insert_one(price)
            else:
                print('<<<<<<<<<<<<< It is A Duplicated Product >>>>>>>>>>>>>>')

        return item

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class MarketItem(scrapy.Item):
    # define the fields for your item here like:
    productBrand = scrapy.Field()
    productDescription = scrapy.Field()
    sellerName = scrapy.Field()
    imageLink = scrapy.Field()
    productLink = scrapy.Field()
    productTitle = scrapy.Field()
    stockStatus = scrapy.Field()
    userRating = scrapy.Field()
    productLocalId = scrapy.Field()
    price = scrapy.Field()
    oldPrice = scrapy.Field()
    productProcessTime= scrapy.Field()
    productProcessSize= scrapy.Field()

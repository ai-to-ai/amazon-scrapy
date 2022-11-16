# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ExtractorsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class AmazonItem(scrapy.Item):
    # define the fields for your item here like:
    productBrand = scrapy.Field()
    productDescription = scrapy.Field()
    sellerName = scrapy.Field()
    imageLink = scrapy.Field()
    productLink = scrapy.Field()
    productTitle = scrapy.Field()
    stockStatus = scrapy.Field()
    userRating = scrapy.Field()
    productStatus = scrapy.Field()
    productLocalId = scrapy.Field()
    # price = scrapy.Field()

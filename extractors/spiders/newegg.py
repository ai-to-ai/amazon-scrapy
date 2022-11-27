import scrapy
import re


class NewEggSpider(scrapy.Spider):
    name = "newegg"

    pageNum = 1
    categoryUrl = "https://www.newegg.com/p/pl?N=100008225%20600030002"

    def start_requests(self):
        yield scrapy.Request(url=self.categoryUrl, callback=self.parse)

    def parse(self, response):
        nextPage = response.xpath('//button[@title="Next"]/@disabled').extract_first()
        self.log(nextPage)
        if nextPage is None:
            self.pageNum += 1
            yield scrapy.Request(url=f'{self.categoryUrl}&page={self.pageNum}', callback=self.parse)

        productLinks = response.xpath('//a[@class="item-title"]/@href').getall()
        self.log(len(productLinks))
        self.log(productLinks)

        for productLink in productLinks:
            yield scrapy.Request(url=productLink, callback=self.parse_product)

    def parse_product(self, response):
        productTitle = response.xpath('//h1[@class="product-title"]/text()').extract_first(default="NA")
        productDescription = response.xpath('//div[@class="product-bullets"]/ul/li/text()').getall()
        while '' in productDescription:
            productDescription.remove('')
        while ' ' in productDescription:
            productDescription.remove(' ')
        while '\n' in productDescription:
            productDescription.remove('\n')

        productDescription = "\n".join(productDescription)

        # imageLink = response.xpath('//div[@class="product-view-container"]/div[@style="display:
        # none;"]/img/@src').getall()
        imageLink = response.xpath(
            '//img[@style="margin:auto;transform:scale(1);transform-origin:top '
            'left;transition-duration:300ms;opacity:1"]/@src').getall()

        sellerName = response.xpath('//div[@class="product-seller"]/strong/text()').extract_first(default="NA")
        self.log(sellerName)

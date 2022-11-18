
def getCategoryName(name):
    name = name.title()
    if name == "Amazon":
        return "amazonCategoryAddress"
    if name == "Bestbuy":
        return "bestbuyCategoryAddress"
    if name == "Costco":
        return "costcoCategoryAddress"
    if name == "Newegg":
        return "neweggCategoryAddress"

def getElement(selectors, response):
    element = None
    for selector in selectors:
        element = response.xpath(selector)
        if element is not None:
            break
    return element


AmazonSelectors = {
    "products":['//*[@data-asin]'],
    "asin":['@data-asin'],
    "nextPage":['//a[contains(@class,"s-pagination-next")]/@href'],
    "brand":[
                '//a[@id="bylineInfo"]/text()',
                '//tr[contains(@class, "po-brand")]/td[2]/span/text()',
                '//div[@id="productOverview_feature_div"]/div/table/tr[1]/td[2]/span/text()'
            ],
    "description":['//div[@id="feature-bullets"]/ul/li/span/text()'],
    "sellerName":[
                    '//a[@id="sellerProfileTriggerId"]/text()',
                    '//div[@tabular-attribute-name="Sold by"]/div[@class="tabular-buybox-text a-spacing-none"]/span/text()'
                ],
    "imageLink":["//script[contains(., 'ImageBlockATF')]/text()"],
    "productTitle":['//span[@id="productTitle"]/text()'],
    "stockStatusDesc":['//div[@id="availabilityInsideBuyBox_feature_div"]/div/div[@id="availability"]/span/text()'],
    "userRatingCount":['//span[@id="acrCustomerReviewText"]/text()'],
    "userRatingStar":['//span[@id="acrPopover"]/@title'],
    "price":['//span[contains(@class,"a-price")]/span[1]/text()'],
    "oldPrice":['//span[contains(@class,"a-price") and @data-a-strike="true"]/span[1]/text()']
}
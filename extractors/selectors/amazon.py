selectors = {
    "products": ['//*[@id="search"]/div[1]/div[1]/div/span[1]/div[1]/div/div/div/div/div/div/div[2]/div/div/div['
                 '1]/h2/a[not(contains(@style,"display:none")) or not(contains(@style,"visible:hidden"))]/@href'],
    "nextPage": ['//a[contains(@class,"s-pagination-next")]/@href'],
    "brand": [
        '//a[@id="bylineInfo"]/text()',
        '//tr[contains(@class, "po-brand")]/td[2]/span/text()',
        '//div[@id="productOverview_feature_div"]/div/table/tr[1]/td[2]/span/text()'
    ],
    "description": ['//div[@id="feature-bullets"]/ul/li/span/text()'],
    "sellerName": [
        '//a[@id="sellerProfileTriggerId"]/text()',
        '//div[@tabular-attribute-name="Sold by"]/div[@class="tabular-buybox-text a-spacing-none"]/span/text()'

    ],
    "imageLink": ["//script[contains(., 'ImageBlockATF')]/text()"],
    "productTitle": ['//span[@id="productTitle"]/text()'],
    "stockStatusDesc": ['//div[@id="availabilityInsideBuyBox_feature_div"]/div/div[@id="availability"]/span['
                        '@class="a-size-medium a-color-price"]/text()'],
    "userRatingCount": ['//span[@id="acrCustomerReviewText"]/text()'],
    "userRatingStar": ['//span[@id="acrPopover"]/@title'],
    "price": [
        # '//span[contains(@class,"a-price")]/span[1]/text()', '//div[@id="centerCol"]/div[
        # @id="apex_desktop"]/div/div/div[@id="corePrice_desktop"]/div/table/tr/td/span',
        # '//div[@id="centerCol"]/div[@id="apex_desktop"]/div/div/div[@id="corePrice_desktop"]/div/table/tr/td/span[
        # contains(@class,"a-price") and not(contains(@data-a-strike,"true"))]',
        '//div[@id="centerCol"]/div[@id="apex_desktop"]/div/div/div[@id="corePrice_desktop"]/div/table/tr/td/span['
        'contains(@class,"a-price") and not(contains(@data-a-strike,"true"))]/span[1]/text()',
        '//div[@id="centerCol"]/div/div[@id="corePriceDisplay_desktop_feature_div"]/div[1]/span/span/text()'
    ],
    "oldPrice": [
        '//div[@id="centerCol"]/div[@id="apex_desktop"]/div/div/div[@id="corePrice_desktop"]/div/table/tr/td/span['
        'contains(@class,"a-price") and @data-a-strike="true"]/span[1]/text()',
        # '//span[contains(@class,"a-price") and @data-a-strike="true"]/span[1]/text()',
    ],
    "variants": [
        '//li[@data-defaultasin]/@data-defaultasin'
    ]
}

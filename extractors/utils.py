import random
import re

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
        # print(element)
        if len(element) != 0:
            break
    return element


def getRandomUAgents(agents, headers):
    randIndex = random.randint(0, len(agents)-1)
    headers["'User-Agent'"] = agents[randIndex]

    return headers

def cleanUrl(url):
    try:
        #detect asin as this type /DHA2423SLA/
        search_result = re.search(r'https:\/\/.*?\/[0-9A-Z]{10}\/',url)

        if search_result is not None:
            result = search_result.group(0)
            result = result[:-1]
        else:
            search_result = re.search(r'https:\/\/.*?\/[0-9A-Z]{10}\?',url)
            if search_result is not None:
                result = search_result.group(0)
                result = result[:-1]
            else:
                result = url

    except Exception as inst:
        print(inst)
        result = url

    return result
import random

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
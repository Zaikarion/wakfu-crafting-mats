# -*- coding: utf-8 -*-
"""
Created on Mon Sep 9

@author: Zethar
"""

import json

"""
These files are downloaded from Ankama API, located:
    * https://wakfu.cdn.ankama.com/gamedata/1.84.1.27/items.json
    * https://wakfu.cdn.ankama.com/gamedata/1.84.1.27/jobsItems.json
    * https://wakfu.cdn.ankama.com/gamedata/1.84.1.27/recipeIngredients.json
    * https://wakfu.cdn.ankama.com/gamedata/1.84.1.27/recipeResults.json
The 1.84.1.27 is the version number, the latest version can be found at
https://wakfu.cdn.ankama.com/gamedata/config.json 

For more information, see https://www.wakfu.com/en/forum/332-development/236779-json-data
"""
with open('recipeIngredients-1-84-1-27.json', 'r') as f:
    r_ing = json.load(f)
with open('recipeResults-1-84-1-27.json', 'r') as f:
    r_out = json.load(f)
with open('items-1-84-1-27.json', 'r', encoding='utf-8') as f:
    r_items = json.load(f)
with open('jobsitems-1-84-1-27.json', 'r', encoding='utf-8') as f:
    r_items2 = json.load(f)

def rawIDlookup(ID):
    """
    Takes the itemID as input and returns the raw json entry
    """
    for i in r_items:
        if i['definition']['item']['id'] == ID:
            return i
    print("Error: Did not find")
    return None
        
rarity_lookup = ['(Grey)','(W)','(G)','(O)','(Y)','(R)','(S)','(E)']
rarity_convert = dict(zip(rarity_lookup, range(len(rarity_lookup))))

"""
Generate rID_dict, a dictionary whose key is the recipeId and value is a list ordered
by ingredietOrder of a (itemId, quantity) tuple
"""
rID_dict = dict()
for i in r_ing:
    if i['recipeId'] not in rID_dict:
        rID_dict.update({i['recipeId']: dict()})
    rID_dict[i['recipeId']].update({i['ingredientOrder']: (i['itemId'], i['quantity'])})
for k,v in rID_dict.items():
    rID_dict[k] = list(map(lambda x:x[1], sorted(v.items())))

"""
Generate pbrID, a dictionary whose key is the produced itemID and value is a list 
of (recipeId, quantity) tuples in descending quantity order.  
"""
pbrID = dict()
for i in r_out:
    if i['productedItemId'] not in pbrID:
        pbrID[i['productedItemId']] = []
    pbrID[i['productedItemId']].append((i['recipeId'], i['productedItemQuantity']))
for k,v in pbrID.items():
    pbrID[k] = list(sorted(v, key=lambda x:x[1], reverse = True))
    
"""
Generates items_by_ID, a dictionary whose key is the itemID and its values are its 
names in the four languages and its rarity. 
"""
items_by_ID = dict()
for i in r_items:
    d = i['title']
    d.update({'rarity': i['definition']['item']['baseParameters']['rarity']})
    items_by_ID[i['definition']['item']['id']] = d
for i in r_items2:
    d = i['title']
    d.update({'rarity': i['definition']['rarity']})
    items_by_ID[i['definition']['id']] = d
    
def IDtoname(ID, lang = "en"):
    """
    Translates itemIDs into item names in lang. Adds a rarity modifer to the name
    if there are multiple versions of the item. 
    """
    name = items_by_ID[ID][lang]
    keys = [k for k, v in items_by_ID.items() if v[lang] == name]
    if len(keys) == 1:
        return name
    return name + " " + rarity_lookup[items_by_ID[ID]['rarity']]

def nametoID(name, rarity = None, lang = "en"):
    """
    Takes a string corresponding to the item name to be looked up in the language lang and 
    returns the corresponding itemID. If a rarity is provided the function will look only
    for that rarity, otherwise it will return the ID of the version with the highest rarity.
    """
    keys = [k for k, v in items_by_ID.items() if v[lang] == name]
    if not keys:
        raise Exception("No such item not found")
    out = None
    for k in keys:
        if items_by_ID[k]['rarity'] == rarity:
            return k
        elif rarity == None:
            if out is None:
                out = k
            elif items_by_ID[out]['rarity'] < items_by_ID[k]['rarity']:
                out = k
    if out is None:
        raise Exception("No item with designated rarity found")
    return out


def consolidatelst(lst):
    """
    Takes a list of (itemID, quantity) tuples and returns a list of (itemID, quantity)
    tuples with the entries having the same itemID consolidated into one entry with the 
    total quantity. 
    """
    d = dict()
    for i in lst:
        if i[0] not in d:
            d.update({i[0]:i[1]})
        else:
            d[i[0]] += i[1]
    return list(d.items())


def craftitem(t):
    """
    Takes a (itemID, quantity) tuple and returns a list of (itemID, quantity) tuples which
    will create the input itemID to the correct quantity using the recipe dict, in the order 
    of the recipes in that dict.
    """
    ID, qty = t
    out = []
    if ID not in pbrID:
        return [(ID, qty)]
    else:
        rlst = pbrID[ID]
    i = 0
    while i < len(rlst):
        if qty <= 0:
            break
        elif qty < rlst[i][1]:
            i += 1
        else:
            out.append(rID_dict[rlst[i][0]])
            qty -= rlst[i][1]
    if qty > 0:
        out.append(rID_dict[rlst[-1][0]])
    return sum(out, [])


def craftitemlst(l):
    """
    List wrapper for craftitem(t)
    """
    out = []
    for i in l:
        out.append(craftitem(i))
    return consolidatelst(sum(out, []))

def printcraftitemlst(l):
    """
    Prints output from a craftitemlst, converting itemID to names
    """
    for i in l:
        print(IDtoname(i[0]) + " x" + str(i[1]))

def parser(string):
    """
    
    Parameters
    ----------
    string : str
        Takes a string in the format "<name> (<rarity>);<n>" where:
            * <name> is the name of the item as it appears in the game
            * <rarity> is the string expected defined from rarity_convert
            * <n> is the quantity of the item desired
        <rarity> and <n> are optional values; not including the () will set the 
        rarity to None, and leaving off the semicolon will default to 1

    Returns
    -------
    tuple of (name, rarity, quantity)
    """
    rarity, qty = (None, 1)
    tmp = string.split(";")
    if len(tmp) > 1:
        qty = int(tmp[-1])
    tmp = tmp[0].strip()
    if tmp.endswith(")"):
        tmp = tmp.split("(")
        rarity = rarity_convert["(" + tmp[1]]
        tmp = tmp[0]
    return (tmp.strip(), rarity, qty)

def convertfile(f):
    with open(f) as file:
        lines = [parser(line.rstrip()) for line in file]
    return lines

def processfile(f):
    lst = [(nametoID(i[0],i[1]), i[2]) for i in convertfile(f)]
    printcraftitemlst(craftitemlst(lst))
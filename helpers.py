import json
import requests
from datetime import datetime, timedelta
from cs50 import SQL

#Dictionary of the main and sub category pairs to use for API requests
Categories = {
"Ring": [20,1], "Necklace": [20,2], "Earring": [20,3], "Belt": [20,4],
"Ores": [25,1], "Plants": [25,2], "Seed/Fruit": [25,3], "Leather": [25,4], "Blood": [25,5],
"Meat": [25,6], "Seafood": [25,7], "Misc.": [25,8], "Black Stone": [30,1], "Upgrade": [30,2],
"Offensive Elixir": [35,1], "Defensive Elixir": [35,2], "Functional Elixir": [35, 3], "Food": [35,4],
"Potion": [35,5], "Siege Items": [35,6], "Item Parts": [35,7], "Other Consumables": [35,8],
"Main Weapon": [50,1], "Sub-weapon": [50,2], "Helmet": [50,3], "Armor": [50,4],
"Gloves": [50,5], "Shoes": [50,6], "Versatile": [50,7], "Awakening Weapon": [50,8]
}
SECONDS_IN_DAY = 86400
db = SQL("sqlite:///identifier.sqlite")
CREATE = False
UPDATE = False

def main():

    #If true copies over all the ID and name data from item_db.json into an SQL table and then enters the main/sub categories of all items and past 90 day prices
    if CREATE == True:
        create()


    if UPDATE == True:
        update()

#Updates every table with 1 new data entry
def update():
    current_day = db.execute("SELECT Max(Day) FROM prices WHERE Id = 4001")[0]["Max(Day)"]
    trades_day = db.execute("SELECT Max(Day) FROM volume WHERE Id = 4001")[0]["Max(Day)"]
    if trades_day == None:
        trades_day = 0
    day = current_day + 1
    complete_date = datetime.today()
    date = str(complete_date).split()[0]
    last_date = db.execute("SELECT MAX(Date) FROM prices LIMIT 1")[0]["MAX(Date)"]
    #Starts the check for all 3 calculated tables to see if empty or not
    check_1 = check_if_exists(1)
    check_2 = check_if_exists(2)
    check_3 = check_if_exists(3)
    for a in Categories:
        items = call_API_category(Categories[a][0],Categories[a][1])
        for item in items:
            id_check = item.split("-")[0]
            item_info = call_API_specific(id_check)
            id = item_info[0]
            #If the current date and the last entry on the prices database are the same it won't insert the values as not to create duplicates
            if date == last_date:
                pass
            else:
                db.execute("INSERT INTO prices (Id, Price, Day, Date) VALUES(?, ?, ?, ?)", id, item_info[3], day, date)
            #But it will still insert into volume database because it uses YYYY:MM:DD:HH:MM:SS rather than just the date, therefore we can use smaller time units to differentiate
            db.execute("INSERT INTO volume (Id, Stock, Trades, Day, Date) VALUES(?, ?, ?, ?, ?)", id, item_info[4],item_info[5], trades_day, complete_date)
            price_avg = db.execute("SELECT AVG(Price) FROM prices WHERE Id = ?", id)[0]["AVG(Price)"]
            price_compared = (float(item_info[3]) / price_avg) * 100
            if check_1 == False:
                db.execute("INSERT INTO price_avg (Id, Price_avg, Price_compared) VALUES(?, ?, ?)", id, price_avg, round(price_compared,2))
            else:
                db.execute("UPDATE price_avg SET Price_avg = ?, Price_compared = ? WHERE Id = ?", price_avg, round(price_compared,2), id)
            if check_2 == False:
                trades_avg = 0
                daily_silver = 0
                db.execute("INSERT INTO depth (Id, Trades_avg, Silver_avg_daily) VALUES(?, ?, ?)", id, trades_avg, daily_silver)
            else:
                #Calculates the time difference between the first entry in Trades and the last as well as the difference it trades
                #In order to calculate a daily average amount of trades
                trades_min = db.execute("SELECT MIN(Trades) FROM volume WHERE Id = ?", id)[0]["MIN(Trades)"]
                trades_max = db.execute("SELECT MAX(Trades) FROM volume WHERE Id = ?", id)[0]["MAX(Trades)"]
                trades_start = db.execute("SELECT MIN(Date) FROM volume WHERE Id = ?", id)[0]["MIN(Date)"]
                trades_end = db.execute("SELECT MAX(Date) FROM volume WHERE Id = ?", id)[0]["MAX(Date)"]
                trades_start = datetime.strptime(trades_start, "%Y-%m-%d %H:%M:%S")
                trades_end = datetime.strptime(trades_end, "%Y-%m-%d %H:%M:%S")
                total_time = (trades_end-trades_start).total_seconds()
                total_time = total_time / SECONDS_IN_DAY
                if total_time > 0.01:
                    trades_avg = (trades_max - trades_min) / total_time
                    daily_silver = float(trades_avg) * float(item_info[3])
                else:
                    trades_avg = 0
                    daily_silver = 0
                db.execute("UPDATE depth SET Trades_avg = ?, Silver_avg_daily = ? WHERE Id = ?", round(trades_avg, 0), round(daily_silver, 0), id)
            #Calculates the average deviation from the average price on every day and then averages it to
            #Give the average deviation per day across all days, indicating how likely a price is to change in either direction
            price_list = db.execute("SELECT Price FROM prices WHERE Id = ?", id)
            deviation = 0
            total_days = len(price_list)
            for price in price_list:
                total_deviation = abs(price["Price"] - price_avg) + deviation
            volatility = total_deviation / total_days
            volatility = (volatility / float(price_avg)) * 100000000
            if check_3 == False:
                db.execute("INSERT INTO Volatility (Id, Volatility) VALUES(?, ?)", id, round(volatility, 0))
            else:
                db.execute("UPDATE Volatility SET Volatility = ? WHERE Id = ?", round(volatility, 0), id)



##Checks if a given table has any data in it at this point to determine whether to use INSERT or UPDATE
def check_if_exists(key):
    if key == 1:
        check = db.execute("SELECT * FROM price_avg LIMIT 1")
        if check == []:
            return False
        else:
            return True
    if key == 2:
        check = db.execute("SELECT * FROM depth LIMIT 1")
        if check == []:
            return False
        else:
            return True
    if key == 3:
        check = db.execute("SELECT * FROM volatility LIMIT 1")
        if check == []:
            return False
        else:
            return True


#Creates a fresh copy of IDs and Names from the item_db.json file and then enters the initial 90 days of price history
#for each item inside the given categories
def create():
    dump_itemdb()
    for a in Categories:
        get_initial_data(Categories[a][0],Categories[a][1])

## Takes a main and sub category integers as input and returns a list of items, with the properties within each item being separated by -
def call_API_category(main,sub):
    url = 'https://eu-trade.naeu.playblackdesert.com/Trademarket/GetWorldMarketList'
    headers = {
      "Content-Type": "application/json",
      "User-Agent": "BlackDesert"
    }
    payload = {
      "keyType": 0,
      "mainCategory": main,
      "subCategory": sub
    }
    response = requests.request('POST', url, json=payload, headers=headers)
    item_list =  json.loads(response.text)["resultMsg"].split("|")
    del item_list[-1]
    return(item_list)

#Returns a list of the past 90 days(today) included of price history for a given item
def call_API_price_history(key):
    url = 'https://eu-trade.naeu.playblackdesert.com/Trademarket/GetMarketPriceInfo'
    headers = {
    "Content-Type": "application/json",
    "User-Agent": "BlackDesert"
    }
    payload = {
    "keyType": 0,
    "mainKey": key,
    "subKey": 0
    }
    response = requests.request('POST', url, json=payload, headers=headers)
    price_list =  json.loads(response.text)["resultMsg"].split("-")
    return(price_list)

#Returns various current details about a given item
def call_API_specific(key):
    url = 'https://eu-trade.naeu.playblackdesert.com/Trademarket/GetWorldMarketSubList'
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "BlackDesert"
    }
    payload = {
        "keyType": 0,
        "mainKey": key
    }

    response = requests.request('POST', url, json=payload, headers=headers)
    attribute_list = json.loads(response.text)["resultMsg"].split("|")
    del attribute_list[-1]
    return(attribute_list[0].split("-"))

#Opens the item_db.json file and writes its contents into the items database
def dump_itemdb():
    with open('item_db.json') as json_file:

        with open('item_db.json', encoding='utf-8') as fh:
            data = json.load(fh)
        for a in data:
            db.execute("INSERT INTO items (Id, Name) VALUES(?, ?)", data[a]["id"], data[a]["name"])

def get_initial_data(main, sub):
    #Uses call_API_category to get a list of all items in said category
    items = call_API_category(main, sub)
    #Goes through every item in the list of items, splitting the indivudal items by their separator to access the ID
    for item in items:
        n = item.split("-")
        db.execute("UPDATE items SET Mcategory = ?, Scategory = ? WHERE Id = ?", main, sub, n[0])

        #Uses the API call to price history to request the list of the past 89 days of prices
        price_list = call_API_price_history(n[0])
        day = 1
        for price in price_list:
            #Uses a day counter to both number each entry but also to accurately trace back the date the entry corresponds to
            date = datetime.today() - timedelta(days = len(price_list) - day)
            date = str(date).split()[0]
            db.execute("INSERT INTO prices (Id, Price, Day, Date) VALUES(?, ?, ?, ?)", n[0], price, day, date)
            day = day + 1

#Checks through all items based on the name input by the user and sends it back to app.py as a list of items
def query(item, limit):
    item = "%" + item + "%"
    response = db.execute("SELECT items.Name, Volatility.Volatility, price_avg.Price_compared, depth.Silver_avg_daily "
                          "FROM items "
                          "JOIN Volatility ON (items.Id = Volatility.Id) "
                          "JOIN price_avg ON (items.Id = price_avg.Id) JOIN depth ON (items.Id = depth.Id) "
                          "WHERE items.Name LIKE ? ORDER BY price_avg.Price_compared ASC LIMIT ?", item, limit)

    return (response)

main()

#Works together with the app.py function to query for the items within range of the user's input and then sends the list of said items back to app.py
def query_analyze(volatility, price_compared, depth, category, order, limit):
    if category == all:
        if order == "volatility":
            response = db.execute("SELECT items.Name, Volatility.Volatility, price_avg.Price_compared, depth.Silver_avg_daily FROM items JOIN Volatility ON (items.Id = Volatility.Id) JOIN price_avg ON (items.Id = price_avg.Id) JOIN depth ON (items.Id = depth.Id) WHERE Volatility.Volatility > ? and price_avg.Price_compared < ? and depth.Silver_avg_daily > ? ORDER BY Volatility.Volatility DESC LIMIT ?",volatility, price_compared, depth, limit)
        elif order == "price":
            response = db.execute("SELECT items.Name, Volatility.Volatility, price_avg.Price_compared, depth.Silver_avg_daily FROM items JOIN Volatility ON (items.Id = Volatility.Id) JOIN price_avg ON (items.Id = price_avg.Id) JOIN depth ON (items.Id = depth.Id) WHERE Volatility.Volatility > ? and price_avg.Price_compared < ? and depth.Silver_avg_daily > ? ORDER BY price_avg.Price_compared ASC LIMIT ?",volatility, price_compared, depth, limit)
        elif order == "depth":
            response = db.execute("SELECT items.Name, Volatility.Volatility, price_avg.Price_compared, depth.Silver_avg_daily FROM items JOIN Volatility ON (items.Id = Volatility.Id) JOIN price_avg ON (items.Id = price_avg.Id) JOIN depth ON (items.Id = depth.Id) WHERE Volatility.Volatility > ? and price_avg.Price_compared < ? and depth.Silver_avg_daily > ? ORDER BY depth.Silver_avg_daily DESC LIMIT ?",volatility, price_compared, depth, limit)
    else:
        Mcategory = Categories[category][0]
        Scategory = Categories[category][1]
        if order == "volatility":
            response = db.execute("SELECT items.Name, Volatility.Volatility, price_avg.Price_compared, depth.Silver_avg_daily FROM items JOIN Volatility ON (items.Id = Volatility.Id) JOIN price_avg ON (items.Id = price_avg.Id) JOIN depth ON (items.Id = depth.Id) WHERE Volatility.Volatility > ? and price_avg.Price_compared < ? and depth.Silver_avg_daily > ? and Mcategory = ? and Scategory = ? ORDER BY Volatility.Volatility DESC LIMIT ?", volatility, price_compared, depth, Mcategory, Scategory, limit)
        elif order == "price":
            response = db.execute("SELECT items.Name, Volatility.Volatility, price_avg.Price_compared, depth.Silver_avg_daily FROM items JOIN Volatility ON (items.Id = Volatility.Id) JOIN price_avg ON (items.Id = price_avg.Id) JOIN depth ON (items.Id = depth.Id) WHERE Volatility.Volatility > ? and price_avg.Price_compared < ? and depth.Silver_avg_daily > ? and Mcategory = ? and Scategory = ? ORDER BY price_avg.Price_compared ASC LIMIT ?", volatility, price_compared, depth, Mcategory, Scategory, limit)
        elif order == "depth":
            response = db.execute("SELECT items.Name, Volatility.Volatility, price_avg.Price_compared, depth.Silver_avg_daily FROM items JOIN Volatility ON (items.Id = Volatility.Id) JOIN price_avg ON (items.Id = price_avg.Id) JOIN depth ON (items.Id = depth.Id) WHERE Volatility.Volatility > ? and price_avg.Price_compared < ? and depth.Silver_avg_daily > ? and Mcategory = ? and Scategory = ? ORDER BY depth.Silver_avg_daily DESC LIMIT ?", volatility, price_compared, depth, Mcategory, Scategory, limit)
    return (response)

#Checks if a selected category is actually within the categories
def category_check(category):
    if category in Categories:
        return True
    else:
        return False

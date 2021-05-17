# BDO-Market
**Video Demonstration**
https://streamable.com/jhcyh6

BDO-Market is a flask project that uses the Market API of the MMO videogame "Black Desert Online" and allows the user search for certain properties of said items. The main properties are "Volatility", "Price % of avg." and "Depth".

**DISCLAIMER**: This App will not work properly until there have been at least two data points made using the update function from helpers.py, preferably more than two data points over days or weeks. The more data has been collected the more accurate "Depth" will be. With just one datapoint "Depth" will always be 0.

**Volatility**: This stat is calculated by taking the average of all price entries in the database, calculating the difference between the daily average to the total average and then taking the average of that difference before comparing it to the total average. This stat displays the tendency for an item to change its price, items with low volatility tend to have stable prices while items with high volatility tend to change price a lot or drastically.

**Price % of avg.** : This stat is calculated by comparing the item's current price to its total average. It's here to show if an item is cheaper or more expensive than it used to be.

**Depth**: This stat is calculated by taking the average daily trade of an item and multiplying it by its current price. It exists to display the market depth of any given item in silver per day, the higher this value is the more resistant the item is to the market being influenced by any given player. Low depth items tend to crash very fast if a single person focuses on creating said item.

**app.py**: This is the file that flask runs through, it launches update from helpers.py on startup and every 24h following in order to collect accurate data for the market. It also handles all user input and sends complex queries for searching for items to helpers.py

**helpers.py**: This is the main file of the program, its two main functions are update() and create().

create() will take all item IDs and names from item_db.json and sort them into the items sqlite table, then, for all items within the desired categories, it will request from the BDO API and enter the price history for the past 89 days and current day for every single item and enter this into the prices table.

update() will first request the current data on all items within the specified categories and then enter it into the prices table if the current day is not the same as the day of the last data entry in the prices table. It will also enter the current stock and total trades of each item into the volume table.

Afterwards this function will use the data from various tables to calculate "Price % of avg.", "Volatility" and "Depth" and update the existing values for each item in their respective tables.

Aside from that helpers.py also handles all the queries that come from app.py for items with stats within certain ranges and order them according to user input.

**item_db.json** : This file is a json file obtained by scrapping the bdocodex website for item names and their respective IDs. Not created by me.







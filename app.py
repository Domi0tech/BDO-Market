from flask import Flask,render_template, request
import helpers
from cs50 import SQL
from apscheduler.schedulers.background import BackgroundScheduler


db = SQL("sqlite:///identifier.sqlite")
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

helpers.update()

if __name__ == '__main__':
    app.run()
# Uses a sensor to update the database using API calls every 24h
def sensor():
    """ Function for test purposes. """
    helpers.update()

sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor,'interval',minutes=1440)
sched.start()

@app.route('/')
def index():
    average_volatility = round(db.execute("SELECT AVG(Volatility) FROM Volatility")[0]["AVG(Volatility)"])
    return render_template("index.html", average_volatility = average_volatility)

#Site for the user to search items by name by, if there are multiple items with similar name it shows as a list of items with few attributes
#If only a single item's name matches with the input then it renders the details page with more detailed info about price history
@app.route('/individual', methods=["GET", "POST"])
def individual():
    if request.method == "POST":
        query = request.form.get("item")
        limit = request.form.get("limit")
        item_list = helpers.query(query, limit)
        print(item_list)
        if len(item_list) > 1:
            return render_template("individual.html", item_list=item_list)
        elif len(item_list) == 1:
            return details(item_list[0]["Name"])
        return render_template("individual.html")

    else:
        return render_template("individual.html")

#This function takes the user's input to determine the range of the value of the attributes for the items that are to be displayed
#It also takes the user's preference for what value to sort it by
@app.route('/analyze', methods=["GET", "POST"])
def analyze():
    if request.method == "POST":
        limit = request.form.get("limit")
        volatility = request.form.get("volatility")
        price_compared = request.form.get("price_compared")
        depth = request.form.get("depth")
        category = request.form.get("category")
        order = request.form.get("order")

        if not limit:
            limit = 50
        elif limit.isnumeric() == False:
            limit = 50
        if not volatility:
            volatility = 0
        elif volatility.isnumeric() == False:
            volatility = 0

        if not price_compared:
            price_compared = db.execute("SELECT MAX(price_compared) FROM price_avg LIMIT 1")[0]["MAX(price_compared)"]
        elif price_compared.isnumeric() == False:
            price_compared = db.execute("SELECT MAX(price_compared) FROM price_avg LIMIT 1")[0]["MAX(price_compared)"]

        if not depth:
            depth = 0
        elif depth.isnumeric() == False:
            depth = 0

        if not category:
            category = all
        elif helpers.category_check(category) == False:
                category = all

        possible_orders = ["price", "volatility", "depth"]
        if not order:
            order = "price"
        elif order not in possible_orders:
            order = "price"


        item_list_analyze = helpers.query_analyze(volatility, price_compared, depth, category, order, limit)
        print (item_list_analyze)
        return render_template("analyze.html", item_list_analyze = item_list_analyze)
    else:
        return render_template("analyze.html")

#Gives a more detailed view of an item's data using a chart
@app.route('/details', methods=["GET","POST"])
def details(data="default"):
    if data == "default":
        item_name = request.form.get("item_name")
        item = helpers.query(item_name, 1)
        item = item[0]
        item_name = item["Name"]
        price_history = db.execute("SELECT prices.Price, Date FROM prices JOIN items ON (prices.Id = items.Id) WHERE items.Name = ? ORDER BY prices.Date ASC", item_name)
        print(price_history)
        print(400)
        return render_template("details.html", item = item, price_history = price_history)
    else:
        item_name = data
        item = helpers.query(item_name, 1)
        item = item[0]
        item_name = item["Name"]
        price_history = db.execute("SELECT prices.Price, Date FROM prices JOIN items ON (prices.Id = items.Id) WHERE items.Name = ? ORDER BY prices.Date ASC", item_name)
        return render_template("details.html", item = item, price_history = price_history)




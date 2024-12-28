from flask import Flask, render_template, jsonify
from selenium_script import fetch_trending_topics  # Import the scraper function
from bson.json_util import dumps

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/run-script', methods=["POST"])
def run_script():
    result = fetch_trending_topics()
    print("Fetched Result:", result)   
    if "_id" in result:
        result["_id"] = str(result["_id"])
    return app.response_class(
        response=dumps(result),
        status=200,
        mimetype='application/json'
    )


if __name__ == "__main__":
    app.run(debug=True)

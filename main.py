import os

from flask import Flask
import extract
app = Flask(__name__)


@app.route("/")
def execute():
    extract.extractData()
    return "Hello"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
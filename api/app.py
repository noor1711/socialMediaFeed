from flask import Flask, render_template, request
from flask_cors import CORS
from models import get_posts, create_post

app = Flask(__name__)

CORS(app, 
     origins=["http://localhost:3000", "https://pins2things.com", "https://www.pins2things.com"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Length", "Access-Control-Allow-Origin", "Access-Control-Allow-Headers", "Access-Control-Allow-Methods"])

@app.route("/posts", methods=["POST", "GET"])
def index():

    if request.method == "POST":
        data = request.get_json()
        print("request data is", data)
        name = data['name'];
        content = data['content'];
        create_post(name, content);
        return {"message": "Passed"}
    else:
        return list(map(lambda key: {"name": key[1], "content": key[2]}, get_posts()));

if __name__ == '__main__':
    app.run(debug=True)
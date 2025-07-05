from flask import Flask, request, jsonify, redirect
from types import SimpleNamespace
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client_id = os.getenv('clientId')
client_secret = os.getenv('clietSecret')
domain = os.getenv('domain')

# Initialize Flask app
app = Flask(__name__)

# common apis start
# ping api to check if the server is running
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"})

# common apis end

# authentication api start
@app.route('/oauth/initiate', methods=['GET'])
def initiate_auth():
    # config variables for oauth initiation call
    configs = SimpleNamespace(
        baseUrl="https://marketplace.gohighlevel.com/oauth/chooselocation?",
        requestType="code",
        redirectUri=domain + "/oauth/callback",
        clientId=client_id,
        scopes=["products.readonly", "products/prices.readonly"],
    )

    # construct the redirect url for oauth initiation, can understand it as line being appended after line
    redirect_url = (
        f"{configs.baseUrl}"
        f"response_type={configs.requestType}&"
        f"redirect_uri={configs.redirectUri}&"
        f"client_id={configs.clientId}&"
        f"scope={' '.join(configs.scopes)}"
    )

    # used for debugging, returns the constructed redirect url
    # return jsonify({
    #     "message": "Redirecting to authentication",
    #     "redirect_url": redirect_url
    # })

    # redirect the caller to the constructed url
    return redirect(redirect_url)

@app.route('/oauth/callback', methods=['GET'])
def authenticate():
    return jsonify({
        "message": "Authentication successful",
        "request_info": {
            "method": request.method,
            "url": request.url,
            "args": dict(request.args),
            "headers": dict(request.headers),
            "code": request.args.get('code'),
            "state": request.args.get('state')
        }
    })

# authentication api end
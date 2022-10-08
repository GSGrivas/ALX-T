import os
from types import NoneType
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app, resources={r"/*" : {"origins":"*"}})

db_drop_and_create_all()

# ROUTES
@app.route("/drinks")
def retrieve_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all();
        formatted_drinks = [drink.short() for drink in drinks]
        if len(formatted_drinks) == 0 :
            abort(404)
        return jsonify(
        {
            "success": True,
            "drinks": formatted_drinks
        }
        )
    except:
        abort(422)

@app.route("/drinks-detail",methods=["GET"])
@requires_auth('get:drinks-detail')
def retrieve_drinks_detail(self):
    try:
        drinks = Drink.query.order_by(Drink.id).all();
        formatted_drinks = [drink.long() for drink in drinks]
        if len(formatted_drinks) == 0 :
            abort(404)

        return jsonify(
        {
            "success": True,
            "drinks": formatted_drinks
        }
        )
    except:
        abort(422)


@app.route("/drinks", methods=["POST"])
@requires_auth('post:drinks')
def create_drinks(self):
    try:
        body = request.get_json()
        new_title = body.get("title", None)
        new_recipe = json.dumps(body.get('recipe', None))
        drink = Drink(title=new_title, recipe=new_recipe)

        if (drink == None):
            abort(404)
        drink.insert()
        
        return jsonify(
        {
            "success": True,
            "drinks": drink.long()
        }
        )
    except:
        abort(422)

@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drinks(self, drink_id):
    try:
        drink = Drink.query.filter_by(id=drink_id).one_or_none();
        if drink is None:
            abort(404)
            
        body = request.get_json()
        if 'title' in body:
            drink.title=body.get('title')
        
        if 'recipe' in body:
            drink.recipe=json.dumps(body.get('recipe'))
        

        drink.update()

        return jsonify({
            "success": True,
            "drinks": drink.long()
        }
        )
    except:
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drink(self, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if drink is None:
        abort(404)

    Drink.delete(drink)

    return jsonify(
        {
            "success": True,
            "deleted": drink_id
        }
    )

# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )

@app.errorhandler(422)
def unprocessable(error):
    return (
        jsonify({"success": False, "error": 422, "message": "unprocessable"}),
        422,
    )
@app.errorhandler(405)
def not_found(error):
    return (
        jsonify({"success": False, "error": 405, "message": "method not allowed"}),
        405,
    )
'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def no_authentication(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message":error.error,
    }), error.status_code

if __name__ == "__main__":
    app.run(use_debugger=False, use_reloader=False, passthrough_errors=True)

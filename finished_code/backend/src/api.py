import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

"""
@TODO (Done) uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
"""
db_drop_and_create_all()

## ROUTES
"""
@TODO implement endpoint (Done)
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks", methods=["GET"])
def get_drinks():
    # Using SQLAlchemy for creating a list of drinks
    # and ordering (Arranging them ) by id
    drinks = Drink.query.order_by(Drink.id).all()
    drinks_list = [drink.short() for drink in drinks]

    # If there are no drinks in the Drink table abort(404)
    if not drinks:
        abort(404)

    # Return success message and the available drinks
    return jsonify({"success": True, "code": "200", "drinks": drinks_list})


"""
@TODO (Done) implement endpoint
    GET /drinks-detail
    it should require the 'get:drinks-detail' permission
    it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} 
    where drinks is the list of drinks
    or appropriate status code indicating reason for failure
"""


@app.route("/drinks-detail", methods=["GET"])
@requires_auth("get:drinks-detail")
def drinks_details(token):
    try:
        # Using SQLAlchemy for creating a list of drinks
        # and ordering (Arranging them ) by id
        drinks = Drink.query.order_by(Drink.id).all()
        error = {
            "sucess": False,
            "code": " 401",
            "message": "The Token has expired or invalid",
        }

        # Handling errors
        if len(drinks) == 0:
            abort(404)  # No drinks found

        # Return success message and the available drinks
        return jsonify(
            {
                "success": True,
                "code": "200",
                # long form representation of the Drink model
                "drinks": [drink.long() for drink in drinks],
            }
        )
    except:
        abort(401)
        return jsonify(error)


"""
@TODO (Done) implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def new_drink(token):
    body = request.get_json()

    if not ("title" in body and "recipe" in body):
        print("Bad request", body)
    # https://httpstatuses.com/422
    abort(422)  # Unprocessable

    try:

        drink = Drink()
        drink.title = body["title"]
        # dumps() => Serialize obj to a JSON formatted str
        # Further reading: https://docs.python.org/3/library/json.html
        drink.recipe = json.dumps(body["recipe"])

        # Further reading on insert()
        # https://www.postgresqltutorial.com/postgresql-insert/ (Basic info)
        # https://www.postgresqltutorial.com/postgresql-python/insert/ (More helpful)
        drink.insert()

        drinks = drink.long()

        return jsonify({"success": True, "code": "200", "drinks": [drinks]})

    except:
        abort(422)


"""
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks/<id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def edit_drinks(token, id):
    try:
        drink = Drink.query.filter_by(id=id).one()
    except:
        abort(404)
    # get data from json or current data
    drink.title = request.json.get("title") or drink.title
    recipe = request.json.get("recipe")
    if recipe:
        # dumps() => Serialize obj to a JSON formatted str
        # Further reading: https://docs.python.org/3/library/json.html
        drink.recipe = json.dumps(recipe)
    drink.update()
    return jsonify({"success": True, "code": "200", "drink": drink.long()})


"""
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(token, id):
    # Delete drink according to its ID
    drink = Drink.query.get(id)

    try:
        # If no drink found with the provided id abort 404
        if not drink:
            # Or:
            # drink == None:
            # len(drink) == 0:
            abort(404)  # Drink not found

        drink.delete()

        return jsonify({"success": True, "code": "200", "delete": id})

    except:
        abort(422)  # Unprocessable error


## Error Handling
"""
Example error handling for unprocessable entity
"""


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422


"""
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404

"""


# To know more about errors check this https://httpstatusdogs.com/
# https://www.flickr.com/photos/girliemac/sets/72157628409467125-------#
# Or this :
# https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": 400, "message": "bad request"}), 400


@app.errorhandler(404)
def ressource_not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )


@app.errorhandler(405)
def method_not_allowed(error):
    return (
        jsonify({"success": False, "error": 405, "message": "method not allowed"}),
        405,
    )


@app.errorhandler(500)
def internal_server_error(error):
    return (
        jsonify({"success": False, "error": 500, "message": "internal server error"}),
        500,
    )


"""
@TODO (Done) implement error handler for AuthError
    error handler should conform to general task above 
"""


@app.errorhandler(AuthError)
def auth_error(auth_error):
    return (
        jsonify(
            {
                "success": False,
                "error": auth_error.status_code,
                "description": auth_error.error,
            }
        ),
        auth_error.status_code,
    )

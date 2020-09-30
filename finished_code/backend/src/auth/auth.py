import json
from flask import request, _request_ctx_stack, abort, jsonify
from functools import wraps
from jose import jwt
from urllib.request import urlopen

# --------------------------------------------------#
# Auth0 Config
# --------------------------------------------------#

# Open your Auth0 account => Go to "Applications"
# Then open your app => Open "Settings"
# Then you'll find the "Domain" and more info

AUTH0_DOMAIN = "dev-0m5vk9lb.us.auth0.com"
ALGORITHMS = ["RS256"]
API_AUDIENCE = "coffee"

## AuthError Exception
"""
AuthError Exception
A standardized way to communicate auth failure modes
"""


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

"""
@TODO implement get_token_auth_header() method
[1] it should attempt to get the header from the request (Done)
[2] it should raise an AuthError if no header is present (Done)
[3] it should attempt to split bearer and the token (Done)
[4] it should raise an AuthError if the header is malformed (Done)
[5] return the token part of the header (Done)
"""

# This part was explained in Lesson 2
# Concept 13. Sending Tokens with Requests in the class room
def get_token_auth_header():

    # Checking that we're recieving a valid authentication header
    # with a token

    # Checking if Authorization is not in request.header
    if "Authorization" not in request.headers:
        # raise an AuthError if no header is present
        raise AuthError(
            {
                "success": False,
                "error": "401",
                "code": "unauthorized",
                "message": "Unauthorized",
            },
            401,
        )

    auth_header = request.headers["Authorization"]
    # split bearer and the token
    header_parts = auth_header.split(" ")

    # To check that there are more than 1 index
    if len(header_parts) != 2:
        raise AuthError(
            {
                "success": False,
                "error": "401",
                "code": "invalid_header",
                "message": "The header must be a header token so it should have more than 1 index",
            },
            401,
        )

    elif header_parts[0].lower() != "bearer":
        raise AuthError(
            {
                "success": False,
                "error": "401",
                "code": "invalid_header",
                "message": "The Authorization header must start with Bearer",
            },
            401,
        )

    # Retuns token
    return header_parts[1]


"""
@TODO (DONE) implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
"""


def check_permissions(permission, payload):
    # permission: string permission
    # Making sure that payload contains the permission key
    if "permissions" not in payload:
        raise AuthError(
            {
                "success": False,
                "error": "400",
                "code": "invalid_claims",
                "description": "400 Bad Request Error, Permissions not included in JWT.",
            },
            400,
        )

    # If the requisted permission exist in the payload permission array
    # RAISE 403 ERROR
    if permission not in payload["permissions"]:
        raise AuthError(
            {
                "success": False,
                "error": "403",
                "code": "forbidden",
                "message": "No permission is found, forbideen",
            },
            403,
        )
    return True


"""
@TODO (Done) implement verify_decode_jwt(token) method (Done)
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
"""

# This exact function was mentioned in the classroom
# Lesson 2 : Identity and Authentication
# Concept 10.Practice - Validating Auth0 Tokens
## Auth Header
# And also check the Auth0 Quickstart
# https://auth0.com/docs/quickstart/backend/python/01-authorization
def verify_decode_jwt(token):
    # GET THE PUBLIC KEY FROM AUTH0
    jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())

    # GET THE DATA IN THE HEADER
    unverified_header = jwt.get_unverified_header(token)

    # CHOOSE OUR KEY
    rsa_key = {}
    if "kid" not in unverified_header:
        raise AuthError(
            {"code": "invalid_header", "description": "Authorization malformed."}, 401
        )

    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }

    # Finally, verify
    if rsa_key:
        try:
            # USE THE KEY TO VALIDATE THE JWT
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer="https://" + AUTH0_DOMAIN + "/",
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError(
                {
                    "success": False,
                    "code": "token_expired",
                    "error": "401",
                    "description": "Token is expired.",
                },
                401,
            )

        except jwt.JWTClaimsError:
            raise AuthError(
                {
                    "success": False,
                    "error": "401",
                    "code": "invalid_claims",
                    "description": "Incorrect claims. Please, check the audience and issuer.",
                },
                401,
            )
        except Exception:
            raise AuthError(
                {
                    "success": False,
                    "error": "400",
                    "code": "invalid_header",
                    "description": "Unable to parse authentication token.",
                },
                400,
            )
    raise AuthError(
        {
            "success": False,
            "error": "400",
            "code": "invalid_header",
            "description": "Unable to find the appropriate key.",
        },
        400,
    )


"""
@TODO (Done) implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method

"""


def requires_auth(permission=""):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except:
                raise AuthError(
                    {
                        "success": False,
                        "code": "unauthorized",
                        "error": "401",
                        "description": "unauthorized action",
                    },
                    401,
                )
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
#!/usr/bin/python3

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import hashlib
import psycopg2 as pg
from flask_limiter import Limiter
from db_connection import db_connection


app = Flask(__name__)
CORS(app)

limiter = Limiter(
    app,
    default_limits=["10 per second"]
)


def get_id_by_username_and_password(headers, cur):
    cur.execute(
        "SELECT id FROM users WHERE username = %s AND hashed_password = %s",
        [
            headers['username'],
            to_sha256(headers['password'])
        ]
    )
    return cur.fetchone()[0]


def to_sha256(text):
    m = hashlib.sha256()
    m.update(str.encode(text))
    return m.digest()


@app.route('/sign_up/', methods=['POST'])
# TODO activate limits
# @limiter.limit(
#     '1/3 minutes',
#     override_defaults=False,
#     deduct_when=lambda response: response.status_code == 201
# )
def sign_up():
    headers = request.headers
    conn, cur = db_connection()
    try:
        username = headers['username']
        password = headers['password']
        default_wisher_displayed_name = headers['default_wisher_displayed_name']
    except KeyError:
        return Response(status=400)
    try:
        cur.execute(
            "INSERT INTO users (username, hashed_password, default_wisher_displayed_name) VALUES (%s, %s, %s)",
            [username, to_sha256(password), default_wisher_displayed_name]
        )
    except pg.errors.UniqueViolation:
        return Response(status=409)
    conn.commit()
    return Response(status=201)


@app.route('/add_friend/', methods=['POST'])
# TODO activate limits
# @limiter.limit(
#     "1/3 seconds",
#     override_defaults=False,
#     deduct_when=lambda response: response.status_code == 200
# )
def add_friend():
    headers = request.headers
    conn, cur = db_connection()
    try:
        wisher_id = get_id_by_username_and_password(headers, cur)
        target_name = headers['target_name']
        target_username = headers['target_username']
        target_birthday = headers['target_birthday']
        # Can be null if there is not a preferred name to display.
        wisher_displayed_name = headers.get('wisher_displayed_name')
    except KeyError:
        return Response(status=400)
    except TypeError:
        return Response(status=401)
    # TODO add duplicate error handling.
    cur.execute(
        "INSERT INTO targets (name, username, birthday, wisher_id, wisher_displayed_name) \
        VALUES (%s, %s, %s, %s, %s)",
        [
            target_name, target_username, target_birthday,
            wisher_id, wisher_displayed_name
        ]
    )
    conn.commit()
    return Response(status=201)


@app.route('/friends/', methods=['GET'])
# TODO add limiting.
def friends():
    headers = request.headers
    conn, cur = db_connection()
    try:
        wisher_id = get_id_by_username_and_password(headers, cur)
    except KeyError:
        return Response(status=400)
    except TypeError:
        return Response(status=401)
    cur.execute(
        "SELECT name, username, birthday, wisher_displayed_name FROM targets \
        WHERE wisher_id = %s",
        [wisher_id]
    )
    return jsonify(
        [
            {
                'name': name,
                'username': username,
                'birthday': birthday.strftime('%Y-%m-%d'),
                'wisher_displayed_name': wisher_displayed_name
            }
            for name, username, birthday, wisher_displayed_name in cur.fetchall()
        ]
    )


def main():
    app.run(debug=True, host='0.0.0.0', port=8080, threaded=True)


if __name__ == '__main__':
    main()

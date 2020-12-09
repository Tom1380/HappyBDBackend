#!/usr/bin/python3

import tweepy
import json
import psycopg2 as pg
from datetime import date


def get_api():
    credentials_path = 'cred.json'
    try:
        cred = json.load(open(credentials_path))
    except FileNotFoundError:
        print(f'Could not read {credentials_path}!')
        quit()
    except json.decoder.JSONDecodeError:
        print(f'Could not parse {credentials_path}!')
        quit()
    try:
        auth = tweepy.OAuthHandler(
            cred['consumer']['key'],
            cred['consumer']['secret']
        )
        auth.set_access_token(
            cred['access']['key'], cred['access']['secret']
        )
    except KeyError:
        print(f'{credentials_path} seems to miss necessary fields.')
        quit()

    return tweepy.API(auth)


def db_conn():
    conn = pg.connect('dbname=happybd')
    cur = conn.cursor()
    return conn, cur


def users_to_tweet(conn, cur):
    query = "SELECT name, username, wisher_id, wisher_displayed_name FROM targets \
	WHERE last_wish_year != date_part('year', CURRENT_DATE) OR last_wish_year IS NULL \
	AND date_part('month', birthday) = date_part('month', CURRENT_DATE) \
	AND date_part('day', birthday) = date_part('day', CURRENT_DATE)"
    cur.execute(query)
    return [Wish(*row, conn) for row in cur.fetchall()]


class Wish:
    def __init__(self, target_name, target_username, wisher_id, wisher_displayed_name, conn):
        self.target_name = target_name
        self.target_username = target_username
        if wisher_displayed_name == "" or wisher_displayed_name is None:
            self.wisher_displayed_name = Wish.get_default_wisher_displayed_name(
                conn,
                wisher_id
            )
        else:
            self.wisher_displayed_name = wisher_displayed_name

    def get_default_wisher_displayed_name(conn, wisher_id):
        cur = conn.cursor()
        cur.execute(
            "SELECT default_wisher_displayed_name FROM users WHERE id = %s",
            [wisher_id]
        )
        return cur.fetchone()[0]


def main():
    conn, cur = db_conn()
    api = get_api()
    for wish in users_to_tweet(conn, cur):
        status = f'Happy birthday from {wish.wisher_displayed_name} @{wish.target_username}, time flies {wish.target_name}!'
        print(f'Trying to tweet this: {status}')
        api.update_status(status=status)
        cur.execute(
            "UPDATE targets SET last_wish_year = date_part('year', CURRENT_DATE)\n"
            "WHERE username = %s",
            [wish.target_username]
        )
        conn.commit()
        print("Successfully tweeted!")


if __name__ == '__main__':
    main()

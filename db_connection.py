import psycopg2 as pg


def db_connection():
    conn = pg.connect('dbname=happybd')
    cur = conn.cursor()
    return conn, cur

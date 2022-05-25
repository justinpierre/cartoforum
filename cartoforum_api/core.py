import psycopg2
import config

try:
    pgconnect = psycopg2.connect(database=config.dbname, user=config.dbusername,
                                 password=config.dbpassword, host='pg.cf.net', port=config.dbport)
except:
    print("no connection")

cur = pgconnect.cursor()
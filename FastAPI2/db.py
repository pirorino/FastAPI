import databases
import sqlalchemy
import os

# DATABASE = 'postgres'
# AWS
# USER = os.environ['USER']
# PASS = os.environ['PASS']
# PORT = '5432'
# Database_endpoint = os.environ['ENDPOINT']
# DB_NAME = os.environ['DB_NAME']

# LOCAL
USER = 'saru'
PASS = 'monkey'
Database_endpoint = 'localhost'

DATABASE = 'postgres'
PORT = '5432'
DB_NAME = 'fastapidb'

DATABASE_URL = '{}://{}:{}@{}:{}/{}'.format(DATABASE, USER, PASS, Database_endpoint, PORT, DB_NAME)

try:
    print("Connecting to "+Database_endpoint)
    print("DATABASE_URL "+DATABASE_URL)
    # databases
    database = databases.Database(DATABASE_URL, min_size=5, max_size=20)
    ECHO_LOG = False
    engine = sqlalchemy.create_engine(DATABASE_URL, echo=ECHO_LOG)
    metadata = sqlalchemy.MetaData()
    print ("Connection successful to "+Database_endpoint)

except Exception as e:
    print ("Connection unsuccessful due to "+str(e))

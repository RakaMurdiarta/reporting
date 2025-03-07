from dbutils.pooled_db import PooledDB
import pymysql
import os

db_name = os.getenv('DATABASE_NAME')
db_host = os.getenv('DB_MYSQL_HOST')
db_user = os.getenv('DB_USERNAME')
db_port = os.getenv('DB_MYSQL_PORT')
db_password = os.getenv('MYSQL_PASSWORD')

pool = PooledDB(
        creator=pymysql,         # Use pymysql as the connector
        host=db_host,         # Database host
        user=db_user,              # Database username
        password=db_password,         # Database password
        database=db_name,  # Database name
        autocommit=True,          # Whether to commit automatically
        maxconnections=10,        # Maximum number of connections in the pool
        mincached=2,              # Minimum number of idle connections in the pool
        maxcached=5,              # Maximum number of idle connections in the pool
        blocking=True,            # Block and wait if the pool is full
        maxshared=3,               # Maximum number of shared connections
        port=int(db_port)
    )
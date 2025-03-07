from dbutils.pooled_db import PooledDB
import pymysql

pool = PooledDB(
        creator=pymysql,         # Use pymysql as the connector
        host='127.0.0.1',         # Database host
        user='root',              # Database username
        password='admin',         # Database password
        database='sia_backup_prod',  # Database name
        autocommit=True,          # Whether to commit automatically
        maxconnections=10,        # Maximum number of connections in the pool
        mincached=2,              # Minimum number of idle connections in the pool
        maxcached=5,              # Maximum number of idle connections in the pool
        blocking=True,            # Block and wait if the pool is full
        maxshared=3,               # Maximum number of shared connections
        port=3306
    )
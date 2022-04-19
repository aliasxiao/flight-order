# -*- coding: utf-8 -*-

"""Global settings for the project"""
import os
from tornado.options import define

# mysql
db_host = os.getenv('SQL_HOST', 'mysql')
db_port = os.getenv('SQL_PORT', 3306)
db_user = os.getenv('SQL_USER', 'flight')
db_pwd = os.getenv('SQL_PWD', 'test')
db_name = os.getenv('SQL_DB', 'flight')
# redis
redis_host = os.getenv('REDIS_IP', 'redis')
redis_pwd = os.getenv('REDIS_PASSWORD', 'test')
redis_db = int(os.getenv('REDIS_DB', 1))

define("port", default=8000, help="run on the given port", type=int)
define("config", default=None, help="tornado config file")
define("debug", default=False, help="debug mode")

# mysql config
define("mysql_host", default=db_host)
define("mysql_port", default=int(db_port))
define("mysql_db", default=db_name)
define("mysql_user", default=db_user)
define("mysql_pwd", default=db_pwd)
# redis config
define("redis_address", default="redis://" + redis_host)
define("redis_db", default=redis_db, type=int)
define("redis_pwd", default=redis_pwd)

settings = dict()
settings["debug"] = False


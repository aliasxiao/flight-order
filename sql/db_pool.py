import traceback
import pymysql
from pymysql.cursors import Cursor, DictCursor
from dbutils.pooled_db import PooledDB
from tornado.options import options


class MySQLEngine(object):
    """
	"""

    def connect(self, **kwargs):
        db_host = kwargs.get('db_host', 'localhost')
        db_port = kwargs.get('db_port', 3306)
        db_user = kwargs.get('db_user', 'root')
        db_pwd = kwargs.get('db_pwd', '')
        db = kwargs.get('db', '')
        self.pool = PooledDB(
            pymysql,
            mincached=1,
            maxcached=5,
            maxconnections=10,
            host=db_host,
            user=db_user,
            passwd=db_pwd,
            db=db,
            port=db_port,
            charset='utf8')

    def _execute(self, sql_query, values=[], css=Cursor):
        # logger.debug("sql:%s values: %s", sql_query.replace('\n', ''), values)
        try:
            conn = self.pool.connection()
            cur = conn.cursor(css)
            cur.execute(sql_query, values)
            conn.commit()
        except Exception:
            print(traceback.format_exc())
            conn.close()

        return conn, cur

    def select(self, sql_query, values=[], cursorclass=DictCursor):
        conn, cur = self._execute(sql_query, values, css=cursorclass)
        conn.close()
        ret = cur.fetchall()
        return ret

    def execute(self, sql, values=[]):
        conn, cur = self._execute(sql, values)
        conn.close()

    def execute_transaction(self, sqls, css=Cursor):
        try:
            conn = self.pool.connection()
            cur = conn.cursor(css)
            for sql, args in sqls:
                cur.execute(sql, args)
            conn.commit()
        except Exception:
            print(traceback.format_exc())
            conn.close()


db_pool = MySQLEngine()
db_pool.connect(**{
	'db_host':options.mysql_host,
	'db_port':options.mysql_port,
	'db_user': options.mysql_user,
	'db_pwd':options.mysql_pwd,
	'db': options.mysql_db,
    })
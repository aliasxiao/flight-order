import random
from settings import db_host, db_port, db_user, db_pwd,db_name
from sql.db_pool import MySQLEngine

mysql_engine = MySQLEngine()
mysql_engine.connect(**{
	'db_host':db_host,
	'db_port':db_port,
	'db_user': db_user,
	'db_pwd':db_pwd,
	'db': db_name,
    })

def create_tables():
    """生成表"""
    sql = '''
		CREATE TABLE IF NOT EXISTS `traveller`(
			`id` int NOT NULL AUTO_INCREMENT,
			`name` varchar(100) NOT NULL COMMENT "用户名",
			PRIMARY KEY (`id`)
		)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
	'''
    mysql_engine.execute(sql)
    sql = '''
			CREATE TABLE IF NOT EXISTS `ticket`(
				`id` int NOT NULL AUTO_INCREMENT,
				`flight_id` int NOT NULL DEFAULT 0 COMMENT "航班id",
				`traveler_id` int NOT NULL DEFAULT 0 COMMENT "旅客id",
				`price` float NOT NULL DEFAULT 0 NULL COMMENT "机票价格",
				`status` int NOT NULL DEFAULT 0 COMMENT "机票状态 0：未预定 1：预定 2：售出",
				PRIMARY KEY (`id`)
			)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
		'''
    mysql_engine.execute(sql)
    sql = '''
			CREATE TABLE IF NOT EXISTS `flight`(
				`id` int NOT NULL AUTO_INCREMENT,
				`capacity` int NOT NULL COMMENT "航班容量20-80",
				`base_price` float NOT NULL COMMENT "机票基础价格",
				`booked_tickets` int NOT NULL DEFAULT 0 COMMENT "机票预定数量",
				`sell_tickets` int NOT NULL DEFAULT 0 COMMENT "机票售出数量",
				PRIMARY KEY (`id`)
			)ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
		'''
    mysql_engine.execute(sql)


def gen_flight(num=200):
    """生成航班数据"""
    base_price = 100.
    for i in range(num):
        capacity = random.randint(20, 80)
        insert_sql = "INSERT INTO `flight`(`capacity`, `base_price`) VALUES(%d, %f)" % (capacity, base_price)
        mysql_engine.execute(insert_sql)


def gen_travller(num=10000):
    """生成旅客数据"""

    for i in range(num):
        insert_sql = "INSERT INTO `traveller`(`name`) VALUES('test_%d')" % (i)
        mysql_engine.execute(insert_sql)


def gen_ticket():
    sql = "SELECT `id`, `capacity` FROM `flight`"
    result = mysql_engine.select(sql)

    for item in result:
        for i in range(item['capacity']):
            insert_sql = "INSERT INTO `ticket`(`flight_id`) VALUES(%d)" % (item['id'])
            mysql_engine.execute(insert_sql)


def gen_db_data():
    create_tables()
    gen_flight()
    gen_travller()
    gen_ticket()

if __name__ == "__main__":
    gen_db_data()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Basic run script"""
import datetime
import asyncio
import time
import traceback

import aioredis
from tornado import httpserver, web
from tornado.options import options, parse_command_line, parse_config_file
from tornado.httpclient import AsyncHTTPClient

from settings import settings
from flight_order.globals import g
from sql.db_pool import db_pool

# 导入的自定义模块内用到了命令行参数，所以需要提前解析命令行参数
parse_command_line()

from flight_order.urls import url_patterns


class TornadoApplication(web.Application):

    def __init__(self, http_client):
        self._http_client = http_client
        web.Application.__init__(self, url_patterns, **settings)


async def run_server():
    """预激awaitable对象并启动http_server"""
    loop = asyncio.get_event_loop()

    redis_pool = await aioredis.create_pool(address=options.redis_address, db=options.redis_db, password=options.redis_pwd, loop=loop)

    http_client = AsyncHTTPClient()
    # 全局变量
    g.db_pool = db_pool
    g.redis_pool = redis_pool
    g.http_client = http_client

    app = TornadoApplication(http_client)
    http_server = httpserver.HTTPServer(app)
    http_server.listen(options.port)


async def flight_book_expire():
    """预定航班机票过期清理 """

    redis_pool = await aioredis.create_pool(address=options.redis_address, db=options.redis_db,
                                            password=options.redis_pwd, loop=asyncio.get_event_loop())

    time_out = 3*60
    while True:
        try:
            # 获取过期机票
            result = await redis_pool.execute("zrange", "flight_book_zset", 0, 0, "WITHSCORES")
            if not result:
                time.sleep(1)
                continue

            member, score = str(result[0], encoding='utf-8'), float(result[1])
            uid, flight_id, ticket_id = member.split(":")[1].split("_")

            flight_id = int(flight_id)
            ticket_id = int(ticket_id)

            sub_time = time.time() - score
            if sub_time >= time_out:
                redis_pool.execute("zrem", "flight_book_zset", member)
                transaction = []
                transaction.append(
                    ("UPDATE ticket SET `status`=0 WHERE id=%s", (ticket_id,)))
                transaction.append(
                    ("UPDATE flight SET booked_tickets = booked_tickets - 1 WHERE id=%s",
                     (flight_id,)))
                db_pool(transaction)
                continue
            print(time_out, sub_time)
            await asyncio.sleep(time_out - sub_time)
        except Exception as e:
            print("flight book expire error", traceback.format_exc())


if __name__ == "__main__":
    if options.config:
        parse_config_file(options.config)
    print(f"[{datetime.datetime.now()}] services running...")
    future = asyncio.gather(run_server(), flight_book_expire())
    asyncio.get_event_loop().run_until_complete(future)

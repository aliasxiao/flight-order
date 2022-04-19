import functools
import time
import func_timeout
import traceback

from flight_order.globals import g
from flight_order.handler.bases import BaseHandler
from flight_order.error_code import *
from flight_order.response import Response
from flight_order.utils import book_ticket_interface, pay_ticket

BOOK_FLIGHT_TIMEOUT = 2*60
PAY_FLIGHT_TIMEOUT = 2*60
CANCEL_FLIGHT_TIMEOUT = 2*60
TimeOut = 3*60

def auth(method):
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        uid = self.get_json_argument('uid', 0)
        token = self.get_json_argument('token', "")
        token_key = "token_%d" % (uid)

        ori_token = await g.redis_pool.execute("get", token_key)
        if not ori_token or token != ori_token.decode():
            self.set_status(401)
            self.finish({})
        else:
            await method(self, *args, **kwargs)
    return wrapper

class BookTicketHandler(BaseHandler):
    """机票预定接口"""
    @auth
    async def post(self):
        uid = self.get_json_argument('uid')
        flight_id = self.get_json_argument('flight_id')

        # 判断是否为重复提交请求
        book_ticket_id = "Book_Ticket_%d_%d"%(uid, flight_id)
        if await g.redis_pool.execute('setex', book_ticket_id, BOOK_FLIGHT_TIMEOUT, "exist") == 0:
            self.write(Response(PROCESSING).dict())
            return

        # 判断是用户是否存在航班信息(过期判断) //或者这里用redis zset中是否存在未过期的记录
        sql = "SELECT id, status FROM ticket WHERE flight_id=%d AND traveler_id=%d"%(flight_id, uid)
        result = g.db_pool.select(sql)

        if result:
            ticket_id = result[0].get("id")
            status = result[0].get("status")

            if status == 2:
                g.redis_pool.execute('del', book_ticket_id)
                self.write(Response(PAID).dict())
                return

            book_tm = await g.redis_pool.execute("zscore", "flight_book_zset", "user_book:%d_%d_%d"%(uid, flight_id, ticket_id))

            if book_tm:
                book_tm = float(book_tm)
            if status == 1 and book_tm and (time.time() - book_tm) < TimeOut:
                g.redis_pool.execute('del', book_ticket_id)
                self.write(Response(BOOKED).dict())
                return

        # 判断是否有足够机票可预定
        sql = "SELECT `capacity`-`booked_tickets` AS `remaining_ticket_num` FROM flight WHERE id=%d"%(flight_id)
        remaining_ticket_num = 0
        result = g.db_pool.select(sql)

        if result:
            remaining_ticket_num = result[0].get("remaining_ticket_num")

        if remaining_ticket_num <= 0:
            g.redis_pool.execute('del', book_ticket_id)
            self.write(Response(LACKTICKET).dict())
            return

        resp = Response(SUCCESS).dict()
        try:
            # 对接航司,失败就异常，成功下一步
            success = book_ticket_interface()
            if not success:
                raise("book ticket interface fail")
            transaction = []
            transaction.append(("UPDATE ticket SET `status`=1, traveler_id=%s WHERE flight_id=%s AND status=0 LIMIT 1", (uid, flight_id)))
            transaction.append(
                ("SELECT count(id) INTO @ticket_count FROM ticket WHERE flight_id=%s AND traveler_id=%s AND status=1", (flight_id, uid)))
            transaction.append(
                ("UPDATE flight SET booked_tickets = booked_tickets + @ticket_count WHERE id=%s",
                 (flight_id,)))
            g.db_pool.execute_transaction(transaction)
            sql = "SELECT id, status FROM ticket WHERE flight_id=%d AND traveler_id=%d" % (flight_id, uid)
            result = g.db_pool.select(sql)

            if result:
                ticket_id = result[0].get("id")
        except Exception as e:
            #sql = "UPDATE ticket SET `status`=0, uid=0 WHERE WHERE flight_id=%d AND uid=%d AND status=1" % (flight_id, uid)
            print(traceback.format_exc())
            resp = Response(EXCEPTION).dict()
        else:
            await g.redis_pool.execute("zadd", "flight_book_zset", time.time(), "user_book:%d_%d_%d"%(uid, flight_id, ticket_id))
        finally:
            g.redis_pool.execute('del', book_ticket_id)

        self.write(resp)

class PayTicketHandler(BaseHandler):
    """机票支付接口"""
    @auth
    async def post(self):
        uid = self.get_json_argument('uid')
        flight_id = self.get_json_argument('flight_id')
        ticket_id = self.get_json_argument('ticket_id')

        # 判断是否为重复提交请求
        pay_ticket_id = "Pay_Ticket_%d_%d" % (uid, flight_id)
        if await g.redis_pool.execute('setex', pay_ticket_id, PAY_FLIGHT_TIMEOUT, "exist") == 0:
            self.write(Response(PROCESSING).dict())
            return

        # status 1：未支付 2：支付成功
        sql = "SELECT status FROM ticket WHERE id=%d" % (ticket_id)
        result = g.db_pool.select(sql)
        if result:
            status = result[0].get("status")
            if status == 0:
                self.write(Response(NOTBOOK).dict())
                return

            elif status == 2:
                self.write(Response(PAID).dict())
                return
        else:
            self.write({"msg":"ticket not exist"})
            return

        # 判断是用户是否预定航班且未过期
        book_tm = await g.redis_pool.execute("zscore", "flight_book_zset", "user_book:%d_%d_%d"%(uid, flight_id, ticket_id))

        if book_tm:
            book_tm = float(book_tm)
            if (time.time() - book_tm) > TimeOut:
                g.redis_pool.execute('del', pay_ticket_id)
                self.write(Response(NOTBOOK).dict())
                return

        # 暂时删除zset中 uid_flight
        await g.redis_pool.execute("zrem", "flight_book_zset", "user_book:%d_%d_%d"%(uid, flight_id, ticket_id))


        try:
            success = pay_ticket()
            if not success:
                await g.redis_pool.execute("zadd", "flight_book_zset", book_tm, "user_book:%d_%d_%d"%(uid, flight_id, ticket_id))
                self.write(Response(TIMEOUT).dict())
                return
        except func_timeout.exceptions.FunctionTimeout:
            self.write(Response(TIMEOUT).dict())
            return

        resp = Response(SUCCESS).dict()
        try:
            transaction = []
            transaction.append(
                ("UPDATE ticket SET `status`=2 WHERE id=%s", (ticket_id,)))
            transaction.append(
                ("UPDATE flight SET booked_tickets = booked_tickets - 1, sell_tickets = sell_tickets + 1 WHERE id=%s",
                 (flight_id,)))
            g.db_pool.execute_transaction(transaction)

        except Exception:
            # 支付成功，预定失败
            resp = Response(EXCEPTION).dict()
        finally:
            g.redis_pool.execute('del', pay_ticket_id)

        self.write(resp)

class CancelTicketHandler(BaseHandler):
    """机票取消接口"""
    @auth
    async def post(self):
        uid = self.get_json_argument('uid')
        flight_id = self.get_json_argument('flight_id')
        ticket_id = self.get_json_argument('ticket_id')

        # 判断是否为重复提交请求
        cancel_ticket_id = "Cancel_Ticket_%d_%d" % (uid, flight_id)
        if await g.redis_pool.execute('setex', cancel_ticket_id, CANCEL_FLIGHT_TIMEOUT, "exist") == 0:
            self.write(Response(PROCESSING).dict())
            return

        # 判断是否存在机票购买记录
        sql = "SELECT count(1) as buy_ticket FROM ticket WHERE id=%d AND STATUS=2" % (flight_id)
        result = g.db_pool.select(sql)
        if result:
            buy_ticket = result[0].get("buy_ticket")
            if buy_ticket == 0:
                self.write(Response(NOTPAID).dict())
                return

        resp = Response(SUCCESS).dict()
        try:
            transaction = []
            transaction.append(
                ("UPDATE ticket SET `status`=0 WHERE id=%s", (ticket_id,)))
            transaction.append(
                ("UPDATE flight SET sell_tickets = sell_tickets - 1 WHERE id=%s",
                 (flight_id,)))
            g.db_pool.execute_transaction(transaction)
            # 退款?
        except Exception:
            resp = Response(ErrorCode).dict()
        finally:
            g.redis_pool.execute('del', cancel_ticket_id)

        self.write(resp)

class QueryFlightHandler(BaseHandler):
    """航班查询接口"""
    async def get(self):
        sql = "SELECT id, capacity, (capacity - booked_tickets - sell_tickets) AS remaining_tickets, " \
              "base_price*(booked_tickets/capacity * 2 + 1) AS current_ticket_price FROM flight"

        result = g.db_pool.select(sql)
        data = []
        for item in result:
            data.append({
                "flight_id": item.get("id"),
                "capacity": item.get("capacity"),
                "remaining_tickets": item.get("remaining_tickets"),
                "current_ticket_price": item.get("current_ticket_price"),
            })
        self.write(Response(SUCCESS, data).dict())


class LoginHandler(BaseHandler):
    """登陆接口"""
    async def post(self):
        uid = self.get_json_argument('uid')
        g.redis_pool.execute("set", "token_%d"%(uid), "test")
        self.write(Response(SUCCESS, data={"token":"test"}).dict())





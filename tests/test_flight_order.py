import unittest
import requests

from flight_order.handler.handlers import *

TIMEOUT = 3 * 60
url = "http://127.0.0.1:8000"
LOGIN_URL = url+"/login"
BOOK_URL = url+"/createTicketOrder"
PAY_URL = url + "/payTicketOrder"
CANCEL_URL = url + "/cancelTicketOrder"
QUERY_URL = url + "/getflightInfo"

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)

    def test_1_login(self):
        pay_load = {"uid": 1}
        resp = requests.post(url=LOGIN_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

    def test_2_book_ticket(self):
        # 第一次预定
        pay_load = {"uid": 1, "flight_id": 1, "token":"test"}
        resp = requests.post(url=BOOK_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

        # 连续预定
        resp = requests.post(url=BOOK_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(PROCESSING.code, resp.json()['code'])

        # 已预定未过期，继续请求
        time.time(TIMEOUT)
        resp = requests.post(url=BOOK_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(BOOKED.code, resp.json()['code'])


    def test_3_pay_ticket(self):
        # 第一次支付
        pay_load = {"uid": 1, "flight_id": 1, "ticket_id": 1, "token":"test"}
        resp = requests.post(url=PAY_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

        # 连续支付
        resp = requests.post(url=PAY_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(PROCESSING.code, resp.json()['code'])

        # 已预定未过期，继续请求
        time.sleep(TIMEOUT)
        resp = requests.post(url=PAY_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(BOOKED.code, resp.json()['code'])

        # 未预定支付
        pay_load = {"uid": 2, "flight_id": 1, "ticket_id": 2, "token":"test"}
        resp = requests.post(url=PAY_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

    def test_4_cancel_ticket(self):
        # 第一次取消
        pay_load = {"uid": 1, "flight_id": 1, "ticket_id": 1, "token":"test"}
        resp = requests.post(url=CANCEL_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

        # 连续取消
        resp = requests.post(url=CANCEL_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(PROCESSING.code, resp.json()['code'])

        # 无预定，未支付取消
        pay_load = {"uid": 2, "flight_id": 1, "ticket_id": 2, "token":"test"}
        resp = requests.post(url=CANCEL_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(NOTPAID.code, resp.json()['code'])

        # 预定未支付
        pay_load = {"uid": 2, "flight_id": 1, "ticket_id": 2, "token":"test"}
        resp = requests.post(url=BOOK_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])
        resp = requests.post(url=CANCEL_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(NOTPAID.code, resp.json()['code'])

    def test_5_query_flight(self):
        base_price = 100.
        # 预定前
        resp = requests.get(url=QUERY_URL, timeout=2)
        self.assertEqual(SUCCESS.code, resp.json()['code'])
        data = resp.json()['data']
        capacity = data[0]["capacity"]
        remaining_tickets = data[0]["remaining_tickets"]
        current_ticket_price = data[0]["current_ticket_price"]
        self.assertEqual(capacity, remaining_tickets)
        self.assertEqual(base_price, current_ticket_price)
        # 预定
        pay_load = {"uid": 1, "flight_id": 1, "token": "test"}
        resp = requests.post(url=BOOK_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

        resp = requests.get(url=QUERY_URL, timeout=2)
        self.assertEqual(SUCCESS.code, resp.json()['code'])
        data = resp.json()['data']
        capacity = data[0]["capacity"]
        remaining_tickets = data[0]["remaining_tickets"]
        current_ticket_price = data[0]["current_ticket_price"]
        self.assertEqual(capacity - 1, remaining_tickets)
        self.assertEqual(base_price*(1/capacity * 2 + 1), current_ticket_price)

        # 支付
        pay_load = {"uid": 1, "flight_id": 1, "ticket_id": 1, "token": "test"}
        resp = requests.post(url=PAY_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

        resp = requests.get(url=QUERY_URL, timeout=2)
        self.assertEqual(SUCCESS.code, resp.json()['code'])
        data = resp.json()['data']
        capacity = data[0]["capacity"]
        remaining_tickets = data[0]["remaining_tickets"]
        current_ticket_price = data[0]["current_ticket_price"]
        self.assertEqual(capacity - 1, remaining_tickets)
        self.assertEqual(base_price * (0 / capacity * 2 + 1), current_ticket_price)
        # 取消
        pay_load = {"uid": 1, "flight_id": 1, "ticket_id": 1, "token": "test"}
        resp = requests.post(url=CANCEL_URL, json=pay_load, headers={"content-type": "application/json"}, timeout=10)
        self.assertEqual(SUCCESS.code, resp.json()['code'])

        resp = requests.get(url=QUERY_URL, timeout=2)
        self.assertEqual(SUCCESS.code, resp.json()['code'])
        data = resp.json()['data']
        capacity = data[0]["capacity"]
        remaining_tickets = data[0]["remaining_tickets"]
        current_ticket_price = data[0]["current_ticket_price"]
        self.assertEqual(capacity, remaining_tickets)
        self.assertEqual(base_price, current_ticket_price)


if __name__ == '__main__':
    unittest.main()

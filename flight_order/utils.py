import random
import time
from func_timeout import func_set_timeout
from tornado.web import HTTPError
from tornado.util import ObjectDict

class HttpError(HTTPError):
    def __init__(self, status_code=500, error_code=5000, reason=None):
        super(HttpError, self).__init__(status_code, reason)
        self.error_code = error_code
        self.reason = reason

def row_to_obj(row, cur):
    """Convert a SQL row to an object supporting dict and attribute access."""
    obj = ObjectDict()
    for val, desc in zip(row, cur.description):
        obj[desc[0]] = val
    return obj

@func_set_timeout(10)
def book_ticket_interface():
    """通过航司系统订票
    由于需要和航司系统对接，并且其系统比较陈旧，所以预定机票(Ticket)有一个随机 250ms-3000ms 的延时以及一个20%的失败率.
    """
    retry = 6
    success = False

    for i in range(retry):
        # 模拟调用时长
        ms = random.randint(250, 3000)
        time.sleep(ms * 0.001)
        # 模拟成功率
        rand = random.randint(1, 100)
        if rand > 20:
            success = True
            break

    return success


@func_set_timeout(10)
def pay_ticket():
    """用户支付操作
    有一个随机的 250ms-3000ms 的延时以及一个10%的失败率， 客户支付失败之后可以重新尝试支付该订单
    """
    retry = 6
    success = False

    for i in range(retry):
        # 模拟调用时长
        ms = random.randint(250, 3000)
        time.sleep(ms * 0.001)
        # 模拟成功率
        rand = random.randint(1, 100)
        if rand > 10:
            success = True
            break
    return success
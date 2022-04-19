# -*- coding: utf-8 -*-
from flight_order.handler.handlers import *

url_patterns = [
    (r'/login', LoginHandler),
    (r'/createTicketOrder', BookTicketHandler),
    (r'/payTicketOrder', PayTicketHandler),
    (r'/cancelTicketOrder', CancelTicketHandler),
    (r'/getflightInfo', QueryFlightHandler),
]

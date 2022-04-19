class ErrorCode(object):
    def __init__(self, code, msg):
        self._code = code
        self._msg = msg

    @property
    def code(self):
        return self._code

    @property
    def msg(self):
        return self._msg


SUCCESS = ErrorCode(2000, "success")
PROCESSING = ErrorCode(2001, "task processing")
TIMEOUT = ErrorCode(2002, "service time out")
EXCEPTION = ErrorCode(2003, "exception")
BOOKED = ErrorCode(2004, "user have booked")
PAID = ErrorCode(2005, "user have paid")
NOTBOOK = ErrorCode(2006, "user not booked")
NOTPAID = ErrorCode(2007, "user not paid")
LACKTICKET = ErrorCode(2008, "lack ticket")





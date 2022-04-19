import json


class Response(object):
    def __init__(self, error_code, data={}):
        self._code = error_code.code
        self._msg = error_code.msg
        self._data = data

    def _response(self):
        return {"code":self._code, "msg":self._msg, "data":self._data}

    def json(self):
        return json.dumps(self._response())

    def dict(self):
        return self._response()
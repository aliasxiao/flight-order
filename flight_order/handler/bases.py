import json
from tornado.web import RequestHandler

from flight_order.utils import HttpError


class BaseHandler(RequestHandler):

    @property
    def db_pool(self):
        return self.application._mysql_pool

    @property
    def redis_pool(self):
        return self.application._redis_pool

    @property
    def http_client(self):
        return self.application._http_client

    @property
    def request_json(self):
        content_type = self.request.headers.get("Content-Type")
        if content_type and content_type.startswith("application/json"):
            _json_dict = json.loads(self.request.body)
            return _json_dict
        else:
            raise HttpError(400, 1000, reason='Content-Type must be "application/json"')

    def options(self):
        """options请求无需返回包体"""
        self.set_status(204)
        self.finish()

    def write_error(self, status_code, **kwargs):
        """自定义错误json"""
        # 获取send_error中的reason
        reason = kwargs.get('reason', 'unknown')
        error_code = kwargs.get('error_code', 500)

        # 获取 HttpError 中的reason
        if 'exc_info' in kwargs:
            exception = kwargs['exc_info'][1]
            if isinstance(exception, HttpError) and exception.reason:
                reason = exception.reason
                error_code = exception.error_code

        self.write({'error_code': error_code, 'reason': reason})

    _ARG_DEFAULT = object()

    def get_json_argument(self, name, default=_ARG_DEFAULT, init=False):
        """获取json中的请求参数"""
        arg = self.request_json.get(name)

        if init and not arg:
            raise HttpError(403, 1001, reason='Missing argument %s' % name)

        if arg is None:
            if default is self._ARG_DEFAULT:
                raise HttpError(403, 1001, reason='Missing argument %s' % name)
            return default
        return arg


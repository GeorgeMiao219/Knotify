from urllib import parse

import requests

from .base_pusher import BasePusher
from .exception import KnotifyException
from .utils import get_cls_name

__all__ = ["Webhook", "Telegram", "Wechat", "WirePusher"]


class Webhook(BasePusher):
    """
    Pusher class for Webhooks
    """
    def __init__(self, url, show_message=True):
        """
        :param url: webhook url
        :param show_message: if set to True, the pusher will print out status and error message
        """
        super().__init__(show_message)
        self.url = url

    def _push(self, message, **kwargs):
        kwargs.setdefault("content", message)
        return self._check_result(self.s.post(self.url, json=kwargs))

    @property
    def uri(self):
        return self._format_uri(url=self.url)


class Telegram(BasePusher):
    """
    Pusher class for Telegram notification bot
    """
    _api = "https://tgbot.lbyczf.com/sendMessage/{token}"

    def __init__(self, token, show_message=True):
        super().__init__(show_message)
        self.token = token

    def _push(self, message, **kwargs):
        req_body = {
            "text": message,
            "parse_mode": "Markdown"
        }
        req_body.update(kwargs)
        return self._check_result(
            self.s.post(self._api.format(token=self.token), json=req_body))

    @property
    def uri(self):
        return self._format_uri(token=self.token)


class Wechat(BasePusher):
    """
    Pusher class for Wechat notification bot Server Chan (Server酱)
    """
    _api = "http://sc.ftqq.com/{sckey}.send"

    def __init__(self, sckey, show_message=True):
        super().__init__(show_message)
        self.sckey = sckey

    def _push(self, message, **kwargs):
        return self._check_result(
            self.s.get(self._api.format(sckey=self.sckey), params=dict(text=message)))

    @property
    def uri(self):
        return self._format_uri(sckey=self.sckey)


class WirePusher(BasePusher):
    """
    Pusher class for android notification app WirePusher
    """
    _api = "https://wirepusher.com/send"
    _args = ["id", "title", "message", "type", "action", "image_url", "message_id"]
    _mandatory = ["id", "title", "message"]

    def __init__(self, pid, show_message=True):
        super().__init__(show_message)
        self.pid = pid

    def _push(self, message, **kwargs):
        kwargs.setdefault("id", self.pid)
        kwargs.setdefault("title", "Knotify Message")
        req_body, _ = self._build_body(self._args, kwargs, self._mandatory, message=message)
        return self._check_result(self.s.get(self._api, params=req_body))

    @property
    def uri(self):
        return self._format_uri(pid=self.pid)


def get_pusher(uri: str) -> BasePusher:
    """
    Use the URIs generated by Pushers or hand-made URIs to create an Pusher Instance

        e.g. "Knotify://telegram?token=foo"

    Scheme must be `Knotify://`
    netloc is one of the Pushers
    params will be passed in while initialize the Pusher Instances
    """
    result: parse.ParseResult = parse.urlparse(uri)
    cls_name = result.netloc.lower()
    if result.scheme != "knotify":
        raise KnotifyException("Invalid url scheme")
    if cls_name not in all_pushers:
        raise KnotifyException("Invalid class name {}".format(result.netloc))
    cls = all_pushers[cls_name]
    params = dict(parse.parse_qsl(result.query))
    try:
        return cls(**params)
    except Exception as e:
        raise KnotifyException(e)


def register_pusher(pusher):
    """
    Register a pusher so that it can be generated by get_pusher
    Unregistered pusher will lead to KnotifyException
    :param pusher: an instance of custom pusher or the class
    """
    if isinstance(pusher, type):
        all_pushers[get_cls_name(pusher)] = pusher
    elif isinstance(pusher, BasePusher):
        all_pushers[get_cls_name(pusher.__class__)] = pusher.__class__
    else:
        raise KnotifyException("Invalid pusher type {}".format(pusher.__class__))


all_pushers = {cls.__name__.lower(): cls for cls in BasePusher.__subclasses__()}

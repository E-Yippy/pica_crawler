import hashlib
import hmac
import json
import os
from time import time
from urllib.parse import urlencode

import requests
import urllib3

from util import get_header, get_secret_cfg, convert_file_name

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base = "https://picaapi.picacomic.com/"


class Pica:
    Order_Default = "ua"  # 默认
    Order_Latest = "dd"  # 新到旧
    Order_Oldest = "da"  # 旧到新
    Order_Loved = "ld"  # 最多爱心
    Order_Point = "vd"  # 最多指名

    def __init__(self) -> None:
        self.__s = requests.session()
        self.__s.proxies = {"https": get_secret_cfg("https_proxy"), "http": get_secret_cfg("http_proxy")}
        self.__s.verify = False
        self.headers = get_header()

    def http_do(self, method, url, **kwargs):
        kwargs.setdefault("allow_redirects", True)
        header = self.headers.copy()
        ts = str(int(time()))
        raw = url.replace(base, "") + str(ts) + header["nonce"] + method + header["api-key"]
        hc = hmac.new(get_secret_cfg('secret_key').encode(), digestmod=hashlib.sha256)
        hc.update(raw.lower().encode())
        header["signature"] = hc.hexdigest()
        header["time"] = ts
        kwargs.setdefault("headers", header)
        return self.__s.request(method=method, url=url, verify=False, **kwargs)

    def login(self):
        url = base + "auth/sign-in"
        send = {"email": get_secret_cfg('email'), "password": get_secret_cfg('password')}
        __a = self.http_do("POST", url=url, json=send).text
        self.headers["authorization"] = json.loads(__a)["data"]["token"]
        return self.headers["authorization"]

    def comics(self, block="", tag="", order="", page=1):
        args = []
        if len(block) > 0:
            args.append(("c", block))
        if len(tag) > 0:
            args.append(("t", tag))
        if len(order) > 0:
            args.append(("s", order))
        if page > 0:
            args.append(("page", str(page)))
        params = urlencode(args)
        url = f"{base}comics?{params}"
        res = self.http_do("GET", url).json()
        return res

    def leaderboard(self) -> list:
        args = [("tt", 'H24'), ("ct", 'VC')]
        params = urlencode(args)
        url = f"{base}comics/leaderboard?{params}"
        res = self.http_do("GET", url)
        return json.loads(res.content.decode())["data"]["comics"]

    def comic_info(self, book_id):
        url = f"{base}comics/{book_id}"
        res = self.http_do("GET", url=url)
        return json.loads(res.content.decode())

    def episodes(self, book_id, page=1):
        url = f"{base}comics/{book_id}/eps?page={page}"
        return self.http_do("GET", url=url)

    def picture(self, book_id, ep_id, page=1):
        url = f"{base}comics/{book_id}/order/{ep_id}/pages?page={page}"
        return self.http_do("GET", url=url)

    def search(self, keyword, sort=Order_Default, page=1):
        url = f"{base}comics/advanced-search?page={page}"
        return self.http_do("POST", url=url, json={"keyword": keyword, "sort": sort})

    def download(self, name: str, i: int, url: str):
        path = get_secret_cfg('save_path') + convert_file_name(name) + '\\' + str(i + 1).zfill(4) + '.jpg'
        if os.path.exists(path):
            return

        f = open(path, 'wb')
        f.write(self.http_do("GET", url=url).content)
        f.close()

    def categories(self):
        url = f"{base}categories"
        return self.http_do("GET", url=url)

    def favourite(self, book_id):
        url = f"{base}comics/{book_id}/favourite"
        return self.http_do("POST", url=url)

    def my_favourite(self):
        url = f"{base}users/favourite"
        res = self.http_do("GET", url=url)
        return json.loads(res.content.decode())["data"]["comics"]["docs"]

#!/usr/bin/env python3
"""
Date: 2018-06-14 v0.2
Note:
    1. Code cleaned.

    2. Send msg to chatroom added.
"""

import sqlite3
import os
import time
import requests
import json
from local_settings import proxies

__author__ = 'yaochenzhi'
__email__ = 'yaochenzhi.z7@gmail.com'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_DB = os.path.join(BASE_DIR, 'wework_token.db')
WECONFIG_FILE = os.path.join(BASE_DIR, 'wework.cfg')


def ensure_msg(func):
    def _dec(self, *args, **kwargs):
        if not args and 'msg' not in kwargs:
            print("Please provide valid msg!")
        else:
            func(self, *args, **kwargs)
    return _dec


class WeApp(object):

    creator = testor = 'yaochenzhi'

    def __init__(self, app):
        with open(WECONFIG_FILE) as f:
            self.wecfg = json.load(f)

        self.current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.conn = sqlite3.connect(TOKEN_DB)
        self.cursor = self.conn.cursor()

        self.default_msg_data = {
            'toparty': self.wecfg['party']['zjz'],
            # 'touser': None,
            # 'totag': None,
            'agentid': '',
            'msgtype': 'text',
            "text" : {
                "content" : '',
            },
            "safe":0
        }


        self.corpid = self.wecfg['corpid']

        self.app_valid, self.room_valid = False, False
        if app in self.wecfg['app']:
            self.app = app
            self.agentid = self.wecfg['app'][app]['agentid']
            self.corpsecret = self.wecfg['app'][app]['secret']
            self.token_in_db = False
            self.token = self.get_token_from_cache_db()

            if 'chatid' in self.wecfg['app'][app]:
                self.chatid = self.wecfg['app'][app]['chatid']
                self.room_valid = True
            self.app_valid = True
        else:
            print("No app named {} ! Please check or update wework.cfg !".format(app))
        self.app_info = self.app_valid, self.room_valid

    @classmethod
    def format_text_msg(cls, title, content, current_time=None):
        if current_time is None:
            import datetime
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(content, dict):
            cd = content
            content = ''
            for k, v in cd.items():
                content += '{}: {}\n'.format(k, v)
        formatted_text = "{}\n{}\n\n{}".format(title, current_time, content)
        return formatted_text

    def auto_request(self, url, msg_data=None, **kwargs):
        if msg_data:
            print("Msg sending ...")
            r = requests.post(url, data=json.dumps(msg_data), proxies=proxies)
            if json.loads(r.text)['errcode'] != 0:
                print("Msg sent with error! Trying to refresh token from tencent server ...")
                self.get_token_from_server()
                print("Msg resending ...")
                head, _sep, invalid_token = url.rpartition('access_token=')
                url = head + _sep + str(self.token)
                r = requests.post(url, data=json.dumps(msg_data), proxies=proxies)
            print("Msg sent with msg: {}".format(r.text))
        else:
            r = requests.get(url, proxies=proxies)
            return r.text

    @ensure_msg
    def send_app_msg(self, msg, touser=None, toparty=None, test=False, testor=None):
        import copy
        msg_data = copy.deepcopy(self.default_msg_data)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}'.format(self.token)
        if testor:
            touser = testor
        elif test:
            touser = self.testor

        if touser:
            if isinstance(touser, str):
                touser = (touser, )

            elif isinstance(touser, (list, tuple)):
                touser = '|'.join(touser)
            else:
                exit("The 'touser' argument must be a string or a list of string!")

            del msg_data['toparty']
            msg_data['touser'] = touser
        elif toparty:
            msg_data['toparty'] = toparty

        msg_data['text']['content'] = msg
        msg_data['agentid'] = self.agentid
        return self.auto_request(url, msg_data)

    @ensure_msg
    def send_room_msg(self, msg):
        msg_data = {
            "chatid": self.chatid,
            "msgtype":"text",
            "text":{
                "content" : msg,
            },
            "safe":0
        }
        print(msg_data)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/appchat/send?access_token={}'.format(self.token)
        return self.auto_request(url=url, msg_data=msg_data)

    def get_token_from_cache_db(self):
        print("Getting token from cache db ...")
        try:
            r = self.cursor.execute('select token from app_token where app = ?', (self.app, ))
        except sqlite3.OperationalError:
            self.init_db()
            r = self.cursor.execute('select token from app_token where app = ?', (self.app, ))
        token_in_db = r.fetchone()
        if token_in_db:
            self.token = token_in_db[0]
            self.token_in_db = True
        else:
            self.get_token_from_server()
        return self.token

    def get_token_from_server(self):
        print("Fetching token from tencent server ...")
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}'.format(self.corpid, self.corpsecret)
        r = requests.get(url, proxies=proxies)
        return_info = json.loads(r.text)
        if return_info['errcode'] == 0:
            self.token = return_info['access_token']
        if self.token_in_db:
            print("Updating app_token table for app '{}' ...".format(self.app))
            self.cursor.execute("update app_token set token = ?, update_time = ? where app = ?", (self.token, self.current_time, self.app))
        else:
            print("Caching to app_token table for app '{}' ...".format(self.app))
            self.cursor.execute("insert into app_token values (?, ?, ?)", (self.app, self.token, self.current_time))
        self.conn.commit()
        return self.token

    def init_db(self):
        print("Creating app_token table ...")
        self.cursor.execute("create table app_token (app text, token text, update_time text)")
        self.conn.commit()

    def close(self):
        print("Closing connection ...")
        self.cursor.close()
        self.conn.close()
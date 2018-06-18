#!/usr/bin/env python3
"""
Date: 2016-06-14 v0.2
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

with open(WECONFIG_FILE) as f:
    wecfg = json.load(f)

current_time = time.strftime("%Y-%m-%d %H:%M:%S")
conn = sqlite3.connect(TOKEN_DB)
cursor = conn.cursor()

default_msg_data = {
    'toparty': wecfg['party']['zjz'],
    # 'touser': None,
    # 'totag': None,
    'agentid': '',
    'msgtype': 'text',
    "text" : {
        "content" : '',
    },
    "safe":0
}


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
        self.corpid = wecfg['corpid']
        if app in wecfg['app']:
            self.app = app
            self.agentid = wecfg['app'][app]['agentid']
            self.corpsecret = wecfg['app'][app]['secret']
            self.token_in_db = False
            self.token = self.get_token_from_cache_db()

            if 'chatid' in wecfg['app'][app]:
                self.chatid = wecfg['app'][app]['chatid']
        else:
            print("No app named {} ! Please check or update wework.cfg !".format(app))

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
            r = requests.get(url)
            return r.text

    @ensure_msg
    def send_app_msg(self, msg, touser=None, toparty=None, test=False, testor=None):
        import copy
        msg_data = copy.deepcopy(default_msg_data)
        url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}'.format(self.token)
        if testor:
            touser = testor
        elif test:
            touser = self.testor
        if touser:
            del msg_data['toparty']
            msg_data['touser'] = touser
        elif toparty:
            msg_data['toparty'] = toparty

        msg_data['text']['content'] = msg
        msg_data['agentid'] = self.agentid
        self.auto_request(url, msg_data)

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
        self.auto_request(url=url, msg_data=msg_data)

    def get_token_from_cache_db(self):
        print("Getting token from cache db ...")
        try:
            r = cursor.execute('select token from app_token where app = ?', (self.app, ))
        except sqlite3.OperationalError:
            self.init_db()
            r = cursor.execute('select token from app_token where app = ?', (self.app, ))
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
        r = requests.get(url)
        return_info = json.loads(r.text)
        if return_info['errcode'] == 0:
            self.token = return_info['access_token']
        if self.token_in_db:
            print("Updating app_token table for app '{}' ...".format(self.app))
            cursor.execute("update app_token set token = ?, update_time = ? where app = ?", (self.token, current_time, self.app))
        else:
            print("Caching to app_token table for app '{}' ...".format(self.app))
            cursor.execute("insert into app_token values (?, ?, ?)", (self.app, self.token, current_time))
        conn.commit()

    def init_db(self):
        print("Creating app_token table ...")
        cursor.execute("create table app_token (app text, token text, update_time text)")
        conn.commit()

    def close(self):
        print("Closing connection ...")
        cursor.close()
        conn.close()
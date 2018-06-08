#!/usr/bin/env python3
# Date: 2018-05-26 v0.1
# Desc: python3 version
# Used: for sending work text msg to wechat


import sqlite3
import os
import time
import requests
import json
# import logging


__author__ = 'yaochenzhi'

# logging.basicConfig(level=logging.DEBUG,
#     format="%(asctime)s - %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_DB = os.path.join(BASE_DIR, 'wework_token.db')
WECONFIG_FILE = os.path.join(BASE_DIR, 'wework.cfg')

with open(WECONFIG_FILE) as f:
    wecfg = json.load(f)

current_time = time.strftime("%Y-%m-%d %H:%M:%S")
conn = sqlite3.connect(TOKEN_DB)
cursor = conn.cursor()


creator = wecfg['user'][0]

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


class WeApp(object):

    def __init__(self, app):
        self.corpid = wecfg['corpid']
        if app in wecfg['app']:
            self.app = app
            self.agentid = wecfg['app'][app]['agentid']
            self.corpsecret = wecfg['app'][app]['secret']
            self.token_in_db = False
            self.try_refresh_token = True
        else:
            print("App not found ! Please check or update wework.cfg !")
        self.msg_data = default_msg_data
        self.try_get_token_from_server_num = 1


    def send_msg(self, msg, touser=None):
        self.get_token_from_cache_db()
        send_msg_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}'.format(self.token)
        if touser:
            del self.msg_data['toparty']
            self.msg_data['touser'] = touser
        if len(msg) > 0:
            self.msg_data['text']['content'] = msg
            self.msg_data['agentid'] = self.agentid
            print("Msg sending ...")
            r = requests.post(url=send_msg_url, data=json.dumps(self.msg_data))
            print("Msg sent with msg: {}".format(r.text))
            return_info = json.loads(r.text)
            if return_info['errcode'] != 0:
                if self.try_refresh_token:
                    print("Msg sent with error! Trying to refresh token from tencent server ...")
                    self.get_token_from_server()
                    self.try_refresh_token = False
                    print("Msg sending ...")
                    r = requests.post(url=send_msg_url, data=json.dumps(self.msg_data))
                    print("Msg sent with msg: {}".format(r.text))
            print("All is done!")

        else:
            print("Msg is empty !")


    def get_token_from_cache_db(self):
        print("Getting token from cache db ...")
        r = cursor.execute('select token from app_token where app = ?', (self.app, ))
        token_in_db = r.fetchone()
        if token_in_db:
            self.token = token_in_db[0]
            self.token_in_db = True
        else:
            self.get_token_from_server()


    def get_token_from_server(self):
        print("Fetching token from tencent server ...")
        get_token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}'.format(self.corpid, self.corpsecret)
        r = requests.get(url=get_token_url)
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
        cursor.execute("create table app_token (app text, token text, update_time text")
        conn.commit()


    def close(self):
        print("Closing connection ...")
        cursor.close()
        conn.close()
    

        
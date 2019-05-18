#!/usr/bin/python
# -*- coding: UTF-8 -*-
#@author happiren
#@blog  www.happiren.com

import urllib2
import urllib
import httplib
from lxml import etree
import thread
import threading
import os
import time
import json
import requests
import os
import shutil
import execjs
from requests.cookies import RequestsCookieJar


request_headers = {
    'connection': "keep-alive",
    'cache-control': "no-cache",
    'upgrade-insecure-requests': "1",
    'user-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",
    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    'accept-language': "zh-CN,en-US;q=0.8,en;q=0.6"
}

def translate(query, fro, to, cookieDict):
    node = execjs.get();
    file = "baidufanyi.js";
    jsScript = open(file, "r").read(); #encoding='utf-8'
    ctx = node.compile(jsScript);
    token, u = prepare_param(cookieDict);
    js = 'e("{0}", "{1}")'.format(query, u);
    sign = ctx.eval(js);

    #经过测试header中cookie必须添加BAIDUID方可正常使用
    headers = {
        'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        'accept-language': "zh-CN,en-US;q=0.8,en;q=0.6",
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",

    }
    #添加cookie
    if len(cookieDict) > 0:
        cookie = "";
        for key in cookieDict:
            cookie = cookie + key+"="+cookieDict[key]+";";
        headers['cookie'] = cookie

    data = {
        'from':fro,
        'to': to,
        "query": query,
        "transtype": 'translang',
        "simple_meas_flag": '3',
         "sign": sign,
        'token': token
    }
    url = "https://fanyi.baidu.com/v2transapi"
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == 200:
        return response.content;
    return None;

import re;
def prepare_param(cookieDict):
    url = "https://fanyi.baidu.com/translate";
    headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            'accept-language': "zh-CN,en-US;q=0.8,en;q=0.6",
            'User-agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",

        }
    if len(cookieDict) > 0:
        cookie = "";
        for key in cookieDict:
            cookie = cookie + key+"="+cookieDict[key]+";";
        headers['cookie'] = cookie
    response = requests.get(url, headers=headers);
    html = response.text;
    windows_gtk = re.findall(";window.gtk = (.*?);</script>", html)[0][1:-1];
    token = re.findall(r"token: '(.*?)',", html)[0];
    #print html;
    return token, windows_gtk;

def get_fanyi_cookie():
    url = "https://fanyi.baidu.com";
    response = requests.get(url);
    return requests.utils.dict_from_cookiejar(response.cookies)
baiduCookies  = get_fanyi_cookie();

content = translate("friend",'en', 'zh', baiduCookies)
print content
json = json.loads(content);
print json;
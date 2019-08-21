#!/usr/bin/python
# -*- coding: UTF-8 -*-
#@author happiren
#@blog  www.happiren.com


import urllib
from lxml import etree
import threading
import os
import time
import json
import requests
import os
import shutil
import execjs
from requests.cookies import RequestsCookieJar
import re;
import random;

import mysqlManager;

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
    jsScript = open(file, "r", encoding="utf-8").read();  #encoding='utf-8'
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
    if response.status_code == 401:
        print("被百度反爬虫啦，啦啦啦啦")
        return None
    return None;


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

def convert2word(json_data):
    en_word = {"word":None, "words":None, "word_done":None, "word_past":None, "word_ing":None, "word_third":None,"word_er":None, "word_est":None, "ph_en":None,"ph_us":None, "explains":None, "tts_en":None, "tts_us":None}
    if "simple_means" not in json_data["dict_result"]:
        return en_word;
    #解释
    symbol_means = json_data["dict_result"]["simple_means"];
    symbols = symbol_means["symbols"]
    en_word["word"] = symbol_means["word_name"]
    #获取解释
    for item in symbols:
        explains = "";
        en_word["ph_en"] =  item["ph_en"]
        en_word["ph_us"] = item["ph_am"]
        parts = item["parts"]
        for part in parts:
            #explain = part["part"]
            explain = ""
            for mean in part["means"]:
                explain = explain + " " + mean + ";"
            explains = explains + explain + "|"
        en_word["explains"] = explains[:-1].strip(); #去掉最后一个字符,并去除左右空格
    if "exchange" in symbol_means:
        exchange = symbol_means["exchange"]
        for key in exchange.keys():
            if key == "word_third":
                if type(exchange[key]) == type([]):
                    en_word["word_third"] = str(exchange[key][0]);
            elif key == "word_ing":
                if type(exchange[key]) == type([]):
                    en_word["word_ing"] = str(exchange[key][0]);
            elif key == "word_done":
                if type(exchange[key]) == type([]):
                    en_word["word_done"] = str(exchange[key][0]);
            elif key == "word_past":
                if type(exchange[key]) == type([]):
                    en_word["word_past"] = str(exchange[key][0]);
            elif key == "word_pl": #复数
                if type(exchange[key]) == type([]):
                    en_word["words"] = str(exchange[key][0]);
            elif key == "word_er":  # 复数
                if type(exchange[key]) == type([]):
                    en_word["word_er"] = str(exchange[key][0]);
            elif key == "word_est":  # 复数
                if type(exchange[key]) == type([]):
                    en_word["word_est"] = str(exchange[key][0]);
    return en_word

#获取例句
def getExampleSentence(json_data):
    en_sentence = {"tags":[], "word":""}
    if "simple_means" not in json_data["dict_result"]:
        return en_sentence;
    dict_result = json_data["dict_result"];
    en_sentence["word"] = dict_result["simple_means"]["word_name"]
    if "oxford" in dict_result: #如果有牛津词典
        oxford = json_data["dict_result"]["oxford"]
        if "entry" in oxford:
            entrys = oxford["entry"][0]
            if entrys["tag"] == "entry":
                data_entrys = entrys["data"];
                for data_entry in data_entrys:
                    if data_entry["tag"] == "h-g":  # 总共有几个词性
                        for data in data_entry["data"]:
                            if data["tag"] == "p":
                                pass;
                                #en_sentence["tags"].append(data["p"]);
                    #if data_entry["tag"] == "p-g": #例句
                    tag = "";
                    for data in data_entry["data"] :
                        if "tag" in data :
                            count = 0;
                            if data["tag"] == "p": #标签
                                tag = data["p"];
                                en_sentence["tags"].append(tag);
                                en_sentence[tag] = []
                            elif data["tag"] == "sd-g": #例句
                                sentences =  data["data"];
                                for sentence in sentences:
                                    if sentence["tag"] == "n-g":
                                        sentence_data_list = sentence["data"];
                                        for sentence_data in sentence_data_list:
                                            if sentence_data["tag"] == "x":
                                                en = sentence_data["enText"];
                                                cn = sentence_data["chText"];
                                                en_sentence[tag].append({"en":en, "cn":cn})
                                                count = count + 1;
                                                if count > 3:
                                                    break;
                            elif data["tag"] == "n-g":
                                sentences = data["data"];
                                for sentence_data in sentences:
                                    if sentence_data["tag"] == "p":
                                        tag = sentence_data["p"];
                                        en_sentence["tags"].append(tag);
                                        en_sentence[tag] = []
                                    elif sentence_data["tag"] == "x":
                                        en = sentence_data["enText"];
                                        cn = sentence_data["chText"];
                                        if tag == "":
                                            tag = "default";
                                            if tag not in en_sentence["tags"]:
                                                en_sentence["tags"].append(tag);
                                                en_sentence[tag] = []
                                        en_sentence[tag].append({"en": en, "cn": cn})
                                        count = count + 1;
                                        if count > 3:
                                            break;
    if True: #双语例句
        double = json_data["liju_result"]["double"]
        if double != "":
            en_sentence["tags"].append("double")  # 双语例句标签
            double_json = json.loads(double)
            en_sentence["double"] = []
            for double_item in double_json:
                english = ""
                chinese = ""
                english_list = double_item[0]
                chinese_list = double_item[1]
                for english_item in english_list:
                    english = english + english_item[0] + " "
                for chinese_item in chinese_list:
                    chinese = chinese + chinese_item[0]
                english = english.strip()
                en_sentence["double"].append({"en": english, "cn": chinese})
    return en_sentence;



#
# content = translate("high",'en', 'zh', baiduCookies)
# print (content)
# print("str data:\r\n")
# print (str(content, encoding = "utf-8"))
# with open("data.txt", 'w') as f:
#     f.write( str(content, encoding = "utf-8")  )
#     f.close()
# json_data = json.loads(content);
# en_word = convert2word(json_data)
# sentences = getExampleSentence(json_data);
# print(json.dumps(sentences));
# #print(json.dumps(en_word));


def insertSentence2db(sentences, mysql):
    en_sentence = [];
    for tag in sentences["tags"]:
        count = 0;
        word = sentences["word"]
        for sentence in sentences[tag]:
            en_sentence = {};
            en_sentence["word"] = word
            en_sentence["fro"] = "baidu"
            en_sentence["third_id"] = None;
            en_sentence["part"] = tag;
            en_sentence["chinese"] = sentence["cn"]
            en_sentence["english"] = sentence["en"]
            mysql.enqueueSentence(en_sentence)
            count = count + 1
            if count >= 3:
                count = 0;
                break;

if __name__ == '__main__':
    mysql = mysqlManager.MysqlManager(5)
    baiduCookies = get_fanyi_cookie();
    f = open('lexicon.txt', "r")
    f_rm_duplicate = open("lexicon_rm_duplicate.txt", "w")
    word_set = set()
    for line in f:
        line = line.replace("\n", "");
        word = line.replace("\r", "");
        if word in word_set:
            print("duplicate:"+word)
            pass
        else:
            word_set.add(word)
            f_rm_duplicate.write(word+str("\n"))
    f_rm_duplicate.close()

    f_lexicon = open('lexicon_rm_duplicate.txt', "r")
    count = 0
    skip_line = 0  #跳过多少行

    for line in f_lexicon:
        line = line.replace("\n", "");
        word = line.replace("\r", "");
        count = count + 1;
        if count <= skip_line:
            continue;
        print(str(count) +  " " + word)
        sleep = random.uniform(0, 1)
        if mysql.hasSentence(word): #有例句就不重复采集了，有例句也表示有单词和词汇了
            continue;
        time.sleep(sleep);  # 随机延时
        content = translate(word, 'en', 'zh', baiduCookies)
        print(str(content, encoding="utf-8"))
        json_data = json.loads(content);
        en_word = convert2word(json_data)
        if en_word["word"] == None:
            with open('error_word.txt', 'a+') as f:
                f.write(word+str("\n"))
                f.close();
        sentences = getExampleSentence(json_data);
        insertSentence2db(sentences, mysql)
        if word.find(" ") >= 0:
            en_word = convert2word(json_data)
            mysql.enqueueWord(en_word)




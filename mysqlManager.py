#!/usr/bin/python
# -*- coding: UTF-8 -*-

import MySQLdb
import mysql.connector
from mysql.connector import errorcode
from mysql.connector import pooling
import hashlib
import time

class MysqlManager:

    DB_NAME = 'english'
    SERVER_IP = '127.0.0.1'
    DB_USER = 'root'
    DB_PASSWORD = '123456'

    TABLES = {}
    TABLES['en_word'] = (
        "DROP TABLE IF EXISTS `en_word`;"
        "CREATE TABLE `en_word`  ("
          "`id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,"
          "`word` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '英语单词',"
          "`words` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '复数',"
          "`word_done` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '过去分词',"
        "`word_past` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '过去式',"
        "`word_ing` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '进行时',"
        " `word_third` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '第三人称单数',"
        " `word_er` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '比较级',"
        " `word_est` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '最高级',"
        " `ph_en` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '英式音标',"
        " `ph_us` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '美式音标',"
        " `explains` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '中文翻译',"
        " `tts_en` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '英式音标发音',"
        " `tts_us` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '美式音标发音',"
        " `created_at` timestamp(0) NULL DEFAULT NULL COMMENT '提交时间',"
        " `updated_at` timestamp(0) NULL DEFAULT NULL COMMENT '更新时间',"
        " `deleted_at` timestamp(0) NULL DEFAULT NULL COMMENT '删除时间',"
        " PRIMARY KEY (`id`) USING BTREE,"
        " UNIQUE INDEX `word`(`word`) USING BTREE"
        ") ENGINE = InnoDB AUTO_INCREMENT = 6231 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '英语单词表' ROW_FORMAT = Dynamic;"
        ")")

    TABLES['en_sentence'] = (
            "DROP TABLE IF EXISTS `en_word_sentence`;"
            "CREATE TABLE `en_word_sentence`  ("
             " `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,"
            " `word` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '英语单词',"
            " `fro` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '例句来源',"
            " `third_id` int(10) UNSIGNED NULL DEFAULT NULL COMMENT '百度或者有道例句ID',"
            " `part` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '词性',"
            " `english` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '英语句子',"
            " `chinese` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '中文翻译',"
            " `created_at` timestamp(0) NULL DEFAULT NULL COMMENT '提交时间',"
            " `updated_at` timestamp(0) NULL DEFAULT NULL COMMENT '更新时间',"
            " `deleted_at` timestamp(0) NULL DEFAULT NULL COMMENT '删除时间',"
            " PRIMARY KEY (`id`) USING BTREE,"
            " INDEX `word`(`word`) USING BTREE"
            ") ENGINE = InnoDB AUTO_INCREMENT = 105 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '英语单词例句表' ROW_FORMAT = Dynamic;"
    )


    def __init__(self, max_num_thread):
        try:
            cnx = mysql.connector.connect(host=self.SERVER_IP, user=self.DB_USER, passwd=self.DB_PASSWORD)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print ('Create Error ' + err.msg)
            exit(1)

        cursor = cnx.cursor()

        try:
            cnx.database = self.DB_NAME
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_BAD_DB_ERROR:
                #self.create_database(cursor)
                cnx.database = self.DB_NAME
                #self.create_tables(cursor)
            else:
                print(err)
                exit(1)
        finally:
            cursor.close()
            cnx.close()

        dbconfig = {
            "database": self.DB_NAME,
            "user":     self.DB_USER,
            "host":     self.SERVER_IP,
            "password": self.DB_PASSWORD
        }
        self.cnxpool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "mypool",
                                                          pool_size = max_num_thread,
                                                          **dbconfig)


    def create_database(self, cursor):
        try:
            cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(self.DB_NAME))
        except mysql.connector.Error as err:
            print("Failed creating database: {}".format(err))
            exit(1)

    def create_tables(self):
        con = self.cnxpool.get_connection()
        cursor = con.cursor()
        for name, ddl in self.TABLES.iteritems():
            try:
                cursor.execute(ddl)
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print ('create tables error ALREADY EXISTS')
                else:
                    print ('create tables error ' + err.msg)
            else:
                print ('Tables created')
        cursor.close()
        con.close()


    def enqueueWord(self, en_word):
        con = self.cnxpool.get_connection()
        cursor = con.cursor()
        try:
            add_sql = ("INSERT INTO en_word (word, words, word_done, word_past, word_ing, word_third, word_er, word_est, ph_en, ph_us, explains, tts_en, tts_us, created_at, updated_at)  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
            data = (en_word["word"], en_word["words"], en_word["word_done"], en_word["word_past"], en_word["word_ing"], en_word["word_third"], en_word["word_er"], en_word["word_est"], en_word["ph_en"], en_word["ph_us"], en_word["explains"], en_word["tts_en"],en_word["tts_us"],time.strftime('%Y-%m-%d %H:%M:%S'), time.strftime('%Y-%m-%d %H:%M:%S'))
            cursor.execute(add_sql, data)
            con.commit()
        except mysql.connector.Error as err:
            print ('inser data error: ' + err.msg)
            return
        finally:
            cursor.close()
            con.close()

    def enqueueSentence(self, en_sentence):
        con = self.cnxpool.get_connection()
        cursor = con.cursor()
        try:
            add_image = ("INSERT INTO en_word_sentence (word, fro, third_id, part, english, chinese, created_at, updated_at)  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            data_iamge = (en_sentence["word"],  en_sentence["fro"], en_sentence["third_id"],en_sentence["part"], en_sentence["english"], en_sentence["chinese"], time.strftime('%Y-%m-%d %H:%M:%S'), time.strftime('%Y-%m-%d %H:%M:%S'))
            cursor.execute(add_image, data_iamge)
            con.commit()
        except mysql.connector.Error as err:
            print ('inser data error: ' + err.msg)
            return
        finally:
            cursor.close()
            con.close()

    def hasSentence(self, word):
        con = self.cnxpool.get_connection()
        cursor = con.cursor(dictionary=True)
        try:
            query = "SELECT id  FROM `en_word_sentence` WHERE word = '%s'"%(word)

            cursor.execute(query)
            row = cursor.fetchall()
            con.commit()
            if len(row) > 0:
                return True
            else:
                return False

            # return row
        except mysql.connector.Error as err:
            print ('hasSentence() ' + err.msg)
            return None
        finally:
            cursor.close()
            con.close()


    def dequeueWord(self, msg_id):
        con = self.cnxpool.get_connection()
        cursor = con.cursor(dictionary=True)
        try:
            query = "SELECT `id`, `name`, `msg_id`, `msg_title`,  `print_num`  FROM guguji_images WHERE msg_id=%d"%(msg_id)

            cursor.execute(query)
            if cursor.rowcount is 0:
                return None
            row = cursor.fetchall()
            con.commit()
            return row
        except mysql.connector.Error as err:
            print ('dequeueWord() ' + err.msg)
            return None
        finally:
            cursor.close()
            con.close()



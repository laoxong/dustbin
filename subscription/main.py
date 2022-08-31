#!/usr/bin/python

# This is a simple echo bot using the decorator mechanism.
# It echoes any incoming text messages.
import asyncio
import logging
import sqlite3
import os

import telebot
import re
from telebot.async_telebot import AsyncTeleBot
from dotenv import load_dotenv
load_dotenv()

conn = sqlite3.connect('user.db')
bot = AsyncTeleBot(os.getenv('bot_token'))
chat_id = os.getenv("chat_id")
logging.basicConfig(format='%(asctime)s: %(levelname)s %(name)s | %(message)s',
                    level=logging.INFO)
logger = telebot.logger.setLevel(logging.INFO)



# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(message, """
/help 帮助
/renew 回复一个用户来使他续费30天
/me 获取你的信息
/info 获取被回复的用户信息
/update 更新用户状态 @用户名 日期
""")


# 处理新用户
@bot.message_handler(content_types=['new_chat_members'])
async def newMemmber(message):
    sql = "REPLACE INTO user VALUES({id},date(CURRENT_DATE, '+30 day'),'user','{username}')".format(id=message.json['new_chat_member']['id'], username = message.json['new_chat_member']['username'])
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    await bot.send_message(chat_id, "欢迎新用户：{}".format(message.json['new_chat_member']['first_name']))

# 续费
@bot.message_handler(commands=['renew'])
async def renew(message):
    a = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if a.status in ['administrator', 'creator']:
        if message.reply_to_message is not None:
            sql = "UPDATE user SET expiredtime=DATE(expiredtime, '+30 day') WHERE id={}".format(
                message.reply_to_message.from_user.id)
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
            expiretime = cur.execute("SELECT expiredtime FROM user WHERE id={}".format(message.reply_to_message.from_user.id)).fetchall()[0][0]
            await bot.reply_to(message, "{}已续费30天\n到期时间为:{}".format(message.reply_to_message.from_user.username, expiretime))
        else:
            await bot.reply_to(message, "请回复一个用户")
    else:
        await bot.reply_to(message, "您不是管理员")

#我的信息
@bot.message_handler(commands=['me'])
async def getmyinfo(message):
    sql = "SELECT expiredtime FROM user WHERE id = {}".format(message.from_user.id)
    cur = conn.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    if len(res) != 0:
        await bot.reply_to(message, "你的信息为:\n用户名:@{}\n到期时间:{}".format(message.from_user.username, res[0][0]))
    else:
        sql = "INSERT INTO user VALUES({id},date(CURRENT_DATE, '+30 day'),'user', '{username}')".format(id=message.from_user.id, username = message.from_user.username)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        await bot.reply_to(message, "什么,数据库中没有你,竟然有漏网之鱼\n不管怎样,你现在入库了")

#更新用户过期时间到指定月份
@bot.message_handler(commands=['update'])
async def update(message):
    a = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if a.status in ['administrator', 'creator']:
        text = message.text
        text = re.sub(' +', ' ', text)
        text = text.split(' ')
        if len(text) == 3:
            p1 = "((((19|20)\d{2})-(0?(1|[3-9])|1[012])-(0?[1-9]|[12]\d|30))|(((19|20)\d{2})-(0?[13578]|1[02])-31)|(((19|20)\d{2})-0?2-(0?[1-9]|1\d|2[0-8]))|((((19|20)([13579][26]|[2468][048]|0[48]))|(2000))-0?2-29))$"
            date = re.search(p1, message.text)[0]
            if date is not None:
                cur = conn.cursor()
                sql = "UPDATE user SET expiredtime='{time}' WHERE username='{username}'".format(time = date, username = text[1].replace("@", ""))
                cur.execute(sql)
                conn.commit()
                await bot.reply_to(message, "已更新用户{}\n到期时间为:{}".format(text[1], date))
            else: 
                await bot.reply_to(message, "格式错误")
    else:
        await bot.reply_to(message, "您不是管理员")

#被回复用户的信息
@bot.message_handler(commands=['info'])
async def getinfo(message):
    a = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if a.status in ['administrator', 'creator']:
        if message.reply_to_message is not None:
            sql = "SELECT expiredtime FROM user WHERE id = {}".format(message.reply_to_message.from_user.id)
            cur = conn.cursor()
            cur.execute(sql)
            res = cur.fetchall()
            if len(res) != 0:
                await bot.reply_to(message, "用户名:@{}\n到期时间:{}".format(message.reply_to_message.from_user.username, res[0][0]))
            else:
                await bot.reply_to(message, "用户名:@{}\n到期时间:暂无".format(message.reply_to_message.from_user.username))
        else:
            #获取@的用户
            message.text = re.sub("/info|@test_bot", "", message.text)
            if message.text.find('@') != -1 and len(message.text) > 1:
                username = message.text[message.text.find('@') + 1:]
                sql = "SELECT id,expiredtime FROM user WHERE username = '{}'".format(username)
                cur = conn.cursor()
                cur.execute(sql)
                res = cur.fetchall()
                if res != []:
                    await bot.reply_to(message, "用户名: @{}\n到期时间:{}".format(username, res[0][1]))
                else:
                    await bot.reply_to(message, "未找到用户用户: @{}".format(username))
            elif message.text == '':
                await bot.reply_to(message, "请回复一个用户")
    else:
        await bot.reply_to(message, "您不是管理员")


try:
    asyncio.run(bot.polling(interval=5))
except Exception as e:
    conn.close()
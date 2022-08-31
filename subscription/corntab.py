import sqlite3
import telebot
import os
from dotenv import load_dotenv
load_dotenv()

bot = telebot.TeleBot(os.getenv('bot_token'))
chat_id=os.getenv("chat_id")
conn = sqlite3.connect('user.db')
#删除过期用户
def removeExpiredUser():
    bot.send_message(os.getenv('masterid'), "开删除过期用户任务~")
    sql = "SELECT id FROM user WHERE expiredtime = date(CURRENT_DATE) AND usertype is 'user'"
    cur = conn.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    if len(res) != 0:
        kicked_user = []
        for i in res:
            bot.kick_chat_member(os.getenv('chat_id'), i[0])
            kicked_user.append(i[0])
            sql = "DELETE FROM user WHERE id = {}".format(i[0])
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
    bot.send_message(chat_id, "用户{}已删除".format(kicked_user))

#提醒续费
def remindrenew():
    bot.send_message(os.getenv('masterid'), "开始提醒续费任务~")
    sql = "SELECT id,username FROM user WHERE expiredtime < date(CURRENT_DATE,'+5 day') AND usertype is 'user'"
    cur = conn.cursor()
    cur.execute(sql)
    text = "以下用户还剩5天到期\n"
    res = cur.fetchall()
    if res != []:
        for i,v in res:
            text = text + "@"+ v + " "
        bot.send_message(chat_id, text)

def notice():
    bot.send_message(os.getenv('masterid'), "计划任务执行成功~")

bot.send_message(os.getenv('masterid'), "开始执行计划任务~")
try:
    removeExpiredUser()
    remindrenew()
    notice()
except Exception as e:
    bot.send_message(os.getenv('masterid'), "计划任务执行失败~")
    bot.send_message(os.getenv('masterid'), e)
    raise e
finally:
    conn.close()
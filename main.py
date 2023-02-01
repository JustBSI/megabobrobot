token = open('token.txt').read()
import telebot
import sqlite3

con = sqlite3.connect("people.db", check_same_thread=False)
cursor = con.cursor()

# new table creation
with con:
    data = con.execute("SELECT count(*) FROM sqlite_master WHERE TYPE='table' and NAME='people'")
    for row in data:
        if row[0] == 0:
            cursor.execute("""CREATE TABLE people
                            (user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            state TEXT)
                            """)

state = dict()
bot = telebot.TeleBot(token)


# reaction on "start" command
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)  # open keyboard
    keyboard.row('Показать ориентацию', 'Изменить ориентацию', 'Удалить ориентацию')
    bot.send_message(message.from_user.id, "Привет, " + message.from_user.first_name + "!", reply_markup=keyboard)


# reaction on keyboard buttons
@bot.message_handler(content_types=['text'])
def get_state(message):
    if message.text == 'Изменить ориентацию':
        keyboard = telebot.types.ReplyKeyboardMarkup(True)
        keyboard.row('Гей', 'Не гей')
        bot.send_message(message.from_user.id, "Укажите ориентацию:", reply_markup=keyboard)
        bot.register_next_step_handler(message, set_state)
    elif message.text == 'Удалить ориентацию':
        cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
        if cursor.fetchone() is None:
            bot.send_message(message.from_user.id, "Я о Вас и так ничего не знаю!")
        else:
            cursor.execute("DELETE FROM people WHERE user_id=(?)", [message.from_user.id])
            con.commit()
            bot.send_message(message.from_user.id, "Информация о Вашей ориентации удалена!")
    elif message.text == 'Показать ориентацию':
        cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
        if cursor.fetchone() is None:
            bot.send_message(message.from_user.id, "Вы ещё не указали, гей Вы или нет!")
        else:
            cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
            bot.send_message(message.from_user.id, "Ваша ориентация: " + ''.join(cursor.fetchone()))


def set_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    keyboard.row('Меню')
    state[message.from_user.id] = message.text
    cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO people (user_id, state) VALUES (?, ?)", (message.from_user.id, message.text))
        con.commit()
    else:
        cursor.execute("UPDATE people SET state =(?) WHERE user_id=(?)", (message.text, message.from_user.id))
        con.commit()
    bot.send_message(message.from_user.id, "Отлично! Теперь Ваша ориентация: " + message.text, reply_markup=keyboard)
    bot.register_next_step_handler(message, start)


bot.polling(none_stop=True, interval=0)

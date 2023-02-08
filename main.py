token = open('token.txt').read()
import telebot
import sqlite3
from datetime import datetime
from telebot import types

current_datetime = datetime.now()
bot = telebot.TeleBot(token)
database = sqlite3.connect("database.db", check_same_thread=False)
database_cursor = database.cursor()


# new database and table creation function
def create_table(name, request):
    with database:
        data = database.execute(f"SELECT count(*) FROM sqlite_master WHERE TYPE='table' and NAME='{name}'")
        for row in data:
            if row[0] == 0:
                database_cursor.execute(f"""CREATE TABLE {name} ({request})""")


create_table("people",
             """user_id INTEGER PRIMARY KEY AUTOINCREMENT,
             state NCHAR""")

create_table("notes",
             """id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INT,
             datetime DATETIME,
             note NCHAR""")


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)  # open keyboard
    keyboard.row('Показать состояние', 'Изменить состояние')
    keyboard.row('Удалить состояние', 'Добавить заметку')
    keyboard.row('Показать заметки')
    bot.send_message(message.from_user.id, "Привет, " + message.from_user.first_name + "! Выберите нужное действие:",
                     reply_markup=keyboard)


def show_notes(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    database_cursor.execute(f"SELECT * FROM notes WHERE user_id={message.from_user.id}")
    if database_cursor.fetchone():
        database_cursor.execute(f"SELECT id, datetime, note FROM notes WHERE user_id={message.from_user.id}")
        for data in database_cursor.fetchall():
            note_id = f"ID заметки: {data[0]}"
            note_datetime = f"\nДата и время заметки: {data[1]}"
            note_text = f"\nТекст заметки: {data[2]}"
            bot.send_message(message.from_user.id, note_id + note_datetime + note_text)
        bot.send_message(message.from_user.id, "Это всё что мне удалось найти.", reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, "Вы ещё не добавили ни одной заметки!", reply_markup=keyboard)


def add_note(message):
    bot.send_message(message.from_user.id, "Напишите заметку:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, write_note)


def write_note(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    database_cursor.execute("INSERT INTO notes (user_id, datetime, note) VALUES (?, ?, ?)",
                            (message.from_user.id, current_datetime, message.text))
    database.commit()
    bot.send_message(message.from_user.id, "Заметка сохранена!", reply_markup=keyboard)


def change_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Болею', 'Не болею')
    bot.send_message(message.from_user.id, "Укажите состояние:", reply_markup=keyboard)
    bot.register_next_step_handler(message, set_state)


def delete_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    database_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
    if database_cursor.fetchone() is None:
        bot.send_message(message.from_user.id, "Я о Вас и так ничего не знаю!", reply_markup=keyboard)
    else:
        database_cursor.execute("DELETE FROM people WHERE user_id=(?)", [message.from_user.id])
        database.commit()
        bot.send_message(message.from_user.id, "Информация о Вашем состоянии удалена!", reply_markup=keyboard)


def show_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    database_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
    if database_cursor.fetchone() is None:
        bot.send_message(message.from_user.id, "Вы ещё не указали, больны Вы или нет!", reply_markup=keyboard)
    else:
        database_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
        bot.send_message(message.from_user.id, "Ваше состояние: " + ''.join(database_cursor.fetchone()),
                         reply_markup=keyboard)


actions = {
    'Изменить состояние': change_state,
    'Удалить состояние': delete_state,
    'Показать состояние': show_state,
    'Добавить заметку': add_note,
    'Показать заметки': show_notes,
    'Меню': start
}


@bot.message_handler(content_types=['text'])
def action(message):
    actions[message.text](message)


def set_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    database_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
    if database_cursor.fetchone() is None:
        database_cursor.execute("INSERT INTO people (user_id, state) VALUES (?, ?)",
                                (message.from_user.id, message.text))
        database.commit()
    else:
        database_cursor.execute("UPDATE people SET state =(?) WHERE user_id=(?)", (message.text, message.from_user.id))
        database.commit()
    bot.send_message(message.from_user.id, "Отлично! Теперь Ваше состояние: " + message.text, reply_markup=keyboard)
    bot.register_next_step_handler(message, start)


bot.infinity_polling()

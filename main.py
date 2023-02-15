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


def change_state(user_id, state):
    database_cursor.execute(f"SELECT * FROM people WHERE user_id={user_id}")
    if database_cursor.fetchone() is None:
        database_cursor.execute(f"INSERT INTO people (user_id, state) VALUES ({user_id}, '{state}')")
    else:
        database_cursor.execute(f"UPDATE people SET state = '{state}' WHERE user_id={user_id}")
    database.commit()


create_table("people",
             """user_id INTEGER PRIMARY KEY AUTOINCREMENT,
             health NCHAR,
             state NCHAR""")

create_table("notes",
             """id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INT,
             datetime DATETIME,
             note NCHAR""")


@bot.message_handler(commands=['start'])
def start(message):
    change_state(message.from_user.id, "start")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)  # open keyboard
    keyboard.row('Состояния', 'Заметки')
    bot.send_message(message.from_user.id, f"Привет, {message.from_user.first_name}! Выбери нужный раздел:",
                     reply_markup=keyboard)


def work_with_health(message):
    change_state(message.from_user.id, "work_with_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Показать', 'Изменить', 'Удалить')
    keyboard.row('Меню')
    bot.send_message(message.from_user.id, "Выбери действие:", reply_markup=keyboard)


def change_health(message):
    change_state(message.from_user.id, "change_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Болею', 'Не болею')
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Укажи состояние:", reply_markup=keyboard)
    bot.register_next_step_handler(message, set_health)


def set_health(message):
    change_state(message.from_user.id, "set_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if message.text != 'Назад':
        database_cursor.execute(f"UPDATE people SET health='{message.text}' WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, f"Отлично! Теперь твоё состояние: {message.text}", reply_markup=keyboard)
        bot.register_next_step_handler(message, action)
    else:
        work_with_health(message)


def delete_health(message):
    change_state(message.from_user.id, "delete_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    database_cursor.execute(f"SELECT health FROM people WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()[0]
    if data is None:
        bot.send_message(message.from_user.id, "Я о тебе и так ничего не знаю!", reply_markup=keyboard)
    else:
        database_cursor.execute(f"UPDATE people SET health=NULL WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, "Информация о твоём состоянии удалена!", reply_markup=keyboard)


def show_health(message):
    change_state(message.from_user.id, "show_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    database_cursor.execute(f"SELECT health FROM people WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()[0]
    if data is None:
        bot.send_message(message.from_user.id, "Вы ещё не указали, больны Вы или нет!", reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, f"Твоё состояние: {''.join(data)}", reply_markup=keyboard)


def work_with_notes(message):
    change_state(message.from_user.id, "work_with_notes")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Показать', 'Добавить', 'Изменить')
    keyboard.row('Удалить по ID', 'Удалить все')
    keyboard.row('Меню')
    bot.send_message(message.from_user.id, "Выбери действие:", reply_markup=keyboard)


def change_note(message):
    change_state(message.from_user.id, "change_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, '', reply_markup=keyboard)


def delete_note_id(message):
    change_state(message.from_user.id, "delete_note_id")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    show_notes(message)
    bot.send_message(message.from_user.id, "Введи ID заметки, которую хочешь удалить:", reply_markup=keyboard)
    # bot.register_next_step_handler(message, )


def delete_all_notes(message):
    change_state(message.from_user.id, "delete_all_notes")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    database_cursor.execute(f"SELECT * FROM notes WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()[0]
    if data is None:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard)
    else:
        database_cursor.execute(f"DELETE FROM notes WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, "Все твои заметки удалены!", reply_markup=keyboard)


def show_notes(message):
    change_state(message.from_user.id, "show_notes")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Изменить')
    keyboard.row('Удалить по ID', 'Удалить все')
    keyboard.row('Назад', 'Меню')
    database_cursor.execute(f"SELECT * FROM notes WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()[0]
    if data:
        database_cursor.execute(f"SELECT id, datetime, note FROM notes WHERE user_id={message.from_user.id}")
        for data in database_cursor.fetchall():
            note_id = f"ID заметки: {data[0]}"
            note_datetime = f"\nДата и время заметки: {data[1]}"
            note_text = f"\nТекст заметки: {data[2]}"
            bot.send_message(message.from_user.id, note_id + note_datetime + note_text,
                             reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.from_user.id, "Это всё, что мне удалось найти.", reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard)


def add_note(message):
    change_state(message.from_user.id, "add_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Напиши заметку:", reply_markup=keyboard)
    bot.register_next_step_handler(message, write_note)


def write_note(message):
    change_state(message.from_user.id, "write_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    database_cursor.execute(f"INSERT INTO notes (user_id, datetime, note)"
                            f" VALUES ({message.from_user.id}, {current_datetime, message}, {message.text})")
    database.commit()
    bot.send_message(message.from_user.id, "Заметка сохранена!", reply_markup=keyboard)


actions = {
    ("start", "Меню"): start,
    ("start", "Состояния"): work_with_health,
    ("start", "Заметки"): work_with_notes,
    ("show_health", "Назад"): work_with_health,
    ("set_health", "Назад"): work_with_health,
    ("delete_health", "Назад"): work_with_health,
    ("change_health", "Назад"): work_with_health,
    ("work_with_health", "Изменить"): change_health,
    ("work_with_health", "Удалить"): delete_health,
    ("work_with_health", "Показать"): show_health,
    ("work_with_notes", "Добавить"): add_note,
    ("work_with_notes", "Показать"): show_notes,
    ("work_with_notes", "Удалить по ID"): delete_note_id,
    ("work_with_notes", "Удалить все"): delete_all_notes,
    ("work_with_notes", "Изменить"): change_note
}


@bot.message_handler(content_types=['text'])
def action(message):
    if message.text == 'Меню':
        start(message)
    else:
        database_cursor.execute(f"SELECT state FROM people WHERE user_id={message.from_user.id}")
        state = ''.join(database_cursor.fetchone())
        actions[(state, message.text)](message)


bot.infinity_polling()

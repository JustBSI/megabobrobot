token = open('token.txt').read()
import telebot
import sqlite3
from datetime import datetime
from telebot import types

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


def menu(message):
    change_state(message.from_user.id, "menu")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)  # open keyboard
    keyboard.row('Состояния', 'Заметки')
    bot.send_message(message.from_user.id, "Выбери нужный раздел:", reply_markup=keyboard)


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
    keyboard.row('Изменить')
    keyboard.row('Назад', 'Меню')
    if message.text != 'Назад':
        database_cursor.execute(f"UPDATE people SET health='{message.text}' WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, f"*Отлично! Теперь твоё состояние:* {message.text}",
                         reply_markup=keyboard, parse_mode="Markdown")
        bot.register_next_step_handler(message, action)
    else:
        work_with_health(message)


def delete_health(message):
    change_state(message.from_user.id, "delete_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Изменить')
    keyboard.row('Назад', 'Меню')
    if check_health(message):
        database_cursor.execute(f"UPDATE people SET health=NULL WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, "Информация о твоём состоянии удалена!", reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, "Я о тебе и так ничего не знаю!", reply_markup=keyboard)


def show_health(message):
    change_state(message.from_user.id, "show_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Изменить')
    keyboard.row('Назад', 'Меню')
    if check_health(message):
        bot.send_message(message.from_user.id, f"*Твоё состояние:* {''.join(check_health(message))}",
                         reply_markup=keyboard, parse_mode="Markdown")
    else:
        bot.send_message(message.from_user.id, "Ты ещё не указал информацию о здоровье!", reply_markup=keyboard)


def check_health(message):
    database_cursor.execute(f"SELECT health FROM people WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()[0]
    if data:
        return data
    else:
        return False


def work_with_notes(message):
    change_state(message.from_user.id, "work_with_notes")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Показать все', 'Добавить', 'Изменить')
    keyboard.row('Удалить по ID', 'Удалить все')
    keyboard.row('Меню')
    bot.send_message(message.from_user.id, "Выбери действие:", reply_markup=keyboard)


def change_note(message):
    change_state(message.from_user.id, "change_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if check_notes_user_id(message):
        print_all_notes(message)
        bot.send_message(message.from_user.id, "Введи ID заметки, которую хочешь изменить:", reply_markup=keyboard)
        bot.register_next_step_handler(message, change_note_text)
    else:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard)


def change_note_after_show(message):
    change_state(message.from_user.id, "change_note_after_show")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Введи ID заметки, которую хочешь изменить:", reply_markup=keyboard)
    bot.register_next_step_handler(message, change_note_text)


def change_note_text(message):
    change_state(message.from_user.id, "change_note_text")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if message.text.isdigit():
        note_id = message.text
        if check_note_id(message):
            bot.send_message(message.from_user.id, "Введи новый текст заметки:", reply_markup=keyboard)
            bot.register_next_step_handler(message, change_note_in_db, note_id)
        else:
            bot.send_message(message.from_user.id, "Введён неверный ID!", reply_markup=keyboard)
    else:
        action(message)


def change_note_in_db(message, note_id):
    change_state(message.from_user.id, "change_note_in_db")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if message.text != 'Назад':
        database_cursor.execute(f"UPDATE notes SET note='{message.text}', "
                                f"datetime='{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}' WHERE id={note_id}")
        database.commit()
        bot.send_message(message.from_user.id, "Заметка успешно изменена!", reply_markup=keyboard)
    else:
        action(message)


def delete_note_id(message):
    change_state(message.from_user.id, "delete_note_id")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if check_notes_user_id(message):
        print_all_notes(message)
        bot.send_message(message.from_user.id, "Введи ID заметки, которую хочешь удалить:", reply_markup=keyboard)
        bot.register_next_step_handler(message, delete_note_id_from_db)
    else:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard)


def delete_note_id_from_db(message):
    change_state(message.from_user.id, "delete_note_id_from_db")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if check_note_id(message):
        database_cursor.execute(f"DELETE FROM notes WHERE id={message.text}")
        database.commit()
        bot.send_message(message.from_user.id, "Заметка удалена!", reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, "Введён неверный ID!", reply_markup=keyboard)


def delete_all_notes(message):
    change_state(message.from_user.id, "delete_all_notes")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if check_notes_user_id(message):
        database_cursor.execute(f"DELETE FROM notes WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, "Все твои заметки удалены!", reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard)


def show_notes(message):
    change_state(message.from_user.id, "show_notes")
    keyboard_1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_1.row('Изменить заметку')
    keyboard_1.row('Удалить по ID', 'Удалить все')
    keyboard_1.row('Назад', 'Меню')
    keyboard_2 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_2.row('Добавить заметку')
    keyboard_2.row('Назад', 'Меню')
    if check_notes_user_id(message):
        print_all_notes(message)
        bot.send_message(message.from_user.id, "Это всё, что мне удалось найти.", reply_markup=keyboard_1)
    else:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard_2)


def check_notes_user_id(message):
    database_cursor.execute(f"SELECT * FROM notes WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()
    if data:
        return True
    else:
        return False


def check_note_id(message):
    database_cursor.execute(f"SELECT * FROM notes WHERE id={message.text}")
    data = database_cursor.fetchone()
    if data:
        return True
    else:
        return False


def print_all_notes(message):
    database_cursor.execute(f"SELECT id, datetime, note FROM notes WHERE user_id={message.from_user.id}")
    for data in database_cursor.fetchall():
        note_id = f"*ID заметки:* {data[0]}"
        note_datetime = f"\n*Дата и время заметки:* {data[1]}"
        note_text = f"\n*Текст заметки:* \n{data[2]}"
        bot.send_message(message.from_user.id, note_id + note_datetime + note_text, parse_mode="Markdown")


def add_note(message):
    change_state(message.from_user.id, "add_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Напиши заметку:", reply_markup=keyboard)
    bot.register_next_step_handler(message, write_note)


def write_note(message):
    change_state(message.from_user.id, "write_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Добавить заметку')
    keyboard.row('Назад', 'Меню')
    database_cursor.execute(f"INSERT INTO notes (user_id, datetime, note) "
                            f"VALUES ('{message.from_user.id}', '{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}', "
                            f"'{message.text}')")
    database.commit()
    bot.send_message(message.from_user.id, "Заметка сохранена!", reply_markup=keyboard)


actions = {
    ("start", "Меню"): start,
    ("start", "Состояния"): work_with_health,
    ("start", "Заметки"): work_with_notes,
    ("menu", "Меню"): start,
    ("menu", "Состояния"): work_with_health,
    ("menu", "Заметки"): work_with_notes,
    ("show_health", "Назад"): work_with_health,
    ("set_health", "Назад"): work_with_health,
    ("set_health", "Изменить"): change_health,
    ("show_health", "Изменить"): change_health,
    ("delete_health", "Назад"): work_with_health,
    ("change_health", "Назад"): work_with_health,
    ("work_with_health", "Изменить"): change_health,
    ("delete_health", "Изменить"): change_health,
    ("work_with_health", "Удалить"): delete_health,
    ("work_with_health", "Показать"): show_health,

    ("change_note", "Назад"): work_with_notes,
    ("change_note_text", "Назад"): work_with_notes,
    ("delete_note_id", "Назад"): work_with_notes,
    ("delete_note_id_from_db", "Назад"): work_with_notes,
    ("delete_all_notes", "Назад"): work_with_notes,
    ("show_notes", "Назад"): work_with_notes,
    ("show_notes", "Изменить заметку"): change_note_after_show,
    ("show_notes", "Добавить заметку"): add_note,
    ("show_notes", "Удалить все"): delete_all_notes,
    ("show_notes", "Удалить по ID"): delete_note_id,
    ("change_note_after_show", "Назад"): work_with_notes,
    ("change_note_in_db", "Назад"): change_note_after_show,
    ("add_note", "Назад"): work_with_notes,
    ("write_note", "Назад"): work_with_notes,
    ("write_note", "Добавить заметку"): add_note,
    ("work_with_notes", "Добавить"): add_note,
    ("work_with_notes", "Показать все"): show_notes,
    ("work_with_notes", "Удалить по ID"): delete_note_id,
    ("work_with_notes", "Удалить все"): delete_all_notes,
    ("work_with_notes", "Изменить"): change_note
}


@bot.message_handler(content_types=['text'])
def action(message):
    if message.text == 'Меню':
        menu(message)
    elif message.text == '/start':
        start(message)
    else:
        database_cursor.execute(f"SELECT state FROM people WHERE user_id={message.from_user.id}")
        state = ''.join(database_cursor.fetchone())
        actions[(state, message.text)](message)


bot.infinity_polling()

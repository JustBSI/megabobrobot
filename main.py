token = open('token.txt').read()
import telebot
import sqlite3
from datetime import datetime
current_datetime = datetime.now()
bot = telebot.TeleBot(token)
people = sqlite3.connect("people.db", check_same_thread=False)
people_cursor = people.cursor()

notes = sqlite3.connect("notes.db", check_same_thread=False)
notes_cursor = notes.cursor()


# new people table creation
with people:
    data = people.execute("SELECT count(*) FROM sqlite_master WHERE TYPE='table' and NAME='people'")
    for row in data:
        if row[0] == 0:
            people_cursor.execute("""CREATE TABLE people
                            (user_id INT PRIMARY KEY AUTOINCREMENT,
                            state NCHAR)
                            """)

# new notes table creation
with notes:
    data = notes.execute("SELECT count(*) FROM sqlite_master WHERE TYPE='table' and NAME='notes'")
    for row in data:
        if row[0] == 0:
            notes_cursor.execute("""CREATE TABLE notes
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INT,
                            datetime DATETIME,
                            note NCHAR)
                            """)


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)  # open keyboard
    keyboard.row('Показать состояние', 'Изменить состояние')
    keyboard.row('Удалить состояние', 'Добавить заметку')
    bot.send_message(message.from_user.id, "Привет, " + message.from_user.first_name + "! Выберите нужное действие:",
                     reply_markup=keyboard)


def add_note(message):
    bot.send_message(message.from_user.id, "Напишите заметку:")
    bot.register_next_step_handler(message, write_note)


def write_note(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    notes_cursor.execute("INSERT INTO notes (user_id, datetime, note) VALUES (?, ?, ?)",
                         (message.from_user.id, current_datetime, message.text))
    notes.commit()
    bot.send_message(message.from_user.id, "Заметка сохранена!", reply_markup=keyboard)


def change_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Болею', 'Не болею')
    bot.send_message(message.from_user.id, "Укажите состояние:", reply_markup=keyboard)
    bot.register_next_step_handler(message, set_state)


def delete_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    people_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
    if people_cursor.fetchone() is None:
        bot.send_message(message.from_user.id, "Я о Вас и так ничего не знаю!", reply_markup=keyboard)
    else:
        people_cursor.execute("DELETE FROM people WHERE user_id=(?)", [message.from_user.id])
        people.commit()
        bot.send_message(message.from_user.id, "Информация о Вашем состоянии удалена!", reply_markup=keyboard)


def show_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    people_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
    if people_cursor.fetchone() is None:
        bot.send_message(message.from_user.id, "Вы ещё не указали, больны Вы или нет!")
    else:
        people_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
        bot.send_message(message.from_user.id, "Ваше состояние: " + ''.join(people_cursor.fetchone()),
                         reply_markup=keyboard)


actions = {
    'Изменить состояние': change_state,
    'Удалить состояние': delete_state,
    'Показать состояние': show_state,
    'Добавить заметку': add_note,
    'Меню': start
}


@bot.message_handler(content_types=['text'])
def action(message):
    actions[message.text](message)


def set_state(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Меню')
    people_cursor.execute("SELECT state FROM people WHERE user_id=(?)", [message.from_user.id])
    if people_cursor.fetchone() is None:
        people_cursor.execute("INSERT INTO people (user_id, state) VALUES (?, ?)", (message.from_user.id, message.text))
        people.commit()
    else:
        people_cursor.execute("UPDATE people SET state =(?) WHERE user_id=(?)", (message.text, message.from_user.id))
        people.commit()
    bot.send_message(message.from_user.id, "Отлично! Теперь Ваше состояние: " + message.text, reply_markup=keyboard)
    bot.register_next_step_handler(message, start)


bot.infinity_polling()

import telebot
import sqlite3
from datetime import datetime
token = open('token.txt').read()

bot = telebot.TeleBot(token)
database = sqlite3.connect("database.db", check_same_thread=False)  # Подключение базы данных.
database_cursor = database.cursor()  # Объект курсора для управления БД.


def create_table(name, request):
    """
    Функция добавления таблицы в БД.

    :param name: Название таблицы
    :param request: SQL запрос с параметрами для новой таблицы
    """
    with database:
        data = database.execute(f"SELECT count(*) FROM sqlite_master WHERE TYPE='table' and NAME='{name}'")
        for row in data:
            if row[0] == 0:
                database_cursor.execute(f"""CREATE TABLE {name} ({request})""")


create_table("people",
             """user_id INTEGER PRIMARY KEY AUTOINCREMENT,
             health NCHAR,
             state NCHAR""")

create_table("notes",
             """id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INT,
             datetime DATETIME,
             note NCHAR""")


def change_state(user_id, state):
    """
    Функция изменения состояния пользователя в ходе работы бота.

    :param user_id: ID пользователя
    :param state: состояние пользователя
    """
    database_cursor.execute(f"SELECT * FROM people WHERE user_id={user_id}")  # Поиск информации о пользователе в БД.
    if database_cursor.fetchone() is None:
        database_cursor.execute(f"INSERT INTO people (user_id, state) VALUES ({user_id}, '{state}')")
    else:
        database_cursor.execute(f"UPDATE people SET state = '{state}' WHERE user_id={user_id}")
    database.commit()


@bot.message_handler(commands=['start'])
def start(message):
    """
    Функция начала работы с ботом.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "start")  # Изменение состояния пользователя в боте.
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)  # Открытие клавиатуры.
    keyboard.row('Состояния', 'Заметки')  # Названия кнопок в строке.
    bot.send_message(message.from_user.id, f"Привет, {message.from_user.first_name}! Выбери нужный раздел:",
                     reply_markup=keyboard)


def menu(message):
    """
    Функция отображения меню разделов.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "menu")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Состояния', 'Заметки')
    bot.send_message(message.from_user.id, "Выбери нужный раздел:", reply_markup=keyboard)


def work_with_health(message):
    """
    Функция отображения меню работы со здоровьем.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "work_with_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Показать', 'Изменить', 'Удалить')
    keyboard.row('Меню')
    bot.send_message(message.from_user.id, "Выбери действие:", reply_markup=keyboard)


def change_health(message):
    """
    Функция, принимающая информацию о здоровье от пользователя.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "change_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Болею', 'Не болею')
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Укажи состояние:", reply_markup=keyboard)
    bot.register_next_step_handler(message, set_health)


def set_health(message):
    """
    Функция записи изменения здоровья в БД.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "set_health")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Изменить', 'Удалить')
    keyboard.row('Назад', 'Меню')
    if message.text in ('Болею', 'Не болею'):
        database_cursor.execute(f"UPDATE people SET health='{message.text}' WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, f"*Отлично! Теперь твоё состояние:* {message.text}",
                         reply_markup=keyboard, parse_mode="Markdown")
    else:
        action(message)


def delete_health(message):
    """
    Функция удаления информации о здоровье из БД.

    :param message: Сообщение от пользователя
    """
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
    """
    Функция отображения здоровья.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "show_health")
    keyboard_1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_1.row('Изменить', 'Удалить')
    keyboard_1.row('Назад', 'Меню')
    keyboard_2 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_2.row('Изменить')
    keyboard_2.row('Назад', 'Меню')
    if check_health(message):
        bot.send_message(message.from_user.id, f"*Твоё состояние:* {check_health(message)}",
                         reply_markup=keyboard_1, parse_mode="Markdown")
    else:
        bot.send_message(message.from_user.id, "Ты ещё не указал информацию о здоровье!", reply_markup=keyboard_2)


def check_health(message):
    """
    Функция проверки наличия информации о здоровье в БД.

    :param message: Сообщение от пользователя;
    :return информация о здоровье или None
    """
    database_cursor.execute(f"SELECT health FROM people WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()[0]
    return data


def work_with_notes(message):
    """
    Функция отображения меню работы с заметками.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "work_with_notes")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Показать все', 'Добавить', 'Изменить')
    keyboard.row('Удалить по ID', 'Удалить все')
    keyboard.row('Меню')
    bot.send_message(message.from_user.id, "Выбери действие:", reply_markup=keyboard)


def change_note(message):
    """
    Функция, принимающая ID изменяемой заметки.

    :param message: Сообщение от пользователя
    """
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
    """
    Функция, принимающая ID изменяемой заметки после отображения всех заметок.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "change_note_after_show")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Введи ID заметки, которую хочешь изменить:", reply_markup=keyboard)
    bot.register_next_step_handler(message, change_note_text)


def change_note_text(message):
    """
    Функция, принимающая новый текст изменяемой заметки.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "change_note_text")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if message.text.isdigit():  # Проверка, что пользователь ввёл ID заметки, а не текст.
        if check_note_id(message):
            note_id = message.text  # Сохранение введённого ID для передачи в следующую функцию.
            bot.send_message(message.from_user.id, "Введи новый текст заметки:", reply_markup=keyboard)
            bot.register_next_step_handler(message, change_note_in_db, note_id)
        else:
            bot.send_message(message.from_user.id, "Введён несуществующий ID! Попробуй снова:", reply_markup=keyboard)
            bot.register_next_step_handler(message, change_note_text)
    elif message.text not in ('Назад', 'Меню'):
        bot.send_message(message.from_user.id, "Введи ID, а не текст!")
        bot.register_next_step_handler(message, change_note_text)
    else:
        action(message)


def change_note_in_db(message, note_id):
    """
    Функция изменения текста заметки в БД.

    :param message: Сообщение от пользователя
    :param note_id: ID выбранной заметки
    """
    change_state(message.from_user.id, "change_note_in_db")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Добавить заметку')
    keyboard.row('Назад', 'Меню')
    if message.text not in ('Назад', 'Меню'):
        database_cursor.execute(f"UPDATE notes SET note='{message.text}', "
                                f"datetime='{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}' WHERE id={note_id}")
        database.commit()
        bot.send_message(message.from_user.id, "Заметка успешно изменена!", reply_markup=keyboard)
    else:
        action(message)


def delete_note_id(message):
    """
    Функция, принимающая ID заметки для удаления.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "delete_note_id")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    if check_notes_user_id(message):
        print_all_notes(message)
        bot.send_message(message.from_user.id, "Введи ID заметки, которую хочешь удалить:", reply_markup=keyboard)
        bot.register_next_step_handler(message, delete_note_id_from_db)
    else:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard)


def delete_note_id_after_show(message):
    """
    Функция, принимающая ID удаляемой заметки после отображения всех заметок.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "delete_note_id_after_show")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Введи ID заметки, которую хочешь удалить:", reply_markup=keyboard)
    bot.register_next_step_handler(message, delete_note_id_from_db)


def delete_note_id_from_db(message):
    """
    Функция удаления заметки из БД.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "delete_note_id_from_db")
    keyboard_1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_1.row('Добавить заметку')
    keyboard_1.row('Назад', 'Меню')
    keyboard_2 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_2.row('Назад', 'Меню')
    if message.text.isdigit():
        if check_note_id(message):
            database_cursor.execute(f"DELETE FROM notes WHERE id={message.text}")
            database.commit()
            bot.send_message(message.from_user.id, "Заметка удалена!", reply_markup=keyboard_1)
        else:
            bot.send_message(message.from_user.id, "Введён несуществующий ID! Попробуй снова:", reply_markup=keyboard_2)
            bot.register_next_step_handler(message, delete_note_id_from_db)
    elif message.text not in ('Назад', 'Меню', 'Добавить заметку'):
        bot.send_message(message.from_user.id, "Введи ID, а не текст!")
        bot.register_next_step_handler(message, delete_note_id_from_db)
    else:
        action(message)


def delete_all_notes(message):
    """
    Функция удаления всех заметок из БД.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "delete_all_notes")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Добавить заметку')
    keyboard.row('Назад', 'Меню')
    if check_notes_user_id(message):
        database_cursor.execute(f"DELETE FROM notes WHERE user_id={message.from_user.id}")
        database.commit()
        bot.send_message(message.from_user.id, "Все твои заметки удалены!", reply_markup=keyboard)
    else:
        bot.send_message(message.from_user.id, "Ты ещё не добавил ни одной заметки!", reply_markup=keyboard)


def show_notes(message):
    """
    Функция отображения всех заметок.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "show_notes")
    keyboard_1 = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_1.row('Изменить заметку', 'Добавить заметку')
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
    """
    Функция проверки наличия заметок у пользователя в БД.

    :param message: Сообщение от пользователя;
    :return найденные заметки или None
    """
    database_cursor.execute(f"SELECT * FROM notes WHERE user_id={message.from_user.id}")
    data = database_cursor.fetchone()
    return data


def check_note_id(message):
    """
    Функция проверки наличия заметки с указанным ID в БД.

    :param message: Сообщение от пользователя;
    :return найденные заметки или None
    """
    database_cursor.execute(f"SELECT * FROM notes WHERE id={message.text}")
    data = database_cursor.fetchone()
    return data


def print_all_notes(message):
    """
    Функция печати всех заметок пользователя.

    :param message: Сообщение от пользователя
    """
    database_cursor.execute(f"SELECT id, datetime, note FROM notes WHERE user_id={message.from_user.id}")
    for data in database_cursor.fetchall():
        note_id = f"*ID заметки:* {data[0]}"
        note_datetime = f"\n*Дата и время заметки:* {data[1]}"
        note_text = f"\n*Текст заметки:* \n{data[2]}"
        bot.send_message(message.from_user.id, note_id + note_datetime + note_text, parse_mode="Markdown")


def add_note(message):
    """
    Функция принятия текста заметки для добавления.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "add_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Назад', 'Меню')
    bot.send_message(message.from_user.id, "Напиши заметку:", reply_markup=keyboard)
    bot.register_next_step_handler(message, write_note)


def write_note(message):
    """
    Функция сохранения заметки в БД.

    :param message: Сообщение от пользователя
    """
    change_state(message.from_user.id, "write_note")
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('Добавить заметку')
    keyboard.row('Назад', 'Меню')
    if message.text not in ('Назад', 'Меню'):
        database_cursor.execute(f"INSERT INTO notes (user_id, datetime, note) "
                                f"VALUES ('{message.from_user.id}', '{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}', "
                                f"'{message.text}')")
        database.commit()
        bot.send_message(message.from_user.id, "Заметка сохранена!", reply_markup=keyboard)
    else:
        action(message)


# Словарь, хранящий все варианты состояний пользователя и действий на кнопки в конкретных состояниях.
actions = {
    ("start", "Меню"): start,
    ("start", "Состояния"): work_with_health,
    ("start", "Заметки"): work_with_notes,

    ("menu", "Меню"): start,
    ("menu", "Состояния"): work_with_health,
    ("menu", "Заметки"): work_with_notes,

    ("work_with_health", "Изменить"): change_health,
    ("work_with_health", "Удалить"): delete_health,
    ("work_with_health", "Показать"): show_health,

    ("change_health", "Назад"): work_with_health,

    ("show_health", "Назад"): work_with_health,
    ("show_health", "Изменить"): change_health,
    ("show_health", "Удалить"): delete_health,

    ("set_health", "Назад"): work_with_health,
    ("set_health", "Изменить"): change_health,
    ("set_health", "Удалить"): delete_health,
    ("set_health", "Болею"): set_health,
    ("set_health", "Не болею"): set_health,

    ("delete_health", "Назад"): work_with_health,
    ("delete_health", "Изменить"): change_health,


    ("work_with_notes", "Добавить"): add_note,
    ("work_with_notes", "Показать все"): show_notes,
    ("work_with_notes", "Удалить по ID"): delete_note_id,
    ("work_with_notes", "Удалить все"): delete_all_notes,
    ("work_with_notes", "Изменить"): change_note,

    ("show_notes", "Назад"): work_with_notes,
    ("show_notes", "Изменить заметку"): change_note_after_show,
    ("show_notes", "Добавить заметку"): add_note,
    ("show_notes", "Удалить все"): delete_all_notes,
    ("show_notes", "Удалить по ID"): delete_note_id_after_show,

    ("change_note", "Назад"): work_with_notes,
    ("change_note", "Добавить заметку"): add_note,

    ("change_note_text", "Назад"): work_with_notes,
    ("change_note_text", "Назад"): work_with_notes,

    ("delete_note_id", "Назад"): work_with_notes,
    ("delete_note_id", "Добавить заметку"): add_note,

    ("change_note_after_show", "Добавить заметку"): add_note,
    ("change_note_after_show", "Назад"): show_notes,

    ("delete_note_id_after_show", "Добавить заметку"): add_note,
    ("delete_note_id_after_show", "Назад"): show_notes,

    ("delete_note_id_from_db", "Назад"): work_with_notes,
    ("delete_note_id_from_db", "Добавить заметку"): add_note,

    ("delete_all_notes", "Назад"): work_with_notes,
    ("delete_all_notes", "Добавить заметку"): add_note,

    ("change_note_in_db", "Назад"): work_with_notes,
    ("change_note_in_db", "Добавить заметку"): add_note,

    ("add_note", "Назад"): work_with_notes,

    ("write_note", "Назад"): work_with_notes,
    ("write_note", "Добавить заметку"): add_note,
}


@bot.message_handler(content_types=['text'])
def action(message):
    """
    Функция определения действий для бота в зависимости от нажатой пользователем кнопки.

    :param message: Сообщение от пользователя
    """
    if message.text == 'Меню':
        menu(message)
    elif message.text == '/start':
        start(message)
    else:
        database_cursor.execute(f"SELECT state FROM people WHERE user_id={message.from_user.id}")
        state = database_cursor.fetchone()[0]
        if (state, message.text) in actions:
            actions[(state, message.text)](message)
        else:
            bot.send_message(message.from_user.id, "Выбери нужный пункт!")
            eval(state)


bot.infinity_polling()

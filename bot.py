import random
from telebot import TeleBot, types
from db import get_connection

TOKEN = "8625756415:AAEHRy2LR75PvNzPOuJI1X_edROrFhNjWJk"  # вставь сюда

bot = TeleBot(TOKEN)

buttons = []


def get_or_create_user(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()

    if user:
        return user[0]

    cur.execute(
        "INSERT INTO users (telegram_id) VALUES (%s) RETURNING id",
        (telegram_id,)
    )
    user_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()

    return user_id


def get_words(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT w.id, w.en_word, w.ru_word
        FROM words w
        WHERE w.id NOT IN (
            SELECT word_id FROM deleted_words WHERE user_id = %s
        )
    """, (user_id,))

    base_words = cur.fetchall()

    cur.execute("""
        SELECT NULL, en_word, ru_word
        FROM user_words
        WHERE user_id = %s
    """, (user_id,))

    user_words = cur.fetchall()

    cur.close()
    conn.close()

    return base_words + user_words


def get_question(user_id):
    words = get_words(user_id)

    correct = random.choice(words)
    others = random.sample(words, min(3, len(words)))

    options = list(set([correct] + others))
    random.shuffle(options)

    return correct, options


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Давай учить английский 🇬🇧")
    send_question(message)


def send_question(message):
    user_id = get_or_create_user(message.from_user.id)

    correct, options = get_question(user_id)

    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []

    for _, en, _ in options:
        btn = types.KeyboardButton(en)
        buttons.append(btn)

    buttons.append(types.KeyboardButton("Дальше ⏭"))
    buttons.append(types.KeyboardButton("Добавить слово ➕"))
    buttons.append(types.KeyboardButton("Удалить слово 🔙"))

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        f"Выбери перевод:\n🇷🇺 {correct[2]}",
        reply_markup=markup
    )

    bot.register_next_step_handler(message, check_answer, correct)


def check_answer(message, correct):
    if message.text == "Дальше ⏭":
        send_question(message)
        return

    if message.text == "Добавить слово ➕":
        bot.send_message(message.chat.id, "Введите слово на английском:")
        bot.register_next_step_handler(message, add_word_en)
        return

    if message.text == "Удалить слово 🔙":
        delete_word(message, correct)
        return

    if message.text == correct[1]:
        bot.send_message(message.chat.id, f"Отлично ❤️\n{correct[1]} -> {correct[2]}")
    else:
        bot.send_message(message.chat.id, "Ошибка ❌ Попробуй ещё")

    send_question(message)


def add_word_en(message):
    bot.send_message(message.chat.id, "Введите перевод:")
    bot.register_next_step_handler(message, add_word_ru, message.text)


def add_word_ru(message, en_word):
    user_id = get_or_create_user(message.from_user.id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO user_words (user_id, en_word, ru_word) VALUES (%s, %s, %s)",
        (user_id, en_word, message.text)
    )

    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, "Слово добавлено ✅")
    send_question(message)


def delete_word(message, correct):
    user_id = get_or_create_user(message.from_user.id)

    if correct[0] is None:
        bot.send_message(message.chat.id, "Нельзя удалить пользовательское слово")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO deleted_words (user_id, word_id) VALUES (%s, %s)",
        (user_id, correct[0])
    )

    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, "Слово удалено ❌")
    send_question(message)


bot.infinity_polling()

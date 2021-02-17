import logging
from typing import Dict
import re
import json
import requests

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    PollAnswerHandler
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY = range(
    2)  # =============================ДВА "СОСТОЯНИЯ" БУДУТ ВОСПРИНИМАТЬСЯ ПРОГРАММОЙ КАК INT 0,1=======================#

reply_keyboard = [
    ['Название', 'Место'],
    ['Время', 'Описание'],
    ['Отправить'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

texttemp = "Default value"


# =============================ДЛЯ КРАСИВОГО ВЫВОДА СЛОВАРЯ=======================#
def facts_to_str(user_data: Dict[str, str]) -> str:
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    # =============================ПРИВЕТСТВИЕ=======================#
    update.message.reply_text(
        "CallBoardHSE приветствует Вас! \n Создайте событие уже сейчас!",
        reply_markup=markup,
    )

    return CHOOSING


def regular_choice(update: Update, context: CallbackContext):
    print("regular_choice")

    text = update.message.text

    global texttemp

    texttemp = text
    print(texttemp)  # =============================МЕСТО,ВРЕМЯ, ОПИСАНИЕ ИЛИ НАЗВАНИЕ=======================#

    context.user_data['choice'] = text

    # =============================ГОВОРИМ ПОЛЬЗОВАТЕЛЮ, ЧТОБЫ ОПИСАЛ СОБЫТИЕ=======================#
    update.message.reply_text(f'Хотите добавить событию {text.lower()}? Замечательно! Напишите в сообщение')

    # =============================КРАЙНЕ КРИНЖОВОЕ РЕШЕНИЕ ДЛЯ ТОГО, ЧТОБЫ ПОЛЬЗОВАТЕЛЬ ЗАПОЛНИЛ СОБЫТИЕ (НЕ БЕЙТЕ ПЖ)=======================#
    if text == "Место":
        update.message.reply_text(
            f'Пожалуйста, выберите одно из зданий: \n Солянка, Ляля, Колобок, БХ \n Введите ответ с прописной буквы без пробелов ;)')
    if text == "Время":
        update.message.reply_text(
            f'Пожалуйста, введите дату в формате ДД/ММ/ГГГГ. \n Пример: 17/02/2021  или 05/11/2022')

    return TYPING_REPLY


def received_information(update: Update, context: CallbackContext) -> int:
    print("received_information")

    user_data = context.user_data
    text = update.message.text
    print(texttemp)

    # =============================ПРОВЕРКА НА ПРАВИЛЬНОСТЬ ВВОДА МЕСТА=======================#
    if texttemp == "Место" and text != 'Ляля' and text != 'БХ' and text != 'Солянка' and text != 'Колобок':
        update.message.reply_text(
            "Пожалуйста, введите свой ответ в правильное форме и повторите попытку",
            reply_markup=markup)
        return

    # =============================ПРОВЕРКА НА ПРАВИЛЬНОСТЬ ВВОДА ДАТЫ=======================#
    pattern = r'^(0?[1-9]|[12][0-9]|3[01])/(0?[1-9]|1[0-2])/(20[2-3][1-9])$'

    if texttemp == "Время" and not (re.match(pattern, text)):
        update.message.reply_text(
            "Пожалуйста, введите свой ответ в правильное форме и повторите попытку",
            reply_markup=markup)
        return

    print(text)
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(
        "Класс! Вот что мы уже заполнили:"
        f"{facts_to_str(user_data)} Скажите, что нужно еще добавить"
        " или поменять.",
        reply_markup=markup,
    )

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    if len(user_data) != 4:
        update.message.reply_text(
            "Заполните все поля и попробуйте еще раз",
            reply_markup=markup)

        return

    contacts = str(update.effective_user.mention_html())
    contacts = contacts[contacts.find('>') + 1:]
    contacts = contacts[:contacts.find('<')]
    user_data['Контакты'] = contacts

    update.message.reply_text(
        f"Вот что вся информация о Вашем событии: {facts_to_str(user_data)} Отправляем!"
    )

    # =============================ИЗМЕНЕНИЕ КЛЮЧЕЙ СЛОВАРЯ ДЛЯ ХОРОШЕГО JSON=======================#
    user_data['title'] = user_data['Название']
    user_data['place'] = user_data['Место']
    user_data['dates'] = user_data['Время']
    user_data['contacts'] = user_data['Контакты']
    user_data['content'] = user_data['Описание']

    del user_data['Контакты']
    del user_data['Название']
    del user_data['Место']
    del user_data['Описание']
    del user_data['Время']

    # =============================ГЕНЕРАЦИЯ JSON=======================#
    temp = json.dumps(user_data)

    loaded_r = json.loads(temp)
    print(loaded_r)

    # =============================ПОПЫТКА ОТПРАВКИ JSON=======================#
    try:
        r = requests.post('http://u1293020.isp.regruhosting.ru/input', json=loaded_r)
        update.message.reply_text(
            "Получилось! \n Создавайте события с помощью /start"
        )
    except:
        update.message.reply_text(
            "Упс...Проблема с соединением. \n Попробуйте еще раз с помощью /start"
        )

    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    updater = Updater("1624913668:AAEV7zf6abIdSZsO8TVTm2pZ3EBuiVI1CAw")

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(
                    Filters.regex('^(Название|Место|Время|Описание)$'), regular_choice
                )
            ],

            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Отправить$')),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Отправить$'), done)],
    )

    dispatcher.add_handler(conv_handler)

    # =============================ЗАСТАВЛЯЕМ БОТА РАБОТАТЬ=======================#

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

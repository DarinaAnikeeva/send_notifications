import os
import time
import argparse
import textwrap as tw
import requests
import logging

from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Updater

logger = logging.getLogger('dever')


def send_lesson_info(new_attempts, chat_id):
    lesson_name = new_attempts['lesson_title']
    is_lesson_negative = new_attempts['is_negative']
    if is_lesson_negative:
        bot.send_message(chat_id=chat_id,
                         text=tw.dedent(f'''
                            Преподаватель проверил урок: "{lesson_name}"
                                           
                            К сожалению, в работе нашлись ошибки''')
                         )
    else:
        bot.send_message(chat_id=chat_id,
                         text=tw.dedent(f'''
                            У вас проверили урок "{lesson_name}"
                                    
                            Преподавателю всё понравилось, можете приступать к другому уроку!''')
                         )


def check_lessons(devman_token, chat_id):
    timestamp = int(time.time())
    while True:
        try:
            url = 'https://dvmn.org/api/long_polling/'
            headers = {
                'Authorization': devman_token
            }

            payload = {
                'timestamp': timestamp
            }

            response = requests.get(url,
                                    params=payload,
                                    headers=headers,
                                    timeout=10)
            response.raise_for_status()
            response_params = response.json()

            if response_params['status'] == "timeout":
                timestamp = response_params['timestamp_to_request']
            elif response_params['status'] == 'found':
                send_lesson_info(response_params['new_attempts'][0], chat_id)
                timestamp = response_params['last_attempt_timestamp']

        except requests.exceptions.ReadTimeout:
            pass
        except requests.exceptions.ConnectionError:
            logger.error('Отсутствует подключение к интернету')
            time.sleep(10)
            pass


class TelegramLogsHandler(logging.Handler):

    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'chat_id',
        type=int,
        help='chat_id вашего телеграма')
    args = parser.parse_args()

    load_dotenv()
    devman_token = os.getenv('DEVMAN_TOKEN')
    tg_token = os.getenv('TG_TOKEN')

    bot = Bot(token=tg_token)
    updater = Updater(token=tg_token, use_context=True)

    try:
        logging.basicConfig(format="%(process)d %(levelname)s %(message)s")
        logger.setLevel(logging.INFO)
        logger.addHandler(TelegramLogsHandler(
            tg_bot=bot,
            chat_id=args.chat_id
        ))
        logger.info('Бот запущен')
        check_lessons(devman_token, chat_id=args.chat_id)
    except Exception as err:
        logger.info('Бот упал с ошибкой')
        logger.error(err, exc_info=True)

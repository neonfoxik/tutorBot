# Этот файл нужен для корректной работы пакета bot
import logging
import os

from django.conf import settings


class DummyBot:
    def message_handler(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def callback_query_handler(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop


def _build_bot():
    try:
        import telebot
        token = getattr(settings, 'BOT_TOKEN', None)
        if not token or os.getenv('ENABLE_TELEGRAM', '1') != '1':
            return DummyBot(), logging.getLogger('bot')
        bot_instance = telebot.TeleBot(
            token,
            threaded=False,
            skip_pending=True,
        )
        commands = getattr(settings, 'BOT_COMMANDS', [])
        if commands:
            try:
                bot_instance.set_my_commands(commands)
            except Exception as e:
                logging.warning(f'Failed to set bot commands: {e}')
        # Логирование TeleBot
        logger_obj = telebot.logger
        logger_obj.setLevel(logging.INFO)
        logging.basicConfig(level=logging.INFO, filename="ai_log.log", filemode="w")
        # Пробуем получить информацию о боте (может упасть без интернета) — не критично
        try:
            me = bot_instance.get_me()
            logging.info(f'@{getattr(me, "username", "unknown")} started')
        except Exception:
            logging.info('Bot started (get_me failed, continue)')
        return bot_instance, logger_obj
    except Exception:
        # Любые ошибки — подставляем заглушку
        return DummyBot(), logging.getLogger('bot')


bot, logger = _build_bot()

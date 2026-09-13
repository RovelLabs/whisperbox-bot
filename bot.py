"""Minimal anonymous Telegram bot for a single owner."""

import asyncio
import logging
import os
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from storage import MessageStore


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OWNER_ID = int(os.getenv("OWNER_ID", "5792274744"))
DATABASE_PATH = BASE_DIR / "bot.db"

router = Router()
store = MessageStore(DATABASE_PATH)


class AnonymousMessage(StatesGroup):
    waiting_for_content = State()


def write_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✉️ Написать", callback_data="write")]]
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Нажмите кнопку, чтобы написать сообщение.", reply_markup=write_button())


@router.callback_query(F.data == "write")
async def request_message(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AnonymousMessage.waiting_for_content)
    await callback.message.answer("Напишите своё сообщение 👇")
    await callback.answer()


@router.message(F.from_user.id == OWNER_ID, F.reply_to_message)
async def owner_reply(message: Message, bot: Bot) -> None:
    """Return an owner's reply to the user linked with the copied message."""
    recipient_id = store.get_recipient(message.reply_to_message.message_id)
    if recipient_id is None:
        return

    try:
        await bot.copy_message(
            chat_id=recipient_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception:
        logging.exception("Could not deliver an owner reply to %s", recipient_id)
        await message.reply("Не удалось доставить ответ: пользователь мог заблокировать бота.")


@router.message(StateFilter(AnonymousMessage.waiting_for_content), F.from_user.id != OWNER_ID)
async def receive_anonymous_message(message: Message, state: FSMContext, bot: Bot) -> None:
    """Copy the next user message to the owner and remember its anonymous route."""
    try:
        copied = await bot.copy_message(
            chat_id=OWNER_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception:
        logging.exception("Could not copy a user message to the owner")
        await message.answer("Не удалось отправить сообщение. Попробуйте ещё раз позже.")
        return

    store.save_recipient(copied.message_id, message.from_user.id)
    await state.clear()
    await message.answer("✅ Сообщение отправлено. Ожидайте ответа.")


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token or token == "PASTE_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN in .env before starting the bot.")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    store.initialize()
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command


# ------------- SETTINGS START -------------
TELEGRAM_BOT_TOKEN = "7803866275:AAEtVrdjQxOhBdgxSfTkE_fOD1llHsdBYWs"  # token for bot, obtained from @botfather # fmt: skip
HOW_MUCH_STARS = 100000
# ------------- SETTINGS END -------------


def payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Injest {HOW_MUCH_STARS} ⭐️", pay=True)

    return builder.as_markup()


async def send_invoice_handler(message: Message):
    prices = [LabeledPrice(label="XTR", amount=HOW_MUCH_STARS)]
    await message.answer_invoice(
        title="Injesting money into veins",
        description="Are you ready to enter Matrix? Yes.",
        prices=prices,
        provider_token="",
        payload="channel_support",
        currency="XTR",
        reply_markup=payment_keyboard(),
    )


async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


async def success_payment_handler(message: Message):
    await message.answer(text="🥳Matrix has you.🤗")


TOKEN = TELEGRAM_BOT_TOKEN
dp = Dispatcher()
dp.message.register(send_invoice_handler, Command(commands="donate"))
dp.pre_checkout_query.register(pre_checkout_handler)
dp.message.register(success_payment_handler, F.successful_payment)


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("-> Type /donate into bot in Telegram")
    asyncio.run(main())
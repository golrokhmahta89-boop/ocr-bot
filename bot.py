"""
ربات تلگرام تبدیل عکس به متن (OCR)
پشتیبانی از زبان فارسی و انگلیسی با Tesseract OCR
"""

import os
import io
import logging

from PIL import Image
import pytesseract

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

OCR_LANGUAGES = "fas+eng"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "سلام! 👋\n\n"
        "یه عکس حاوی متن برام بفرست تا متنش رو استخراج کنم.\n"
        "از فارسی و انگلیسی پشتیبانی می‌کنم."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "کافیه یه عکس (یا فایل تصویری) بفرستی، متن داخلش رو برات استخراج می‌کنم.\n\n"
        "برای بهترین نتیجه:\n"
        "• عکس واضح و با نور کافی باشه\n"
        "• متن کج یا خیلی کوچیک نباشه\n"
        "• کنتراست متن و پس‌زمینه خوب باشه"
    )


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    processing_msg = await message.reply_text("در حال پردازش عکس... ⏳")

    try:
        if message.photo:
            file = await message.photo[-1].get_file()
        elif message.document and message.document.mime_type.startswith("image/"):
            file = await message.document.get_file()
        else:
            await processing_msg.edit_text("لطفاً یک فایل تصویری معتبر بفرستید.")
            return

        file_bytes = await file.download_as_bytearray()
        image = Image.open(io.BytesIO(file_bytes))

        extracted_text = pytesseract.image_to_string(image, lang=OCR_LANGUAGES).strip()

        if not extracted_text:
            await processing_msg.edit_text(
                "متنی توی عکس پیدا نکردم. عکس واضح‌تری امتحان کن."
            )
            return

        max_len = 4000
        chunks = [
            extracted_text[i : i + max_len]
            for i in range(0, len(extracted_text), max_len)
        ]

        await processing_msg.edit_text("متن استخراج‌شده:")
        for chunk in chunks:
            await message.reply_text(chunk)

    except Exception as exc:
        logger.exception("خطا در پردازش عکس")
        await processing_msg.edit_text(f"خطایی پیش اومد: {exc}")


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "متغیر محیطی BOT_TOKEN تنظیم نشده."
        )

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))

    logger.info("ربات در حال اجراست...")
    app.run_polling()


if __name__ == "__main__":
    main()

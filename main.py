import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === Переменные окружения ===
TOKEN = os.getenv[BOT_TOKEN]           # токен бота от BotFather
APP_URL = os.getenv["https://fuel-bot-jsek.onrender.com"]           # публичный URL сервиса (напр. https://fuel-bot.onrender.com)

# === FastAPI-приложение и Telegram Application ===
app = FastAPI()
tg_app = Application.builder().token(TOKEN).build()

# === Хэндлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Привет! давай посчитаем рассход топлива.\n"
        "Отправь мне через пробел:\n"
        "расстояние(км) топливо(л) цена(₸/₽, опционально)\n"
        "Например: 500 40 220"
    )
    await update.message.reply_text(msg)

def calc_text(text: str) -> str:
    parts = text.replace(",", ".").split()
    if len(parts) < 2:
        return "Ошибка! Нужно минимум два числа: расстояние(км) и топливо(л).\nПример: 500 40 220"

    try:
        distance = float(parts[0])
        fuel = float(parts[1])
        price = float(parts[2]) if len(parts) > 2 else None
        if distance <= 0 or fuel <= 0:
            return "Дистанция и топливо должны быть > 0."
    except ValueError:
        return "Не понял числа. Пример: 500 40 220"

    consumption = (fuel / distance) * 100
    result = f"Расход: {consumption:.2f} л/100 км"
    if price and price > 0:
        cost = fuel * price
        result += f"\nСтоимость: {cost:.2f}"
    return result

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # игнорируем команды
    if text.startswith("/"):
        return
    await update.message.reply_text(calc_text(text))

# Регистрируем хэндлеры
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))

# === Webhook ===
@app.on_event("startup")
async def on_startup():
    # инициализируем приложение и ставим webhook
    await tg_app.initialize()
    webhook_url = f"{APP_URL}/webhook/{TOKEN}"
    await tg_app.bot.set_webhook(webhook_url)

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    if token != TOKEN:
        raise HTTPException(status_code=403, detail="forbidden")
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}

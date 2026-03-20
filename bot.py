import asyncio
import json
import time
from pathlib import Path
from os import environ

import requests
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

BOT_TOKEN = environ["BOT_TOKEN"]

GITHUB_USER = "DepMSK37"
GITHUB_REPO = "proxy-list"
GITHUB_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/verified"

CACHE_DIR       = Path("cache")
RATE_LIMIT_FILE = Path("rate_limit.json")

CACHE_TTL     = 4 * 3600
USER_COOLDOWN = 4 * 3600
MAX_MSG_LEN   = 4096

REGION_FILES = {
    "eu":  "proxy_eu_verified.txt",
    "ru":  "proxy_ru_verified.txt",
    "all": "proxy_all_verified.txt",
}

REGION_LABELS = {
    "eu":  "🌍 EU",
    "ru":  "🇷🇺 RU",
    "all": "🌐 Все регионы",
}

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()


def _load_limits() -> dict:
    if RATE_LIMIT_FILE.exists():
        try:
            return json.loads(RATE_LIMIT_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_limits(data: dict) -> None:
    RATE_LIMIT_FILE.write_text(json.dumps(data), encoding="utf-8")


def check_cooldown(user_id: int) -> int | None:
    limits = _load_limits()
    uid = str(user_id)
    if uid in limits:
        elapsed = time.time() - limits[uid]
        if elapsed < USER_COOLDOWN:
            return int(USER_COOLDOWN - elapsed)
    return None


def set_cooldown(user_id: int) -> None:
    limits = _load_limits()
    limits[str(user_id)] = time.time()
    _save_limits(limits)


def _cache_path(region: str) -> Path:
    return CACHE_DIR / REGION_FILES[region]


def _cache_age(region: str) -> float | None:
    path = _cache_path(region)
    if path.exists():
        return time.time() - path.stat().st_mtime
    return None


def _fetch_from_github(region: str) -> bool:
    url = f"{GITHUB_RAW}/{REGION_FILES[region]}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            _cache_path(region).write_text(r.text, encoding="utf-8")
            return True
    except Exception:
        pass
    return False


def get_proxy_lines(region: str) -> list[str]:
    age = _cache_age(region)
    if age is None or age > CACHE_TTL:
        _fetch_from_github(region)
    path = _cache_path(region)
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def split_by_length(lines: list[str], max_len: int = MAX_MSG_LEN) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        needed = len(line) + (1 if current else 0)
        if current and current_len + needed > max_len:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += needed
    if current:
        chunks.append("\n".join(current))
    return chunks


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌍 EU прокси",  callback_data="proxy_eu"),
            InlineKeyboardButton(text="🇷🇺 RU прокси", callback_data="proxy_ru"),
        ],
        [
            InlineKeyboardButton(text="🌐 Все прокси", callback_data="proxy_all"),
        ],
    ])


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>MTProto Proxy Bot</b>\n\n"
        "Получай свежие рабочие MTProto-прокси для Telegram.\n"
        "Каждая ссылка добавляет прокси в один клик прямо из чата.\n\n"
        "⏱ <i>Лимит: один запрос раз в 4 часа</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=main_keyboard(),
    )


@dp.callback_query(F.data.in_({"proxy_eu", "proxy_ru", "proxy_all"}))
async def handle_proxy_request(call: CallbackQuery) -> None:
    region  = call.data.removeprefix("proxy_")
    user_id = call.from_user.id
    label   = REGION_LABELS[region]

    remaining = check_cooldown(user_id)
    if remaining is not None:
        h = remaining // 3600
        m = (remaining % 3600) // 60
        await call.answer(
            f"⏳ Следующий запрос доступен через {h} ч {m} мин",
            show_alert=True,
        )
        return

    await call.answer()
    set_cooldown(user_id)

    proxies = await asyncio.get_event_loop().run_in_executor(
        None, get_proxy_lines, region
    )

    if not proxies:
        await call.message.answer(
            "😔 Список пока пуст — база ещё не загружена с GitHub.\n"
            "Попробуй через несколько минут.",
            reply_markup=main_keyboard(),
        )
        return

    await _send_proxies(call.message, proxies, label)


async def _send_proxies(
    message: Message,
    proxies: list[str],
    label: str,
) -> None:
    chunks = split_by_length(proxies)

    await message.answer(
        f"{label} прокси — <b>{len(proxies)} шт.</b>\n"
        f"Нажми на ссылку → прокси добавится в Telegram автоматически 👇",
        parse_mode=ParseMode.HTML,
    )

    for chunk in chunks:
        await message.answer(chunk)

    await message.answer(
        "✅ Готово! Если прокси не работает — попробуй следующий.",
        reply_markup=main_keyboard(),
    )


async def main() -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    print("🤖 Бот запущен (polling)")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
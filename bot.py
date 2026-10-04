"""
CODE MASTER — Python o‘rgatuvchi AI mentor (Telegram bot)

Texnologiyalar: Python 3.14, aiogram 3.31, python-dotenv, google-genai.

.env fayl (GitHub'ga yuborilmasin!):
    BOT_TOKEN=...
    GEMINI_API_KEY=...
    # ixtiyoriy: GEMINI_MODEL=gemini-3.5-flash

Ishga tushirish:
    pip install aiogram==3.31.0 python-dotenv google-genai
    python bot.py
"""

import asyncio
import html
import json
import logging
import os
import random
import re
from collections import deque
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatAction, ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, Filter
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    ErrorEvent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# SOZLAMALAR
# ============================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN .env faylida topilmadi.")

# Gemini modeli — faqat shu yerda o‘zgartiriladi.
# Model nomi API versiyangizga mos kelmasa, shu qiymatni almashtiring
# (masalan: "gemini-3.5-flash", "gemini-2.5-flash") yoki .env ga GEMINI_MODEL yozing.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Tezlik uchun "o‘ylash" darajasi. Model qo‘llamasa, bot o‘zi avtomatik o‘chiradi.
# O‘chirish uchun None qiling.
GEMINI_THINKING_LEVEL = "LOW"

GEMINI_TIMEOUT = 45          # soniya
GEMINI_MAX_OUTPUT = 3000     # javobdagi maksimal token
HISTORY_LIMIT = 14           # har bir foydalanuvchi uchun oxirgi xabarlar soni
HISTORY_ANSWER_CHARS = 2500  # xotirada saqlanadigan AI javobining maksimal uzunligi
MAX_USER_TEXT = 4000
TG_CHUNK = 3000              # Telegram limiti (4096) dan xavfsiz past chegara

DATA_FILE = Path(__file__).with_name("progress.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("codemaster")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
router = Router()
router.message.filter(F.chat.type == "private")

gemini_client = None
if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        logger.exception("Gemini klientini yaratib bo‘lmadi")
else:
    logger.warning("GEMINI_API_KEY topilmadi: AI Mentor ishlamaydi.")


# ============================================================
# AI UCHUN SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """Sening isming CODE MASTER AI.
Sen Python dasturlash bo‘yicha professional, sabrli va tushunarli mentor-san.

Asosiy vazifang foydalanuvchiga dasturlashni o‘rgatish.

Foydalanuvchi boshlang‘ich darajada bo‘lsa:
- oddiy so‘zlardan foydalan;
- kodni bosqichma-bosqich tushuntir;
- har bir muhim qator nima qilishini ayt;
- real misollar ber;
- xatolarni tushuntir;
- foydalanuvchini mustaqil kod yozishga unda.

Javoblar o‘zbek tilida bo‘lsin.

Agar foydalanuvchi kod yuborsa:
1. Kod nima qilayotganini tushuntir.
2. Xato bo‘lsa, xatoni ko‘rsat.
3. Nima sababdan xato bo‘lganini tushuntir.
4. To‘g‘rilangan kodni ber.
5. To‘g‘rilangan kodni ham tushuntir.

Agar foydalanuvchi 'tushunmadim' desa, mavzuni undan ham oddiyroq qilib qayta tushuntir.

Javoblar juda qisqa bo‘lib ketmasin, lekin keraksiz uzun ham bo‘lmasin.

Kod bloklaridan foydalan.

Sen foydalanuvchiga tayyor javob berish bilan birga uning dasturchi sifatida fikrlashini ham rivojlantirishing kerak.

Qo‘shimcha qoidalar:
- Juda murakkab terminlarni oddiy qilib tushuntir va kerak bo‘lsa kichik mashq ber.
- Javob Telegram uchun: jadval (| belgilari bilan) ishlatma, sarlavhalar o‘rniga qalin matn (**shunday**) ishlat.
- Kod bloklarini ```python bilan yoz.
- Savol dasturlashga umuman aloqasi bo‘lmasa, muloyimlik bilan Python mavzusiga qaytar."""

AI_ERROR = "❌ AI bilan bog‘lanishda muammo yuz berdi. Birozdan keyin qayta urinib ko‘ring."

AI_INTRO = """🤖 AI Mentor ishga tushdi!

Python, dasturlash yoki kodingiz haqida savol yozing.

Masalan:
• Python'da list nima?
• Shu kodimdagi xatoni top
• Menga if ni tushuntir
• Calculator dasturini qanday yozaman?

⬅️ Orqaga"""


# ============================================================
# FOYDALANUVCHI MA'LUMOTLARI
# ============================================================

users: dict[int, dict] = {}
ai_locks: dict[int, asyncio.Lock] = {}
save_lock = asyncio.Lock()

TOTAL_LESSONS = 30


def user(user_id: int) -> dict:
    """Yangi foydalanuvchi uchun hamma kerakli ma'lumotlar avtomatik yaratiladi."""
    u = users.get(user_id)
    if u is None:
        u = {
            "cur": 1,                 # hozirgi dars
            "done": {},               # {dars_raqami: eng yaxshi ball}
            "viewed": False,          # hozirgi dars ko‘rilganmi
            "test": None,             # ishlanayotgan test holati
            "menu": "main",           # main / python / lesson / ai
            "ai": False,              # AI rejimi yoqilganmi
            "history": deque(maxlen=HISTORY_LIMIT),
        }
        users[user_id] = u
    return u


def first_incomplete(u: dict) -> int:
    for n in range(1, TOTAL_LESSONS + 1):
        if n not in u["done"]:
            return n
    return TOTAL_LESSONS


def all_done(u: dict) -> bool:
    return len(u["done"]) >= TOTAL_LESSONS


def is_unlocked(u: dict, n: int) -> bool:
    return n == 1 or (n - 1) in u["done"]


def total_score(u: dict) -> int:
    return sum(u["done"].values())


def load_progress() -> None:
    if not DATA_FILE.exists():
        return
    try:
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        for uid, done in raw.items():
            u = user(int(uid))
            u["done"] = {int(k): int(v) for k, v in done.items()}
            u["cur"] = first_incomplete(u)
        logger.info("Progress yuklandi: %d foydalanuvchi", len(raw))
    except Exception:
        logger.exception("progress.json o‘qilmadi")


def _write_snapshot(snapshot: dict) -> None:
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, DATA_FILE)


async def save_progress() -> None:
    snapshot = {
        str(uid): {str(k): v for k, v in u["done"].items()}
        for uid, u in users.items()
        if u["done"]
    }
    async with save_lock:
        try:
            await asyncio.to_thread(_write_snapshot, snapshot)
        except Exception:
            logger.exception("Progressni saqlab bo‘lmadi")


# ============================================================
# KEYBOARD
# ============================================================

B_PY = "🐍 Python"
B_CPP = "⚙️ C++"
B_PROG = "📊 Progress"
B_HELP = "ℹ️ Yordam"
B_LESSONS = "📚 Darslar"
B_CONT = "▶️ Davom etish"
B_BACK = "⬅️ Orqaga"
B_AI = "🤖 AI Mentor"
B_TEST = "📝 Testni boshlash"
B_CLEAR = "🧹 Suhbatni tozalash"


def kb(rows):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=x) for x in row] for row in rows],
        resize_keyboard=True,
    )


MAIN = kb([
    [B_PY, B_CPP],
    [B_PROG, B_HELP],
])

PYTHON = kb([
    [B_LESSONS, B_CONT],
    [B_AI, B_PROG],
    [B_BACK],
])

LESSON_MENU = kb([
    [B_TEST],
    [B_CONT],
    [B_LESSONS, B_PROG],
    [B_AI, B_BACK],
])

AI_MENU = kb([
    [B_CLEAR],
    [B_BACK],
])


def current_kb(u: dict):
    return {
        "main": MAIN,
        "python": PYTHON,
        "lesson": LESSON_MENU,
        "ai": AI_MENU,
    }.get(u["menu"], MAIN)


# ============================================================
# 30 TA PYTHON DARSI
# ============================================================

DATA = [

(
"Python bilan tanishuv va print()",
"Python nima, dasturlash nima va Python bilan qanday ishlashni tushunamiz.",
'''print("Salom, Dunyo!")''',
"`print()` ekranga ma’lumot chiqaradi. Qavs ichidagi matn qo‘shtirnoq ichida bo‘ladi. Python buyruqlarni odatda yuqoridan pastga bajaradi.",
"`print(Salom)` kabi kodda matn qo‘shtirnoqsiz yozilgani uchun Python uni nom sifatida izlaydi va xato beradi.",
"Isming, maqsading va Python o‘rganayotganing haqida 3 ta print() yoz."
),

(
"O‘zgaruvchilar",
"Ma’lumotni nom bilan saqlash va keyin undan qayta foydalanishni o‘rganamiz.",
'''name = "Asil"
age = 20
print(name, age)''',
"`name` va `age` o‘zgaruvchi nomlari. `=` o‘ng tomondagi qiymatni chap tomondagi nomga biriktiradi. O‘zgaruvchi qiymati keyinchalik o‘zgartirilishi mumkin.",
'`2name = "Ali"` xato, chunki o‘zgaruvchi nomi raqam bilan boshlanmaydi.',
"Ism, yosh va sevimli til uchun 3 ta o‘zgaruvchi yarat."
),

(
"Ma’lumot turlari",
"Python qiymatlarning turini qanday ajratishini o‘rganamiz.",
'''name = "Ali"
age = 15
price = 12.5
active = True

print(type(name))
print(type(age))
print(type(price))
print(type(active))''',
"`str` — matn, `int` — butun son, `float` — o‘nlik son, `bool` — True/False. `type()` qiymat turini tekshiradi.",
'`"15"` va `15` bir xil emas: birinchisi matn, ikkinchisi butun son.',
"4 xil turdan bittadan qiymat yarat va `type()` bilan tekshir."
),

(
"Arifmetik operatorlar",
"Pythonni kalkulyator sifatida ishlatish va asosiy matematik operatorlarni o‘rganamiz.",
'''a = 10
b = 3

print(a + b)
print(a - b)
print(a * b)
print(a / b)
print(a // b)
print(a % b)
print(a ** b)''',
"`+` qo‘shadi, `-` ayiradi, `*` ko‘paytiradi, `/` bo‘ladi, `//` butun bo‘lish natijasini beradi, `%` qoldiqni beradi, `**` darajaga ko‘taradi.",
"`10 % 3 = 1`. `%` ni noto‘g‘ri tushunish juft/toq va bo‘linish tekshiruvlarida xato keltiradi.",
"Ikki son ol va barcha asosiy arifmetik amallarni chiqar."
),

(
"input() bilan ma’lumot olish",
"Foydalanuvchidan ma’lumot olib, uni dastur ichida ishlatishni o‘rganamiz.",
'''name = input("Ismingiz: ")
print("Salom,", name)

age = int(input("Yoshingiz: "))
print(age + 1)''',
"`input()` kiritilgan ma’lumotni odatda `str` qilib qaytaradi. `int()` uni butun songa aylantiradi.",
"`age = input(...)` dan keyin `age + 1` qilish xato bo‘lishi mumkin, chunki `age` hali `str`.",
"Ism va yoshni so‘rab, foydalanuvchi haqida bitta gap chiqar."
),

(
"Taqqoslash operatorlari",
"Qiymatlar orasidagi munosabatni tekshirishni o‘rganamiz.",
'''age = 18

print(age == 18)
print(age >= 18)
print(age != 20)''',
"`==` tenglikni tekshiradi, `!=` teng emas, `>` katta, `<` kichik, `>=` katta yoki teng, `<=` kichik yoki teng. Natija `True` yoki `False` bo‘ladi.",
"`=` qiymat beradi, `==` esa tenglikni tekshiradi. Ularni aralashtirmaslik kerak.",
"Ikki sonni olib, ularning teng, katta yoki kichik holatlarini tekshir."
),

(
"if sharti",
"Dasturga shart asosida qaror qabul qildirishni o‘rganamiz.",
'''age = 18

if age >= 18:
    print("Kirish mumkin")''',
"`if` shartni tekshiradi. Natija `True` bo‘lsa ichkaridagi kod bajariladi. `:` blok boshlanishini bildiradi, indentation esa blokning ichini ko‘rsatadi.",
"`if` dan keyin `:` ni unutish yoki ichki qatorni surmaslik `SyntaxError` yoki `IndentationError` keltirishi mumkin.",
"Yosh 18 yoki undan katta bo‘lsa ruxsat beradigan dastur yoz."
),

(
"else va elif",
"Bir nechta ehtimolni tartibli tekshirishni o‘rganamiz.",
'''score = 82

if score >= 90:
    print("A")
elif score >= 70:
    print("B")
else:
    print("C")''',
"`elif` — oldingi shart bajarilmasa keyingi shartni tekshiradi. `else` — hech biri bajarilmaganda ishlaydi. Python mos kelgan birinchi blokni bajaradi.",
"Shartlarni noto‘g‘ri tartiblash keyingi shartlarga yetib bormaslikka sabab bo‘ladi.",
"Ballga qarab A, B, C, D natija beradigan dastur yoz."
),

(
"and, or, not",
"Bir nechta shartni birlashtirish va mantiqiy qarorlar tuzishni o‘rganamiz.",
'''age = 20
has_id = True

if age >= 18 and has_id:
    print("Kirish mumkin")''',
"`and` — barcha shartlar rost bo‘lishini, `or` — kamida bittasi rost bo‘lishini, `not` — True/False qiymatining teskarisini bildiradi.",
"`and` va `or` ni chalkashtirish dastur qarorini o‘zgartiradi. Har bir shartni alohida tekshirib ko‘rish foydali.",
"Yosh va hujjat mavjudligiga qarab kirishga ruxsat ber."
),

(
"while sikli",
"Shart rost bo‘lib turganda kodni takrorlashni o‘rganamiz.",
'''count = 1

while count <= 5:
    print(count)
    count += 1''',
"`while` har aylanishda shartni tekshiradi. `count += 1` hisoblagichni o‘zgartirib, siklning bir payt tugashiga yordam beradi.",
"Hisoblagich o‘zgarmasa, shart doim True bo‘lib, cheksiz sikl yuzaga kelishi mumkin.",
"1 dan 10 gacha sonlarni `while` bilan chiqar."
),

(
"for va range()",
"Takrorlanadigan ishlarni ketma-ket bajarishning qulay usulini o‘rganamiz.",
'''for i in range(1, 6):
    print(i)''',
"`for` ketma-ketlikdagi har bir qiymat uchun kodni bajaradi. `range(1, 6)` 1, 2, 3, 4, 5 ni beradi; oxirgi chegara kirmaydi.",
"`range(5)` 1 dan emas, 0 dan boshlanishini eslab qolish kerak.",
"1 dan 20 gacha juft sonlarni `for` yordamida chiqar."
),

(
"break va continue",
"Sikl bajarilishini maxsus boshqarishni o‘rganamiz.",
'''for i in range(1, 10):
    if i == 5:
        break

    print(i)''',
"`break` butun siklni to‘xtatadi. `continue` esa joriy aylanishni tashlab, keyingi aylanishga o‘tadi.",
"`continue` va `break` bir xil emas: biri siklni tugatadi, ikkinchisi faqat bitta aylanishni tashlaydi.",
"1 dan 20 gacha yurib, 10 ga kelganda `break` ishlat."
),

(
"List",
"Bir nechta qiymatni bitta tartibli kolleksiyada saqlashni o‘rganamiz.",
'''fruits = ["olma", "banan", "uzum"]

print(fruits[0])

fruits.append("anor")

print(fruits)''',
"List `[]` bilan yoziladi va indeks 0 dan boshlanadi. `append()` oxiriga qo‘shadi. List ichidagi qiymatlar o‘zgarishi mumkin.",
"Birinchi element `[1]` emas, `[0]`. Mavjud bo‘lmagan indeksga murojaat `IndexError` berishi mumkin.",
"5 ta sevimli taomingni listga yozib, `for` bilan chiqar."
),

(
"List metodlari va slicing",
"Listni o‘zgartirish, qism olish va tartiblashni o‘rganamiz.",
'''numbers = [40, 10, 30, 20]

numbers.append(50)
numbers.sort()

print(numbers)
print(numbers[1:4])''',
"`append()` qo‘shadi, `remove()` o‘chiradi, `pop()` olib tashlaydi, `sort()` tartiblaydi, `reverse()` teskari qiladi. Slicing `[start:end]` bo‘lib, `end` kirmaydi.",
"`numbers[1:4]` 1, 2, 3 indekslarni oladi; 4-indeksning o‘zi kirmaydi.",
"Sonlar listini qo‘sh, o‘chir, tartibla va undan bir qismini ol."
),

(
"Tuple",
"O‘zgarmas ketma-ketlik bilan ishlashni o‘rganamiz.",
'''point = (10, 20)

print(point[0])''',
"Tuple odatda `()` bilan yoziladi. Elementlari o‘zgarmaydi. O‘zgarmas ma’lumotni saqlashda foydali.",
"`point[0] = 5` kabi kod `TypeError` beradi, chunki tuple o‘zgarmas.",
"Koordinata yoki ranglar uchun tuple yarat va elementlarini o‘qi."
),

(
"Dictionary",
"Ma’lumotni kalit va qiymat juftligi sifatida saqlashni o‘rganamiz.",
'''student = {
    "name": "Ali",
    "age": 15
}

print(student["name"])

student["age"] = 16''',
"Dictionary `{}` ichida `key: value` shaklida ishlaydi. Kalit orqali qiymat olinadi va o‘zgartiriladi.",
'Mavjud bo‘lmagan kalitga `student["city"]` kabi murojaat `KeyError` berishi mumkin.',
"O‘zing haqingda `name`, `age`, `city`, `language` kalitlari bilan dictionary tuz."
),

(
"Set",
"Takrorlanmaydigan qiymatlar to‘plami bilan ishlashni o‘rganamiz.",
'''numbers = {1, 2, 2, 3}

print(numbers)''',
"Set bir xil qiymatlarni takror saqlamaydi. Takroriy qiymatlarni olib tashlashda qulay.",
"Set indeksli list emas. `numbers[0]` kabi murojaat qilish mumkin emas.",
"Takrorlangan sonlar listini `set` ga aylantirib, noyob sonlarni chiqar."
),

(
"Funksiyalar",
"Qayta ishlatiladigan kod bloklarini yaratishni o‘rganamiz.",
'''def greet(name):
    print(f"Salom, {name}!")

greet("Asil")''',
"`def` funksiya yaratadi. `name` parametr. Funksiya chaqirilganda unga argument beriladi. Funksiya kodni tartibli va qayta ishlatiladigan qiladi.",
'Funksiyani faqat yaratib qo‘yish yetarli emas; uni `greet("Asil")` kabi chaqirish kerak.',
"Ikki sonni qabul qiladigan funksiya yarat."
),

(
"return",
"Funksiya natijasini tashqariga qaytarishni o‘rganamiz.",
'''def add(a, b):
    return a + b

result = add(5, 3)

print(result)''',
"`print()` natijani ko‘rsatadi, `return` esa qiymatni funksiya chaqirilgan joyga qaytaradi. Qaytgan qiymatni o‘zgaruvchiga saqlash mumkin.",
"`return` dan keyingi kod shu chaqiruvda bajarilmaydi. Natijani keyingi hisoblarda ishlatish kerak bo‘lsa `return` muhim.",
"To‘g‘ri to‘rtburchak yuzini qaytaradigan funksiya yoz."
),

(
"Scope: local va global",
"O‘zgaruvchining qayerda ko‘rinishi va ishlatilishini tushunamiz.",
'''x = 20

def show():
    y = 10
    print(x, y)

show()''',
"Funksiya ichidagi `y` local. Tashqaridagi `x` global bo‘lishi mumkin. Scope katta dasturlarda nomlarni boshqarishga yordam beradi.",
"Local o‘zgaruvchini funksiya tashqarisida ishlatishga urinish `NameError` berishi mumkin.",
"Local va global o‘zgaruvchili kichik tajriba yoz."
),

(
"String bilan ishlash",
"Matnni indekslash, o‘zgartirish va foydali metodlar bilan ishlashni o‘rganamiz.",
'''text = "Python"

print(text[0])
print(text.upper())
print(text.lower())''',
"String indekslanadi. `upper()` katta harfga, `lower()` kichik harfga o‘tkazadi. `replace()`, `strip()`, `split()` kabi metodlar ham ko‘p ishlatiladi.",
"String metodlari yangi natija qaytarishi mumkin; `text.upper()` chaqirilganda `text` o‘zgaruvchisi avtomatik o‘zgarmaydi.",
"Ismni olib, katta harfda, kichik harfda va uzunligi bilan chiqar."
),

(
"f-string",
"O‘zgaruvchilarni matn ichiga qulay joylashtirishni o‘rganamiz.",
'''name = "Asil"
age = 20

print(f"Mening ismim {name}, yoshim {age}.")''',
"f-string satr oldidan `f` bilan boshlanadi. `{}` ichidagi o‘zgaruvchi yoki ifoda natijasi matnga qo‘shiladi.",
"`f` ni unutish `{name}` ni oddiy matn sifatida chiqarishi mumkin.",
"Ism, yosh va shaharni bitta chiroyli gapda chiqar."
),

(
"Xatolar va try/except",
"Dasturdagi kutiladigan xatolarni ushlash va foydalanuvchiga tushunarli javob berishni o‘rganamiz.",
'''try:
    age = int(input("Yosh: "))
except ValueError:
    print("Iltimos, son kiriting.")''',
"`try` xato chiqishi mumkin bo‘lgan kodni, `except` esa xato yuz berganda bajariladigan kodni bildiradi. `ValueError` noto‘g‘ri qiymat turida yuzaga kelishi mumkin.",
"Barcha xatoni `Exception` bilan yutib yuborish sababni yashirishi mumkin. Kerakli exceptionni tutish yaxshiroq.",
"Noto‘g‘ri son kiritilganda xabar beradigan kalkulyator yoz."
),

(
"Fayllar",
"Ma’lumotni dastur yopilgandan keyin ham saqlash uchun fayllardan foydalanishni o‘rganamiz.",
'''with open("data.txt", "w", encoding="utf-8") as file:
    file.write("Salom, Python!")''',
"`w` yozish, `r` o‘qish, `a` oxiriga qo‘shish rejimi. `with` fayl ish tugagach uni boshqarishni xavfsizroq qiladi.",
"`w` mavjud fayl mazmunini almashtirishi mumkin. Muhim ma’lumot bilan ishlaganda rejimni to‘g‘ri tanlash kerak.",
"Ism va ballni faylga yozib, keyin o‘qib chiqar."
),

(
"Modullar va import",
"Tayyor kodlardan foydalanish va loyihani modullarga ajratishni o‘rganamiz.",
'''import random

number = random.randint(1, 10)

print(number)''',
"`import` modulni ulaydi. `random` tasodifiy sonlar bilan ishlaydi, `math` matematik imkoniyatlar beradi. O‘z modulingni ham yaratish mumkin.",
"Modul nomini noto‘g‘ri yozish `ModuleNotFoundError` keltirishi mumkin.",
"`random` yordamida 1 dan 100 gacha tasodifiy son chiqar."
),

(
"List comprehension",
"List yaratishning ixcham va ifodali usulini o‘rganamiz.",
'''squares = [x * x for x in range(1, 6)]

print(squares)''',
"Umumiy shakl: `[ifoda for element in ketma-ketlik if shart]`. Bu oddiy `for` siklining ixcham ko‘rinishi.",
"Juda murakkab comprehension kodni o‘qishni qiyinlashtiradi. Kodning o‘qilishi ham muhim.",
"1 dan 20 gacha juft sonlar kvadratlaridan list yarat."
),

(
"OOP: class va object",
"Obyektga yo‘naltirilgan dasturlashning asosiy g‘oyalarini tushunamiz.",
'''class Student:
    pass

student = Student()''',
"`class` — objectlar uchun andoza. `object` esa shu class asosida yaratilgan aniq nusxa. Katta dasturlarni mantiqiy obyektlarga ajratishda OOP foydali.",
"Class yaratish object yaratish degani emas. `student = Student()` orqali alohida object yaratiladi.",
"`Car` class va undan ikkita object yarat."
),

(
"OOP: __init__ va self",
"Object yaratilganda ma’lumot berish va self tushunchasini o‘rganamiz.",
'''class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

student = Student("Asil", 20)

print(student.name)''',
"`__init__` object yaratilganda ishga tushadi. `self` ayni objectni bildiradi. `self.name` objectning xususiyati, `name` esa parametr.",
"`self` ni noto‘g‘ri ishlatish yoki atributni noto‘g‘ri yozish object bilan ishlashda xatolarga olib keladi.",
"`Car` classiga `brand` va `year` atributlarini qo‘sh."
),

(
"OOP: metodlar va inheritance",
"Class ichidagi metodlar va meros olishni o‘rganamiz.",
'''class Animal:
    def speak(self):
        print("Ovoz")

class Dog(Animal):
    pass

dog = Dog()
dog.speak()''',
"Class ichidagi funksiya metod deyiladi. Inheritance orqali `Dog` `Animal` imkoniyatini oladi. Bu umumiy kodni qayta ishlatishga yordam beradi.",
"Meros olish munosabatini faqat mantiqan mos classlarda ishlatish kerak.",
"`Animal` va undan meros oluvchi `Cat` classini yarat."
),

(
"Yakuniy loyiha va dasturchi fikrlashi",
"O‘rgangan bilimlarni bitta amaliy loyiha va mustaqil fikrlashga birlashtiramiz.",
'''students = []

def add_student(name):
    students.append(name)

add_student("Ali")

print(students)''',
"Yaxshi dastur alohida mavzularni birlashtiradi: input, shartlar, sikllar, kolleksiyalar, funksiyalar, fayllar va OOP. Eng muhim ko‘nikma — muammoni kichik qismlarga ajratish.",
"Tayyor kodni ko‘r-ko‘rona ko‘chirish bilimni mustahkamlamaydi. Har bir qator nima uchun kerakligini tushunish kerak.",
"Mini Student Manager: talaba qo‘shish, ko‘rish, qidirish, saqlash va chiqish menyusini yarat."
),

]

assert len(DATA) == TOTAL_LESSONS


# ============================================================
# 60 TA TEST
# Har bir darsga 2 ta:
# 1 — OSON
# 2 — O‘RTA
# Format: (savol, variantlar, to‘g‘ri_javob_indeksi, tushuntirish, kod_misoli)
# Variantlar ko‘rsatilganda aralashtiriladi, shuning uchun
# to‘g‘ri javob doim birinchi turmaydi.
# ============================================================

TESTS = [

(
"Python nima?",
["Dasturlash tili", "Antivirus", "Brauzer", "Printer"],
0,
"Python — dasturlar yaratish uchun ishlatiladigan dasturlash tili.",
'print("Salom")'
),

(
"print() vazifasi nima?",
["Ma’lumot chiqarish", "Fayl o‘chirish", "Kompyuterni o‘chirish", "Internet ulash"],
0,
"print() qiymatni ekranga chiqaradi.",
'print("Salom") → Salom'
),

(
"age = 20 da age nima?",
["O‘zgaruvchi", "Sikl", "Modul", "Exception"],
0,
"age — 20 qiymatini saqlovchi o‘zgaruvchi nomi.",
"age = 20"
),

(
"Qiymat biriktirish uchun qaysi belgi?",
["=", "==", "!=", ">="],
0,
"= o‘ng tomondagi qiymatni chap tomondagi nomga biriktiradi.",
'name = "Ali"'
),

(
'"15" ning turi nima?',
["str", "int", "float", "bool"],
0,
"Qo‘shtirnoq ichidagi 15 matn, ya’ni str.",
'type("15")'
),

(
"True turi nima?",
["bool", "str", "int", "float"],
0,
"True va False bool turiga kiradi.",
"active = True"
),

(
"10 % 3 natijasi?",
["1", "0", "3", "10"],
0,
"% bo‘lish qoldig‘ini beradi.",
"10 % 3 → 1"
),

(
"2 ** 3 natijasi?",
["8", "6", "9", "5"],
0,
"** darajaga ko‘tarish operatori.",
"2 ** 3 → 8"
),

(
"input() odatda nimani qaytaradi?",
["str", "int", "float", "bool"],
0,
"input() foydalanuvchi kiritgan ma’lumotni matn sifatida qaytaradi.",
'name = input("Ism: ")'
),

(
"Son olish uchun qaysi yozuv mos?",
["int(input())", "input(int())", "print(input())", "str(int())"],
0,
"int() kiritilgan butun sonni int ga aylantiradi.",
'age = int(input("Yosh: "))'
),

(
"Tenglikni tekshiruvchi operator?",
["==", "=", "=>", "==="],
0,
"== ikki qiymat tengligini tekshiradi.",
"age == 18"
),

(
"5 > 2 natijasi?",
["True", "False", "5", "2"],
0,
"5 soni 2 dan katta, shuning uchun True.",
"print(5 > 2)"
),

(
"if nima qiladi?",
["Shart tekshiradi", "Fayl ochadi", "Internet ulaydi", "List yaratadi"],
0,
"if shart rost bo‘lsa kod blokini bajaradi.",
'if age >= 18: print("OK")'
),

(
"if shartidan keyin odatda nima yoziladi?",
[":", ";", ".", ","],
0,
"Ikki nuqta blok boshlanishini bildiradi.",
"if x > 0:"
),

(
"else qachon ishlaydi?",
["Oldingi shartlar bajarilmaganda", "Har doim", "Faqat siklda", "Faqat True da"],
0,
"else oldingi if/elif shartlari mos kelmaganda ishlaydi.",
"if x: ... else: ..."
),

(
"elif nima uchun kerak?",
["Qo‘shimcha shart tekshirish", "Siklni to‘xtatish", "List yaratish", "Fayl yozish"],
0,
"elif birinchi shart bajarilmasa boshqa shartni tekshiradi.",
"if x > 10: ... elif x > 5: ..."
),

(
"and qanday ishlaydi?",
["Barcha shartlar rost bo‘lishi kerak", "Bittasi rost bo‘lsa yetarli", "Teskarisini oladi", "Qiymat beradi"],
0,
"and umumiy natijani True qilish uchun barcha shartlarni rost talab qiladi.",
"age >= 18 and has_id"
),

(
"not nima qiladi?",
["Mantiqiy qiymatni teskarilaydi", "Sonni qo‘shadi", "Sikl yaratadi", "Fayl ochadi"],
0,
"not True → False, not False → True.",
"if not blocked:"
),

(
"while qachon takrorlaydi?",
["Shart True bo‘lganda", "Faqat bir marta", "Faqat False bo‘lganda", "Faqat list bilan"],
0,
"while shart True bo‘lib turgan paytda ishlaydi.",
"while count <= 5:"
),

(
"while siklida hisoblagichni o‘zgartirish nega kerak?",
["Siklni tugatishga yaqinlashish uchun", "Matn chiqarish uchun", "Fayl yaratish uchun", "Class yaratish uchun"],
0,
"Hisoblagich o‘zgarsa shart oxirida False bo‘lishi mumkin.",
"count += 1"
),

(
"for nimaga qulay?",
["Takroriy ishlar uchun", "Faqat xatolar uchun", "Faqat fayl uchun", "Faqat class uchun"],
0,
"for ketma-ketliklar bo‘ylab takrorlash uchun qulay.",
"for i in range(5):"
),

(
"range(5) nimani beradi?",
["0,1,2,3,4", "1,2,3,4,5", "0,1,2,3,4,5", "Faqat 5"],
0,
"range yuqori chegarani qo‘shmaydi va standart 0 dan boshlanadi.",
"list(range(5))"
),

(
"break nima qiladi?",
["Siklni to‘xtatadi", "Faqat joriy aylanishni tashlaydi", "Qiymat beradi", "Funksiya yaratadi"],
0,
"break butun siklni darhol tugatadi.",
"if i == 5: break"
),

(
"continue nima qiladi?",
["Joriy aylanishni tashlaydi", "Butun siklni tugatadi", "Fayl yopadi", "Listni o‘chiradi"],
0,
"continue keyingi aylanishga o‘tadi.",
"if i == 3: continue"
),

(
"Listning birinchi indeksi?",
["0", "1", "-1", "2"],
0,
"Python list indekslari 0 dan boshlanadi.",
"items[0]"
),

(
"append() nima qiladi?",
["Oxiriga element qo‘shadi", "Element o‘chiradi", "Listni bo‘shatadi", "Stringga aylantiradi"],
0,
"append() list oxiriga yangi element qo‘shadi.",
"numbers.append(10)"
),

(
"Slicing [1:3] nimani anglatadi?",
["1 dan boshlanib 3 gacha, 3 kirmaydi", "Faqat 3", "1 va 3", "Barcha list"],
0,
"Slicingda start kiradi, end kirmaydi.",
"items[1:3]"
),

(
"sort() nima qiladi?",
["Listni tartiblaydi", "Listga qo‘shadi", "Element o‘chiradi", "Stringni kattalashtiradi"],
0,
"sort() list elementlarini tartiblaydi.",
"numbers.sort()"
),

(
"Tuplening muhim xususiyati?",
["O‘zgarmas ketma-ketlik", "Har doim o‘zgaruvchan", "Faqat son saqlaydi", "Indeksi yo‘q"],
0,
"Tuple elementlari odatda o‘zgartirilmaydi.",
"point = (10, 20)"
),

(
"Tuple qaysi belgida yoziladi?",
["()", "[]", "{}", "<>"],
0,
"Tuple odatda yumaloq qavs bilan yoziladi.",
'colors = ("red", "blue")'
),

(
"Dictionary qanday tuziladi?",
["key:value", "faqat indeks", "faqat qiymat", "faqat string"],
0,
"Dictionary kalit va qiymat juftliklarini saqlaydi.",
'{"name": "Ali"}'
),

(
"Dictionary qiymatini qanday olamiz?",
["Kalit orqali", "Faqat indeks orqali", "Faqat loop orqali", "Faqat print orqali"],
0,
"student['name'] kabi kalit orqali qiymat olinadi.",
'student["name"]'
),

(
"Setning asosiy xususiyati?",
["Takroriy qiymatlarni saqlamaslik", "Indeks bilan ishlash", "Faqat matn saqlash", "Har doim tartiblangan bo‘lish"],
0,
"Set noyob qiymatlar to‘plamidir.",
"set([1, 1, 2]) → {1, 2}"
),

(
"Setga aylantirish nimaga foydali?",
["Takrorlarni olib tashlashga", "Fayl yozishga", "Funksiya chaqirishga", "Matnni tarjima qilishga"],
0,
"set() takroriy qiymatlarni bitta nusxaga tushiradi.",
"unique = set(names)"
),

(
"Funksiya yaratish uchun?",
["def", "func", "function", "make"],
0,
"Python funksiyasi def bilan aniqlanadi.",
"def add(a, b):"
),

(
"Parametr nima?",
["Funksiyaga kiruvchi qiymat uchun nom", "Faqat natija", "Faqat xato", "Fayl nomi"],
0,
"Parametr funksiya qabul qiladigan qiymatni nomlaydi.",
"def greet(name):"
),

(
"return nima qiladi?",
["Qiymatni funksiyadan qaytaradi", "Faqat ekranga chiqaradi", "Siklni boshlaydi", "Faylni o‘chiradi"],
0,
"return natijani funksiya chaqirilgan joyga qaytaradi.",
"return a + b"
),

(
"print va return farqi?",
["print ko‘rsatadi, return qaytaradi", "Ular aynan bir xil", "return faqat matn", "print faqat son"],
0,
"print ekranga chiqaradi, return natijani keyingi kodda ishlatishga qaytaradi.",
"result = add(2, 3)"
),

(
"Local o‘zgaruvchi odatda qayerda?",
["Funksiya ichida", "Faqat modulda", "Faqat listda", "Faqat internetda"],
0,
"Funksiya ichidagi o‘zgaruvchi shu scope ichida local bo‘ladi.",
"def f(): x = 10"
),

(
"Global o‘zgaruvchi qayerda bo‘lishi mumkin?",
["Funksiya tashqarisida", "Faqat if ichida", "Faqat listda", "Faqat class metodida"],
0,
"Modulning yuqori darajasida yaratilgan nom global scope ga ega bo‘lishi mumkin.",
"x = 10"
),

(
"String nima?",
["Matn", "Butun son", "List", "Bool"],
0,
"str matnlarni ifodalaydi.",
'name = "Ali"'
),

(
"upper() nima qiladi?",
["Katta harfga o‘tkazadi", "Sonni bo‘ladi", "Listni o‘chiradi", "Fayl yaratadi"],
0,
"upper() harflarni katta ko‘rinishga o‘tkazadi.",
'"python".upper()'
),

(
"f-string nimaga qulay?",
["O‘zgaruvchini matn ichiga qo‘shishga", "Siklni to‘xtatishga", "Fayl o‘chirishga", "List yaratishga"],
0,
"f-string matn ichida {} orqali qiymatlarni qulay joylashtiradi.",
'f"Salom {name}"'
),

(
"f-string uchun satr oldidan nima yoziladi?",
["f", "s", "str", "text"],
0,
"f prefiksi string ichida ifodalarni ishlatish imkonini beradi.",
'f"{name}"'
),

(
"try/except nimaga kerak?",
["Xatolarni boshqarishga", "Faqat printga", "Faqat listga", "Internetga"],
0,
"try/except kutiladigan exceptionlarni ushlab, mos javob berishga yordam beradi.",
"try: int(x)"
),

(
'int("salom") qanday exception berishi mumkin?',
["ValueError", "NameError", "IndexError", "KeyError"],
0,
"salom butun songa aylantirilmagani uchun ValueError yuzaga kelishi mumkin.",
"except ValueError:"
),

(
"Fayl yozish rejimi?",
["w", "r", "a", "read"],
0,
"w yozish rejimi.",
'open("data.txt", "w")'
),

(
"Fayl o‘qish rejimi?",
["r", "w", "a", "write"],
0,
"r o‘qish rejimi.",
'open("data.txt", "r")'
),

(
"Modulni ulash?",
["import", "include", "using", "module"],
0,
"import modulni dasturga ulash uchun ishlatiladi.",
"import math"
),

(
"random.randint(1,10) nima beradi?",
["1–10 oralig‘idagi tasodifiy int", "Faqat 1", "Faqat 10", "Matn"],
0,
"randint ikkala chegara ham kiradigan tasodifiy butun son qaytaradi.",
"random.randint(1, 10)"
),

(
"List comprehension nima?",
["List yaratishning ixcham usuli", "Fayl turi", "Exception", "Class"],
0,
"List comprehension list yaratishni qisqa va ifodali yozishga yordam beradi.",
"[x*x for x in range(5)]"
),

(
"Juft sonlarni tanlash sharti?",
["x % 2 == 0", "x % 2 == 1", "x / 2 == 0", "x + 2 == 0"],
0,
"2 ga bo‘lgandagi qoldiq 0 bo‘lsa son juft.",
"[x for x in nums if x % 2 == 0]"
),

(
"Class nima?",
["Objectlar uchun andoza", "Faqat funksiya", "Fayl", "List"],
0,
"Class objectlarning tuzilishi va xatti-harakatini belgilaydi.",
"class Student: pass"
),

(
"Object nima?",
["Classdan yaratilgan nusxa", "Faqat string", "Faqat funksiya", "Exception"],
0,
"Object class asosida yaratilgan aniq nusxa.",
"student = Student()"
),

(
"__init__ qachon ishlaydi?",
["Object yaratilganda", "Faqat loopda", "Faqat faylda", "Faqat xatoda"],
0,
"__init__ boshlang‘ich holatni o‘rnatish uchun object yaratilishida ishlaydi.",
'Student("Ali")'
),

(
"self nimani bildiradi?",
["Joriy objectning o‘zini", "Global modulni", "Class nomini", "Faylni"],
0,
"self metod ichida ayni objectga murojaat qilish uchun ishlatiladi.",
"self.name = name"
),

(
"Inheritance nima?",
["Bir classdan boshqasiga imkoniyat meros qilish", "Faylni nusxalash", "Listni tartiblash", "Stringni o‘zgartirish"],
0,
"Inheritance umumiy kodni boshqa classlarda qayta ishlatishga yordam beradi.",
"class Dog(Animal): pass"
),

(
"Class ichidagi funksiya nima?",
["Metod", "List", "Tuple", "Modul"],
0,
"Class ichidagi funksiya metod deyiladi.",
"def speak(self):"
),

(
"Yakuniy loyiha nima uchun?",
["Bilimlarni birlashtirish uchun", "Faqat print uchun", "Faqat test uchun", "Pythonni o‘chirish uchun"],
0,
"Loyiha o‘rganilgan tushunchalarni bitta amaliy dasturga birlashtiradi.",
"Mini Student Manager"
),

(
"Dasturchi xatoga qanday qarashi kerak?",
["Sababini tahlil qilib o‘rganish", "Darhol taslim bo‘lish", "Xatoni yashirish", "Kod yozmaslik"],
0,
"Xato dasturlashning tabiiy qismi. Uni tahlil qilish muhim ko‘nikma.",
"Error → sabab → tuzatish"
),

]

assert len(TESTS) == TOTAL_LESSONS * 2

# (belgi, nom, ball)
LEVELS = [
    ("🟢", "OSON", 10),
    ("🟡", "O‘RTA", 20),
]
MAX_LESSON_SCORE = sum(x[2] for x in LEVELS)


# ============================================================
# MATNNI TELEGRAM HTML GA AYLANTIRISH VA BO‘LISH
# ============================================================

_FENCE_RE = re.compile(r"```([\w+#.\-]*)[ \t]*\n(.*?)```", re.S)
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")


def esc(value) -> str:
    return html.escape(str(value), quote=False)


def _fmt(text: str) -> str:
    text = esc(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def _inline(text: str) -> str:
    out = []
    pos = 0
    for m in _INLINE_CODE_RE.finditer(text):
        out.append(_fmt(text[pos:m.start()]))
        out.append("<code>" + esc(m.group(1)) + "</code>")
        pos = m.end()
    out.append(_fmt(text[pos:]))
    return "".join(out)


def _text_block(block: str) -> str:
    lines = []
    for line in block.split("\n"):
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.*)$", line)
        bullet = re.match(r"^(\s*)[*\-+]\s+(.*)$", line)
        if heading:
            lines.append("<b>" + _inline(heading.group(1).replace("**", "")) + "</b>")
        elif re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line):
            lines.append("──────────")
        elif bullet:
            lines.append(bullet.group(1) + "• " + _inline(bullet.group(2)))
        else:
            lines.append(_inline(line))
    return "\n".join(lines)


def md_to_html(text: str) -> str:
    """Gemini yozadigan Markdown'ni Telegram HTML formatiga o‘tkazadi."""
    out = []
    pos = 0
    for m in _FENCE_RE.finditer(text):
        out.append(_text_block(text[pos:m.start()]))
        lang = m.group(1)
        code = esc(m.group(2).rstrip("\n"))
        if lang:
            out.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
        else:
            out.append(f"<pre>{code}</pre>")
        pos = m.end()
    out.append(_text_block(text[pos:]))
    return "".join(out).strip()


def split_markdown(text: str, limit: int = TG_CHUNK) -> list[str]:
    """Uzun matnni Telegram limitiga mos bo‘laklarga bo‘ladi.
    Kod bloki o‘rtasida bo‘linsa, blok yopilib, keyingi bo‘lakda qayta ochiladi."""
    chunks: list[str] = []
    cur: list[str] = []
    cur_len = 0
    in_code = False
    lang = ""
    piece_size = max(limit - 200, 500)

    for line in text.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        is_fence = stripped.startswith("```")
        pieces = [line[i:i + piece_size] for i in range(0, len(line), piece_size)] or [""]

        for piece in pieces:
            if not is_fence and cur and cur_len + len(piece) + 1 > limit:
                body = "\n".join(cur)
                if in_code:
                    body += "\n```"
                chunks.append(body)
                cur = [f"```{lang}"] if in_code else []
                cur_len = len(cur[0]) + 1 if cur else 0
            cur.append(piece)
            cur_len += len(piece) + 1

        if is_fence:
            if in_code:
                in_code = False
                lang = ""
            else:
                in_code = True
                lang = stripped[3:].strip()

    if cur:
        body = "\n".join(cur)
        if in_code:
            body += "\n```"
        chunks.append(body)

    return [c.strip() for c in chunks if c.strip()]


async def push(message: Message, chunk: str, placeholder: Message | None = None, markup=None):
    """Bitta bo‘lakni yuboradi. HTML xato bersa, oddiy matn sifatida yuboradi.
    placeholder berilsa, shu xabarni tahrirlaydi (tezroq)."""
    html_text = md_to_html(chunk)
    if html_text and len(html_text) <= 4096:
        try:
            if placeholder is not None:
                return await placeholder.edit_text(html_text, reply_markup=markup)
            return await message.answer(html_text, reply_markup=markup)
        except TelegramBadRequest as e:
            logger.warning("HTML yuborilmadi, oddiy matnga o‘tildi: %s", e)

    plain = chunk[:4096]
    if placeholder is not None:
        try:
            return await placeholder.edit_text(plain, parse_mode=None, reply_markup=markup)
        except TelegramBadRequest:
            pass
    return await message.answer(plain, parse_mode=None, reply_markup=markup)


async def send_text(message: Message, text: str, reply_markup=None, placeholder: Message | None = None):
    chunks = split_markdown(text) or [text]
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await push(
            message,
            chunk,
            placeholder=placeholder if i == 0 else None,
            markup=reply_markup if is_last else None,
        )


# ============================================================
# GEMINI
# ============================================================

_thinking_ok = True


def make_config(use_thinking: bool):
    kwargs = {
        "system_instruction": SYSTEM_PROMPT,
        "max_output_tokens": GEMINI_MAX_OUTPUT,
    }
    if use_thinking and GEMINI_THINKING_LEVEL:
        try:
            kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level=GEMINI_THINKING_LEVEL
            )
        except Exception:
            pass
    return types.GenerateContentConfig(**kwargs)


async def ask_gemini(history, question: str) -> str:
    global _thinking_ok

    items = list(history)
    while items and items[0][0] != "user":
        items.pop(0)

    contents = [
        types.Content(role=role, parts=[types.Part(text=text)])
        for role, text in items
    ]
    contents.append(types.Content(role="user", parts=[types.Part(text=question)]))

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = await asyncio.wait_for(
                gemini_client.aio.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=make_config(_thinking_ok),
                ),
                timeout=GEMINI_TIMEOUT,
            )
            text = (response.text or "").strip()
            if text:
                return text
            raise RuntimeError("Gemini bo‘sh javob qaytardi")
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            last_error = e
            msg = str(e).lower()
            if _thinking_ok and GEMINI_THINKING_LEVEL and "think" in msg:
                logger.warning("Model thinking sozlamasini qo‘llamadi, o‘chirildi: %s", e)
                _thinking_ok = False
                continue
            if attempt < 2:
                await asyncio.sleep(1)
                continue
    raise last_error or RuntimeError("Noma’lum Gemini xatosi")


async def keep_typing(chat_id: int, stop: asyncio.Event):
    while not stop.is_set():
        try:
            await bot.send_chat_action(chat_id, ChatAction.TYPING)
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=4)
        except asyncio.TimeoutError:
            pass


class AiMode(Filter):
    async def __call__(self, message: Message) -> bool:
        return bool(message.from_user) and user(message.from_user.id)["ai"]


# ============================================================
# DARS, PROGRESS VA TEST MATNLARI
# ============================================================

def lesson_md(n: int) -> str:
    title, intro, code, explain, error, task = DATA[n - 1]
    return (
        f"# 🐍 {n}-DARS — {title}\n\n"
        f"👋 Salom! Bugun yangi mavzuni bosqichma-bosqich o‘rganamiz.\n\n"
        f"# 📌 Dars maqsadi\n{intro}\n\n"
        f"# 🧠 Asosiy tushuncha\n{explain}\n\n"
        f"# 💻 Kod misoli\n```python\n{code}\n```\n\n"
        f"# ⚠️ Ko‘p uchraydigan xato\n{error}\n\n"
        f"# 🎯 Mashq\n{task}\n\n"
        f"❓ Savolingiz bo‘lsa — 🤖 AI Mentor'dan so‘rang.\n"
        f"📝 Tayyor bo‘lsangiz, «Testni boshlash» tugmasini bosing."
    )


def lessons_list_html(u: dict) -> str:
    lines = ["<b>📚 Python darslari</b>", ""]
    for n in range(1, TOTAL_LESSONS + 1):
        if n in u["done"]:
            mark = "✅"
        elif is_unlocked(u, n):
            mark = "▶️"
        else:
            mark = "🔒"
        lines.append(f"{mark} {n}. {esc(DATA[n - 1][0])}")
    lines.append("")
    lines.append("✅ tugatilgan · ▶️ ochiq · 🔒 yopiq")
    lines.append("Dars raqamini bosing 👇")
    return "\n".join(lines)


def lessons_markup(u: dict) -> InlineKeyboardMarkup:
    rows, row = [], []
    for n in range(1, TOTAL_LESSONS + 1):
        if n in u["done"]:
            label = f"✅{n}"
        elif is_unlocked(u, n):
            label = f"▶️{n}"
        else:
            label = f"🔒{n}"
        row.append(InlineKeyboardButton(text=label, callback_data=f"L:{n}"))
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def progress_html(u: dict) -> str:
    done = len(u["done"])
    percent = round(done * 100 / TOTAL_LESSONS)
    filled = round(done * 10 / TOTAL_LESSONS)
    bar = "█" * filled + "░" * (10 - filled)
    cur = first_incomplete(u)
    lines = [
        "<b>📊 Sizning progressingiz</b>",
        "",
        f"✅ Tugatilgan darslar: <b>{done}/{TOTAL_LESSONS}</b>",
        f"{bar} {percent}%",
        f"⭐ Umumiy ball: <b>{total_score(u)}/{TOTAL_LESSONS * MAX_LESSON_SCORE}</b>",
    ]
    if all_done(u):
        lines.append("")
        lines.append("🏆 Siz barcha darslarni tugatdingiz!")
    else:
        lines.append(f"📍 Keyingi dars: <b>{cur}. {esc(DATA[cur - 1][0])}</b>")
    return "\n".join(lines)


def question_view(n: int, q: int, state: dict):
    icon, level, _points = LEVELS[q]
    question, options, _correct, _expl, _code = TESTS[2 * (n - 1) + q]

    if len(state["orders"]) <= q:
        order = list(range(len(options)))
        random.shuffle(order)
        state["orders"].append(order)
    order = state["orders"][q]

    text = (
        f"<b>📝 {n}-dars testi</b>\n"
        f"{icon} <b>{level}</b> — savol {q + 1}/{len(LEVELS)}\n\n"
        f"<b>{esc(question)}</b>"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{'ABCD'[pos]}) {options[idx]}", callback_data=f"a:{q}:{pos}")]
        for pos, idx in enumerate(order)
    ])
    return text, markup


def result_view(n: int, state: dict, correct_count: int, points: int, passed: bool, first_try_done: bool):
    lines = [
        f"<b>📊 {n}-dars — test natijasi</b>",
        "",
        f"✅ To‘g‘ri javoblar: <b>{correct_count}/{len(LEVELS)}</b>",
        f"⭐ Ball: <b>{points}/{MAX_LESSON_SCORE}</b>",
        "",
    ]
    for q, (icon, level, _pts) in enumerate(LEVELS):
        question, options, correct, expl, code = TESTS[2 * (n - 1) + q]
        picked = state["picks"][q]
        lines.append(f"{icon} <b>{level}</b>: {esc(question)}")
        if picked == correct:
            lines.append("✅ To‘g‘ri!")
        else:
            lines.append(f"❌ Sizning javobingiz: {esc(options[picked])}")
            lines.append(f"✔️ To‘g‘ri javob: <b>{esc(options[correct])}</b>")
        lines.append(f"💡 {esc(expl)}")
        lines.append(f"💻 <code>{esc(code)}</code>")
        lines.append("")

    buttons = []
    if passed:
        if n == TOTAL_LESSONS:
            lines.append("🏆 Tabriklaymiz! Siz barcha 30 ta darsni tugatdingiz!")
        else:
            lines.append(f"🎉 {n}-dars tugadi! {n + 1}-dars ochildi.")
            buttons.append([InlineKeyboardButton(text="➡️ Keyingi dars", callback_data=f"L:{n + 1}")])
    else:
        lines.append("😕 Bu safar bo‘lmadi. Dars matnini qayta o‘qib, testni yana urinib ko‘ring.")
    buttons.append([
        InlineKeyboardButton(text="🔁 Qayta urinish", callback_data=f"T:{n}"),
        InlineKeyboardButton(text="📚 Darslar", callback_data="LIST"),
    ])
    return "\n".join(lines).strip(), InlineKeyboardMarkup(inline_keyboard=buttons)


HELP_TEXT = (
    "<b>ℹ️ Yordam</b>\n\n"
    "🐍 <b>Python</b> — 30 ta dars, har birida 2 ta test (🟢 oson, 🟡 o‘rta).\n"
    "📚 <b>Darslar</b> — darslar ro‘yxati. Keyingi dars oldingisining testi tugagach ochiladi.\n"
    "▶️ <b>Davom etish</b> — qolgan joyingizdan davom etasiz.\n"
    "🤖 <b>AI Mentor</b> — Python bo‘yicha istalgan savolni yozing, kodingizni yuboring.\n"
    "📊 <b>Progress</b> — natijalaringiz.\n"
    "⬅️ <b>Orqaga</b> — oldingi menyuga qaytish.\n\n"
    "Komandalar: /start, /help"
)


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

def stop_ai(u: dict) -> None:
    u["ai"] = False


async def send_lesson(message: Message, u: dict, n: int) -> None:
    u["cur"] = n
    u["viewed"] = True
    u["ai"] = False
    u["menu"] = "lesson"
    await send_text(message, lesson_md(n), reply_markup=LESSON_MENU)


async def start_test(message: Message, u: dict, n: int) -> None:
    u["ai"] = False
    u["menu"] = "lesson"
    state = {"lesson": n, "q": 0, "picks": [], "orders": [], "mid": None}
    u["test"] = state
    text, markup = question_view(n, 0, state)
    sent = await message.answer(text, reply_markup=markup)
    state["mid"] = sent.message_id


# ============================================================
# HANDLERLAR: /start, MENYULAR
# ============================================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    u = user(message.from_user.id)
    u["ai"] = False
    u["test"] = None
    u["menu"] = "main"
    name = esc(message.from_user.first_name or "do‘st")
    await message.answer(
        f"👋 Salom, <b>{name}</b>!\n\n"
        "🎓 <b>CODE MASTER</b> — Python o‘rgatuvchi AI mentor.\n\n"
        "Bu yerda siz:\n"
        "• 30 ta dars orqali Pythonni boshidan o‘rganasiz;\n"
        "• har bir dars bo‘yicha test yechasiz;\n"
        "• 🤖 AI Mentor'dan istalgan savolni so‘raysiz.\n\n"
        "Boshlash uchun bo‘limni tanlang 👇",
        reply_markup=MAIN,
    )


@router.message(Command("help"))
@router.message(F.text == B_HELP)
async def on_help(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)
    await message.answer(HELP_TEXT, reply_markup=current_kb(u))


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)
    u["menu"] = "main"
    await message.answer("🏠 Asosiy menyu", reply_markup=MAIN)


@router.message(F.text == B_PY)
async def on_python(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)
    u["menu"] = "python"
    await message.answer(
        "🐍 <b>Python bo‘limi</b>\n\n"
        "Darslarni o‘rganing, test ishlang yoki 🤖 AI Mentor'dan so‘rang.",
        reply_markup=PYTHON,
    )


@router.message(F.text == B_CPP)
async def on_cpp(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)
    u["menu"] = "main"
    await message.answer("⚙️ C++ bo‘limi tez orada qo‘shiladi.", reply_markup=MAIN)


@router.message(F.text == B_PROG)
async def on_progress(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)
    await message.answer(progress_html(u), reply_markup=current_kb(u))


@router.message(F.text == B_LESSONS)
async def on_lessons(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)
    if u["menu"] not in ("python", "lesson"):
        u["menu"] = "python"
    await message.answer(lessons_list_html(u), reply_markup=lessons_markup(u))


@router.message(F.text == B_CONT)
async def on_continue(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)

    if all_done(u):
        u["menu"] = "python"
        await message.answer(
            "🏆 Tabriklaymiz! Siz barcha 30 ta darsni tugatdingiz.\n"
            "Istalgan darsni 📚 Darslar bo‘limidan qayta ko‘rishingiz mumkin.",
            reply_markup=PYTHON,
        )
        return

    n = u["cur"]
    if n in u["done"]:
        n = first_incomplete(u)
        u["cur"] = n
        u["viewed"] = False

    if not is_unlocked(u, n):
        n = first_incomplete(u)
        u["cur"] = n
        u["viewed"] = False

    if not u["viewed"]:
        await send_lesson(message, u, n)
    else:
        await start_test(message, u, n)


@router.message(F.text == B_TEST)
async def on_test_button(message: Message):
    u = user(message.from_user.id)
    stop_ai(u)
    n = u["cur"]
    if not is_unlocked(u, n):
        n = first_incomplete(u)
        u["cur"] = n
    await start_test(message, u, n)


@router.message(F.text == B_AI)
async def on_ai_open(message: Message):
    u = user(message.from_user.id)
    u["ai"] = True
    u["menu"] = "ai"
    if gemini_client is None:
        await message.answer(
            "❌ AI Mentor hozircha sozlanmagan (GEMINI_API_KEY topilmadi).",
            reply_markup=AI_MENU,
        )
        return
    await message.answer(AI_INTRO, reply_markup=AI_MENU)


@router.message(F.text == B_CLEAR)
async def on_ai_clear(message: Message):
    u = user(message.from_user.id)
    u["history"].clear()
    if u["ai"]:
        await message.answer("🧹 Suhbat tozalandi. Yangi savol yozing.", reply_markup=AI_MENU)
    else:
        await message.answer("🧹 Suhbat tozalandi.", reply_markup=current_kb(u))


@router.message(F.text == B_BACK)
async def on_back(message: Message):
    u = user(message.from_user.id)
    if u["ai"] or u["menu"] in ("ai", "lesson"):
        u["ai"] = False
        u["menu"] = "python"
        await message.answer("🐍 Python bo‘limi", reply_markup=PYTHON)
    else:
        u["ai"] = False
        u["menu"] = "main"
        await message.answer("🏠 Asosiy menyu", reply_markup=MAIN)


# ============================================================
# CALLBACKLAR: DARSLAR VA TEST
# ============================================================

@router.callback_query(F.data == "LIST")
async def cb_list(cb: CallbackQuery):
    await cb.answer()
    if not isinstance(cb.message, Message):
        return
    u = user(cb.from_user.id)
    stop_ai(u)
    await cb.message.answer(lessons_list_html(u), reply_markup=lessons_markup(u))


@router.callback_query(F.data.startswith("L:"))
async def cb_lesson(cb: CallbackQuery):
    try:
        n = int(cb.data.split(":")[1])
    except (ValueError, IndexError):
        await cb.answer()
        return
    if not 1 <= n <= TOTAL_LESSONS:
        await cb.answer()
        return

    u = user(cb.from_user.id)
    if not is_unlocked(u, n):
        await cb.answer(f"🔒 Avval {n - 1}-darsni va uning testini tugating.", show_alert=True)
        return

    await cb.answer()
    if not isinstance(cb.message, Message):
        return
    await send_lesson(cb.message, u, n)


@router.callback_query(F.data.startswith("T:"))
async def cb_test(cb: CallbackQuery):
    try:
        n = int(cb.data.split(":")[1])
    except (ValueError, IndexError):
        await cb.answer()
        return
    u = user(cb.from_user.id)
    if not 1 <= n <= TOTAL_LESSONS or not is_unlocked(u, n):
        await cb.answer("🔒 Bu dars hali ochilmagan.", show_alert=True)
        return
    await cb.answer()
    if not isinstance(cb.message, Message):
        return
    u["cur"] = n
    await start_test(cb.message, u, n)


@router.callback_query(F.data.startswith("a:"))
async def cb_answer(cb: CallbackQuery):
    u = user(cb.from_user.id)
    state = u["test"]
    try:
        _, q_raw, pos_raw = cb.data.split(":")
        q, pos = int(q_raw), int(pos_raw)
    except (ValueError, TypeError):
        await cb.answer()
        return

    if (
        not state
        or not isinstance(cb.message, Message)
        or cb.message.message_id != state["mid"]
        or q != state["q"]
        or not 0 <= pos < len(state["orders"][q])
    ):
        await cb.answer("Bu test eskirgan. 📝 Testni qaytadan boshlang.")
        return

    await cb.answer()

    n = state["lesson"]
    order = state["orders"][q]
    state["picks"].append(order[pos])
    state["q"] += 1

    if state["q"] < len(LEVELS):
        text, markup = question_view(n, state["q"], state)
        try:
            await cb.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as e:
            logger.warning("Savolni tahrirlab bo‘lmadi: %s", e)
        return

    # Test tugadi
    correct_count = 0
    points = 0
    for i, (_icon, _level, pts) in enumerate(LEVELS):
        if state["picks"][i] == TESTS[2 * (n - 1) + i][2]:
            correct_count += 1
            points += pts

    passed = correct_count >= 1
    u["test"] = None

    if passed:
        u["done"][n] = max(u["done"].get(n, 0), points)
        new_cur = first_incomplete(u)
        if new_cur != u["cur"]:
            u["viewed"] = False
        u["cur"] = new_cur
        await save_progress()

    text, markup = result_view(n, state, correct_count, points, passed, True)
    try:
        await cb.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        logger.warning("Natijani tahrirlab bo‘lmadi: %s", e)
        await cb.message.answer(text, reply_markup=markup)


# ============================================================
# AI MENTOR REJIMI
# ============================================================

@router.message(AiMode())
async def ai_chat(message: Message):
    uid = message.from_user.id
    u = user(uid)
    text = (message.text or "").strip()

    if not text:
        await message.answer("✍️ Iltimos, savolingizni matn ko‘rinishida yozing.", reply_markup=AI_MENU)
        return
    if text.startswith("/"):
        await message.answer("ℹ️ AI rejimida savolni oddiy matn qilib yozing yoki ⬅️ Orqaga ni bosing.")
        return
    if gemini_client is None:
        await message.answer("❌ AI Mentor hozircha sozlanmagan.", reply_markup=AI_MENU)
        return

    lock = ai_locks.setdefault(uid, asyncio.Lock())
    if lock.locked():
        await message.answer("⏳ Oldingi savolingizga javob tayyorlanmoqda, biroz kuting.")
        return

    async with lock:
        placeholder = await message.answer("🤔 AI o‘ylayapti...")
        stop = asyncio.Event()
        typing_task = asyncio.create_task(keep_typing(message.chat.id, stop))
        question = text[:MAX_USER_TEXT]
        answer = None
        try:
            answer = await ask_gemini(u["history"], question)
        except Exception:
            logger.exception("Gemini xatosi")
        finally:
            stop.set()
            await typing_task

        if answer is None:
            try:
                await placeholder.edit_text(AI_ERROR)
            except TelegramBadRequest:
                await message.answer(AI_ERROR)
            return

        u["history"].append(("user", question))
        u["history"].append(("model", answer[:HISTORY_ANSWER_CHARS]))

        chunks = split_markdown(answer) or [answer]
        for i, chunk in enumerate(chunks):
            await push(message, chunk, placeholder=placeholder if i == 0 else None)


# ============================================================
# BOSHQA XABARLAR (AI rejimidan tashqarida botni buzmaydi)
# ============================================================

@router.message(F.text)
async def fallback_text(message: Message):
    u = user(message.from_user.id)
    await message.answer(
        "🤔 Buni tushunmadim. Iltimos, pastdagi menyudan foydalaning.\n"
        "Savol bermoqchi bo‘lsangiz: 🐍 Python → 🤖 AI Mentor.",
        reply_markup=current_kb(u),
    )


@router.error()
async def on_error(event: ErrorEvent):
    logger.error("Handler xatosi: %s", event.exception, exc_info=event.exception)
    return True


# ============================================================
# ISHGA TUSHIRISH
# ============================================================

async def main():
    load_progress()

    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Botni boshlash"),
            BotCommand(command="menu", description="Asosiy menyu"),
            BotCommand(command="help", description="Yordam"),
        ])
    except Exception:
        logger.warning("Komandalarni o‘rnatib bo‘lmadi")

    logger.info("CODE MASTER ishga tushdi. Gemini modeli: %s", GEMINI_MODEL)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to‘xtatildi.")

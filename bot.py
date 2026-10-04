
import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from dotenv import load_dotenv
from google import genai


# =========================================================
# SOZLAMALAR
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylda topilmadi!")

dp = Dispatcher()

ai = None
if GEMINI_API_KEY:
    ai = genai.Client(api_key=GEMINI_API_KEY)


# =========================================================
# 30 TA DARS
# =========================================================

PYTHON_LESSONS = [
    "Python bilan tanishuv",
    "print() funksiyasi",
    "O‘zgaruvchilar",
    "Ma'lumot turlari",
    "input() funksiyasi",
    "Matematik amallar",
    "if / else",
    "elif",
    "Taqqoslash operatorlari",
    "Mantiqiy operatorlar",
    "while sikli",
    "for sikli",
    "range()",
    "Listlar",
    "List metodlari",
    "Tuple",
    "Set",
    "Dictionary",
    "String",
    "String metodlari",
    "Funksiyalar",
    "return",
    "Parametrlar",
    "Modullar",
    "try / except",
    "Fayllar bilan ishlash",
    "Class",
    "Obyektlar",
    "Mini loyiha",
    "Yakuniy loyiha",
]


# =========================================================
# BATAFSIL DARS MA'LUMOTLARI
# =========================================================

LESSON_TEXTS = {

1: """
🐍 1-DARS — PYTHON BILAN Tanishuv

Python — yuqori darajadagi, o‘rganish nisbatan oson bo‘lgan dasturlash tili.

Python yordamida:

• Telegram botlar
• Web saytlar
• AI va Machine Learning
• Kompyuter dasturlari
• Avtomatlashtirish
• O‘yinlar
• Ma'lumotlarni tahlil qilish

kabi loyihalar yaratish mumkin.

📌 Python'ning afzalliklari:

1. Sintaksisi sodda.
2. Juda ko‘p kutubxonalari bor.
3. AI uchun keng ishlatiladi.
4. Web dasturlashda ishlatiladi.
5. Boshlovchilar uchun qulay.

💻 BIRINCHI KOD:

print("Hello World")

Bu kod ekranga:

Hello World

degan yozuvni chiqaradi.

📌 Python kodni yuqoridan pastga qarab bajaradi.

Masalan:

print("Salom")
print("Python")

Natija:

Salom
Python

💡 MUHIM:

Python'da katta va kichik harflar farq qiladi.

Print() ❌
print() ✅

Shuning uchun funksiyalarni to‘g‘ri yozish kerak.
""",

2: """
🖨 2-DARS — print() FUNKSIYASI

print() Python'da eng ko‘p ishlatiladigan funksiyalardan biridir.

U ma'lumotni ekranga chiqaradi.

📌 Oddiy misol:

print("Salom!")

Natija:

Salom!

📌 Bir nechta ma'lumot:

print("Ism:", "Asil")
print("Yosh:", 15)

Natija:

Ism: Asil
Yosh: 15

📌 Son chiqarish:

print(10)
print(25 + 5)

Natija:

10
30

📌 O‘zgaruvchini chiqarish:

ism = "Ali"
print(ism)

Natija:

Ali

📌 Bir nechta qiymat:

ism = "Ali"
yosh = 15

print("Ism:", ism)
print("Yosh:", yosh)

💡 Eslab qol:

print() = ekranga chiqarish.

⚠️ Xato:

print("Salom"

Bu yerda yopuvchi ) yo‘q.

To‘g‘ri:

print("Salom")
""",

3: """
📦 3-DARS — O‘ZGARUVCHILAR

O‘zgaruvchi — ma'lumotni saqlash uchun ishlatiladigan nom.

Masalan:

ism = "Asil"
yosh = 15

Bu yerda:

ism → o‘zgaruvchi
"Asil" → qiymat

yosh → o‘zgaruvchi
15 → qiymat

📌 Misol:

ism = "Ali"
yosh = 16
shahar = "Toshkent"

print(ism)
print(yosh)
print(shahar)

📌 O‘zgaruvchining qiymatini o‘zgartirish mumkin:

yosh = 15
yosh = 16

print(yosh)

Natija:

16

📌 Bir nechta o‘zgaruvchi:

ism, yosh = "Ali", 15

print(ism)
print(yosh)

💡 O‘zgaruvchi nomi:

✅ ism
✅ yosh
✅ user_name
✅ age

❌ 1ism
❌ user-name

O‘zgaruvchi nomini raqam bilan boshlash mumkin emas.

📌 Tavsiya:

user_name = "Ali"

snake_case usuli Python'da juda ko‘p ishlatiladi.
""",

4: """
🔢 4-DARS — MA'LUMOT TURLARI

Python'da ma'lumotlarning turli turlari mavjud.

Asosiy turlar:

1️⃣ str — matn
2️⃣ int — butun son
3️⃣ float — kasr son
4️⃣ bool — True yoki False

📌 str:

ism = "Asil"

📌 int:

yosh = 15

📌 float:

narx = 12.5

📌 bool:

talaba = True

📌 type() yordamida turini bilish mumkin:

x = 10

print(type(x))

Natija:

<class 'int'>

Yana:

ism = "Ali"
print(type(ism))

Natija:

<class 'str'>

💡 Eslab qol:

"Hello" → str
10 → int
10.5 → float
True → bool
""",

5: """
⌨️ 5-DARS — input()

input() foydalanuvchidan ma'lumot olish uchun ishlatiladi.

📌 Oddiy misol:

ism = input("Ismingizni kiriting: ")

print("Salom", ism)

Dastur foydalanuvchidan ism so‘raydi.

📌 Yosh:

yosh = input("Yoshingiz: ")

print("Sizning yoshingiz:", yosh)

⚠️ Muhim:

input() orqali olingan ma'lumot odatda str bo‘ladi.

Agar son kerak bo‘lsa:

yosh = int(input("Yoshingiz: "))

Endi yosh int bo‘ladi.

📌 Misol:

a = int(input("Birinchi son: "))
b = int(input("Ikkinchi son: "))

print(a + b)

Agar:

5
3

kiritilsa:

8

chiqadi.
""",

6: """
➗ 6-DARS — MATEMATIK AMALLAR

Python matematik hisob-kitoblarni ham bajaradi.

Asosiy operatorlar:

+ → qo‘shish
- → ayirish
* → ko‘paytirish
/ → oddiy bo‘lish
// → butun bo‘lish
% → qoldiq
** → daraja

📌 Misollar:

print(5 + 3)
print(10 - 4)
print(5 * 2)
print(10 / 2)

Natija:

8
6
10
5.0

📌 Qoldiq:

print(10 % 3)

Natija:

1

Chunki 10 ni 3 ga bo‘lganda 1 qoldiq qoladi.

📌 Daraja:

print(2 ** 3)

Natija:

8

Chunki:

2 × 2 × 2 = 8

📌 Butun bo‘lish:

print(10 // 3)

Natija:

3
""",

7: """
🔀 7-DARS — if / else

if shart tekshirish uchun ishlatiladi.

Masalan:

yosh = 18

if yosh >= 18:
    print("Siz voyaga yetgansiz")

Agar shart noto‘g‘ri bo‘lsa:

yosh = 15

if yosh >= 18:
    print("Katta")
else:
    print("Yosh")

Natija:

Yosh

📌 else — if sharti bajarilmaganda ishlaydi.

Muhim:

if dan keyin shart yoziladi.

Misol:

x = 10

if x > 5:
    print("5 dan katta")

💡 Python'da bo‘sh joy — indentation — juda muhim.

To‘g‘ri:

if x > 5:
    print("Ha")

Noto‘g‘ri:

if x > 5:
print("Ha")
""",

8: """
🔀 8-DARS — elif

elif bir nechta shartni tekshirish uchun ishlatiladi.

Misol:

ball = 85

if ball >= 90:
    print("A")
elif ball >= 70:
    print("B")
else:
    print("C")

Natija:

B

📌 elif = else if

Bir nechta shart:

yosh = 15

if yosh >= 18:
    print("Katta")
elif yosh >= 13:
    print("O‘smir")
else:
    print("Bola")

Python shartlarni yuqoridan pastga tekshiradi.

Birinchi rost shart bajarilgandan keyin qolganlari tekshirilmaydi.
""",

9: """
⚖️ 9-DARS — TAQQOSLASH OPERATORLARI

Python'da qiymatlarni taqqoslash mumkin.

== → teng
!= → teng emas
> → katta
< → kichik
>= → katta yoki teng
<= → kichik yoki teng

📌 Misollar:

print(5 == 5)

Natija:

True

print(5 == 3)

Natija:

False

📌 Katta:

print(10 > 5)

True

📌 Kichik:

print(3 < 10)

True

📌 Teng emas:

print(5 != 3)

True

💡 == va = bir xil emas!

= → qiymat berish

== → taqqoslash

Misol:

x = 10

if x == 10:
    print("Teng")
""",

10: """
🧠 10-DARS — MANTIQIY OPERATORLAR

Asosiy mantiqiy operatorlar:

and → va
or → yoki
not → emas

📌 and:

yosh = 20

if yosh >= 18 and yosh <= 30:
    print("Mos keladi")

and ishlashi uchun ikkala shart ham True bo‘lishi kerak.

📌 or:

kun = "shanba"

if kun == "shanba" or kun == "yakshanba":
    print("Dam olish")

Bu yerda shartlardan bittasi True bo‘lsa yetarli.

📌 not:

x = False

if not x:
    print("Xato emas")

💡 Mantiqiy operatorlar murakkab shartlar yaratishda juda foydali.
""",

11: """
🔄 11-DARS — while SIKLI

while shart True bo‘lgan vaqt davomida kodni takrorlaydi.

📌 Misol:

son = 1

while son <= 5:
    print(son)
    son += 1

Natija:

1
2
3
4
5

Bu yerda:

son += 1

sonni har safar bittaga oshiradi.

⚠️ Agar shart hech qachon False bo‘lmasa, cheksiz sikl paydo bo‘lishi mumkin.

Masalan:

while True:
    print("Salom")

Bunday kod to‘xtamasdan ishlaydi.

Shuning uchun while bilan ishlaganda sikl qachon tugashini o‘ylash kerak.
""",

12: """
🔁 12-DARS — for SIKLI

for sikli ma'lum miqdordagi takrorlashlar uchun juda qulay.

Misol:

for i in range(5):
    print(i)

Natija:

0
1
2
3
4

📌 List bilan:

mevalar = ["olma", "banan", "anor"]

for meva in mevalar:
    print(meva)

Natija:

olma
banan
anor

📌 String bilan ham ishlaydi:

for harf in "Python":
    print(harf)

Har bir harf alohida chiqariladi.

💡 for — takroriy vazifalarda juda ko‘p ishlatiladi.
""",

13: """
🔢 13-DARS — range()

range() sonlar ketma-ketligini yaratadi.

📌 range(5):

0
1
2
3
4

5 ning o‘zi kirmaydi.

📌 Boshlanish va tugash:

range(1, 6)

Natija:

1
2
3
4
5

📌 Qadam:

range(0, 10, 2)

Natija:

0
2
4
6
8

Bu yerda 2 — qadam.

Misol:

for i in range(1, 11):
    print(i)

Bu kod 1 dan 10 gacha chiqaradi.
""",

14: """
📋 14-DARS — LISTLAR

List — bir nechta qiymatni bitta o‘zgaruvchida saqlash usuli.

Misol:

mevalar = ["olma", "banan", "anor"]

List indekslari 0 dan boshlanadi.

mevalar[0] → olma
mevalar[1] → banan
mevalar[2] → anor

📌 Elementni o‘zgartirish:

mevalar[0] = "uzum"

📌 List uzunligi:

len(mevalar)

📌 Element qo‘shish:

mevalar.append("shaftoli")

📌 for bilan:

for meva in mevalar:
    print(meva)

💡 List Python'dagi eng muhim ma'lumot tuzilmalaridan biridir.
""",

15: """
🛠 15-DARS — LIST METODLARI

List bilan ishlashda ko‘plab metodlar mavjud.

append() → oxiriga qo‘shadi

sonlar = [1, 2, 3]
sonlar.append(4)

Natija:

[1, 2, 3, 4]

remove() → qiymatni o‘chiradi

sonlar.remove(2)

pop() → elementni olib tashlaydi

sonlar.pop()

sort() → tartiblaydi

sonlar.sort()

reverse() → teskari qiladi

sonlar.reverse()

len() → elementlar sonini beradi

len(sonlar)

📌 Misol:

sonlar = [5, 2, 8, 1]

sonlar.sort()

print(sonlar)

Natija:

[1, 2, 5, 8]
""",

16: """
📦 16-DARS — TUPLE

Tuple listga o‘xshaydi, lekin asosiy farqi:

Tuple elementlarini keyinchalik o‘zgartirib bo‘lmaydi.

Misol:

ranglar = ("qizil", "yashil", "ko‘k")

Element olish:

print(ranglar[0])

Natija:

qizil

Tuple:

()
qavslaridan foydalanadi.

📌 List:

mevalar = ["olma", "banan"]

📌 Tuple:

mevalar = ("olma", "banan")

💡 O‘zgarmas ma'lumotlarni saqlash kerak bo‘lsa Tuple foydali.
""",

17: """
🧩 17-DARS — SET

Set — takrorlanmaydigan qiymatlar to‘plami.

Misol:

sonlar = {1, 2, 3, 3, 4}

Natijada:

{1, 2, 3, 4}

Takroriy 3 faqat bir marta saqlanadi.

📌 Element qo‘shish:

sonlar.add(5)

📌 O‘chirish:

sonlar.remove(2)

📌 Set yaratish:

mevalar = {"olma", "anor", "banan"}

💡 Set takroriy ma'lumotlarni olib tashlash uchun juda foydali.
""",

18: """
📚 18-DARS — DICTIONARY

Dictionary ma'lumotni key va value ko‘rinishida saqlaydi.

Misol:

odam = {
    "ism": "Asil",
    "yosh": 15,
    "shahar": "Toshkent"
}

Qiymat olish:

print(odam["ism"])

Natija:

Asil

📌 Qiymatni o‘zgartirish:

odam["yosh"] = 16

📌 Yangi qiymat:

odam["kasb"] = "Programmer"

📌 for:

for key, value in odam.items():
    print(key, value)

Dictionary real loyihalarda juda ko‘p ishlatiladi.
""",

19: """
🔤 19-DARS — STRING

String — matn.

Misol:

ism = "Asilbek"

String indekslari 0 dan boshlanadi.

ism[0]

birinchi belgini beradi.

📌 Uzunligi:

len(ism)

📌 Birlashtirish:

ism = "Asil"
familiya = "Oktamov"

print(ism + " " + familiya)

📌 Stringni for bilan aylanish:

for harf in "Python":
    print(harf)

Stringlar Telegram botlar, web dasturlar va boshqa loyihalarda juda ko‘p ishlatiladi.
""",

20: """
🔤 20-DARS — STRING METODLARI

String bilan ishlash uchun ko‘plab metodlar mavjud.

upper():

ism = "asil"

print(ism.upper())

Natija:

ASIL

lower():

ism = "ASil"

print(ism.lower())

Natija:

asil

replace():

matn = "Men Java bilaman"

matn = matn.replace("Java", "Python")

strip():

matn = " Salom "

print(matn.strip())

💡 String metodlari matnlarni tozalash va o‘zgartirishda juda foydali.
""",

21: """
⚙️ 21-DARS — FUNKSIYALAR

Funksiya — ma'lum vazifani bajaruvchi qayta ishlatiladigan kod blokidir.

Funksiya yaratish:

def salom():
    print("Salom!")

Funksiyani chaqirish:

salom()

📌 Parametr bilan:

def salom(ism):
    print("Salom", ism)

salom("Asil")

Natija:

Salom Asil

Funksiyalar kodni tartibli va qayta ishlatiladigan qiladi.

💡 Katta dasturlarda funksiyalarsiz kod yozish juda qiyinlashadi.
""",

22: """
↩️ 22-DARS — return

return funksiya natijasini qaytaradi.

Misol:

def qosh(a, b):
    return a + b

natija = qosh(5, 3)

print(natija)

Natija:

8

📌 return va print bir xil emas.

print() → ekranga chiqaradi.

return → qiymatni qaytaradi.

Misol:

def kvadrat(x):
    return x * x

print(kvadrat(5))

Natija:

25

return funksiyalardan natijani boshqa joyda ishlatishga imkon beradi.
""",

23: """
📥 23-DARS — PARAMETRLAR

Parametr — funksiyaga ma'lumot uzatish uchun ishlatiladi.

Misol:

def salom(ism):
    print("Salom", ism)

salom("Ali")

Bu yerda:

ism → parametr
"Ali" → argument

Bir nechta parametr:

def qosh(a, b):
    print(a + b)

qosh(5, 7)

Natija:

12

Parametrlar funksiyalarni moslashuvchan qiladi.

Masalan bitta funksiyani turli qiymatlar bilan ishlatish mumkin.
""",

24: """
📦 24-DARS — MODULLAR

Modul — tayyor Python kodlari joylashgan fayl yoki kutubxona.

Masalan:

import math

print(math.sqrt(25))

Natija:

5.0

math moduli matematik amallar uchun ishlatiladi.

📌 random:

import random

son = random.randint(1, 10)

print(son)

Bu 1 dan 10 gacha tasodifiy son beradi.

📌 Modulning foydasi:

• Tayyor funksiyalardan foydalanamiz.
• Kodni qayta yozish shart emas.
• Katta loyihalarni qismlarga bo‘lish mumkin.
""",

25: """
⚠️ 25-DARS — TRY / EXCEPT

Dastur ishlayotgan vaqtda xatolar yuz berishi mumkin.

Masalan:

son = int(input("Son: "))

Agar foydalanuvchi "salom" yozsa, xato chiqadi.

try/except yordamida buni boshqarish mumkin:

try:
    son = int(input("Son: "))
except:
    print("Iltimos, son kiriting!")

📌 try → xato bo‘lishi mumkin bo‘lgan kod.

📌 except → xato yuz berganda ishlaydi.

Bu foydalanuvchi xatolari sabab dastur butunlay to‘xtab qolishining oldini olishga yordam beradi.
""",

26: """
📁 26-DARS — FAYLLAR BILAN ISHLASH

Python fayllarni o‘qishi va yozishi mumkin.

Fayl ochish:

f = open("test.txt", "w")

"w" → yozish

Faylga yozish:

f.write("Salom Python!")

Faylni yopish:

f.close()

📌 O‘qish:

f = open("test.txt", "r")

matn = f.read()

print(matn)

f.close()

Asosiy rejimlar:

r → o‘qish
w → yozish
a → oxiriga qo‘shish

💡 Fayllar ma'lumotlarni saqlash uchun foydali.
""",

27: """
🏗 27-DARS — CLASS

Class — obyektlar yaratish uchun qolip.

Misol:

class Odam:
    def __init__(self, ism):
        self.ism = ism

Bu yerda:

class → class yaratadi.

__init__ → obyekt yaratilganda ishlaydi.

self → obyektning o‘zini bildiradi.

Misol:

class Odam:
    def __init__(self, ism):
        self.ism = ism

odam = Odam("Ali")

print(odam.ism)

Natija:

Ali

Class katta dasturlarda kodni tartibli qilishga yordam beradi.
""",

28: """
👤 28-DARS — OBYEKTLAR

Obyekt — class asosida yaratilgan alohida nusxa.

Misol:

class Odam:
    def __init__(self, ism):
        self.ism = ism

odam1 = Odam("Ali")
odam2 = Odam("Vali")

print(odam1.ism)
print(odam2.ism)

Natija:

Ali
Vali

Bir class asosida juda ko‘p obyekt yaratish mumkin.

Class — qolip.

Obyekt — shu qolip asosida yaratilgan narsa.

Bu tushuncha OOP — Object Oriented Programming asoslaridan biridir.
""",

29: """
🚀 29-DARS — MINI LOYIHA

Endi o‘rgangan bilimlarimizni amalda ishlatamiz.

Mini loyiha sifatida:

1. Kalkulyator
2. Son topish o‘yini
3. Quiz
4. Login tizimi
5. Oddiy Telegram bot

yaratish mumkin.

Masalan, oddiy kalkulyator:

a = int(input("Birinchi son: "))
b = int(input("Ikkinchi son: "))

amal = input("Amal (+ yoki -): ")

if amal == "+":
    print(a + b)

elif amal == "-":
    print(a - b)

Bu loyihada:

• input()
• int()
• o‘zgaruvchi
• if
• elif
• print()

ishlatildi.

Demak, kichik loyihalar orqali bilimni mustahkamlash mumkin.
""",

30: """
🏆 30-DARS — YAKUNIY LOYIHA

Tabriklayman!

Siz Python kursining yakuniy bosqichiga yetib keldingiz.

Bu kursda:

✅ print()
✅ input()
✅ o‘zgaruvchilar
✅ ma'lumot turlari
✅ matematik operatorlar
✅ if / else
✅ elif
✅ mantiqiy operatorlar
✅ while
✅ for
✅ range()
✅ list
✅ tuple
✅ set
✅ dictionary
✅ string
✅ funksiyalar
✅ return
✅ parametrlar
✅ modullar
✅ try/except
✅ fayllar
✅ class
✅ obyektlar

bilan tanishdingiz.

🎯 ENDIGI MAQSAD:

Faqat kodni o‘qib qolmasdan, o‘zingiz mustaqil loyiha yaratish.

Masalan:

🤖 Telegram bot
🎮 Oddiy o‘yin
🧮 Kalkulyator
📝 Quiz dasturi
🌐 Web loyiha
🤖 AI loyiha

Eng muhimi:

KODNI KO‘P YOZING!

Xato qilish — dasturlashni o‘rganishning bir qismi.

🔥 Sizning keyingi bosqichingiz — REAL LOYIHA YARATISH!
"""
}


# =========================================================
# TESTLAR — HAR DARS 2 TA
# =========================================================

QUESTIONS = {
    1: [
        ("Python nima?", ["dasturlash tili", "programming language"],
         "Python — dasturlash tili.",
         'print("Hello")'),

        ("Python yordamida nima yaratish mumkin?", ["dastur", "bot", "web", "ai"],
         "Python dasturlar, botlar, web loyihalar va AI yaratishda ishlatiladi.",
         'print("Salom")')
    ],

    2: [
        ("Ekranga ma'lumot chiqarish uchun qaysi funksiya ishlatiladi?", ["print"],
         "print() ma'lumotni ekranga chiqaradi.",
         'print("Salom")'),

        ("print() nima qiladi?", ["ekranga", "chiqar"],
         "print() qiymatni ekranga chiqaradi.",
         'print(10)')
    ],

    3: [
        ("O‘zgaruvchi nima uchun kerak?", ["saqlash", "ma'lumot"],
         "O‘zgaruvchi ma'lumotni saqlash uchun ishlatiladi.",
         'ism = "Ali"'),

        ("Qaysi biri o‘zgaruvchi yaratadi?", ["x = 10", "x=10"],
         "x = 10 x nomli o‘zgaruvchi yaratadi.",
         'x = 10')
    ],

    4: [
        ("Butun sonning turi nima?", ["int"],
         "Butun son Python'da int turiga kiradi.",
         'x = 10'),

        ("Matnning turi nima?", ["str", "string"],
         "Matn Python'da str turiga kiradi.",
         'ism = "Ali"')
    ],

    5: [
        ("Foydalanuvchidan ma'lumot olish uchun nima ishlatiladi?", ["input"],
         "input() foydalanuvchidan ma'lumot oladi.",
         'input("Ism: ")'),

        ("input() odatda qanday ma'lumot qaytaradi?", ["str", "string"],
         "input() odatda string qaytaradi.",
         'ism = input()')
    ],

    6: [
        ("Ko‘paytirish operatori qaysi?", ["*"],
         "* ko‘paytirish operatori.",
         '5 * 3'),

        ("Qoldiq olish operatori qaysi?", ["%"],
         "% qoldiqni beradi.",
         '10 % 3')
    ],

    7: [
        ("Shart tekshirish uchun nima ishlatiladi?", ["if"],
         "if shart tekshiradi.",
         'if x > 5:'),

        ("if bajarilmasa qaysi blok ishlaydi?", ["else"],
         "else boshqa holatni bajaradi.",
         'else:')
    ],

    8: [
        ("Qo‘shimcha shart uchun nima ishlatiladi?", ["elif"],
         "elif qo‘shimcha shartni tekshiradi.",
         'elif x > 5:'),

        ("elif nimani anglatadi?", ["else if"],
         "elif — else if ma'nosida.",
         'elif x == 5:')
    ],

    9: [
        ("Tenglikni tekshirish operatori?", ["=="],
         "== tenglikni tekshiradi.",
         'x == 5'),

        ("Katta operatori?", [">"],
         "> katta ekanini tekshiradi.",
         '10 > 5')
    ],

    10: [
        ("Mantiqiy 'va' operatori?", ["and"],
         "and ikkala shart True bo‘lishini talab qiladi.",
         'x > 0 and x < 10'),

        ("Mantiqiy 'yoki' operatori?", ["or"],
         "or shartlardan bittasi True bo‘lsa yetarli.",
         'x == 1 or x == 2')
    ],

    11: [
        ("Shart rost bo‘lguncha ishlaydigan sikl?", ["while"],
         "while shart True bo‘lganida takrorlanadi.",
         'while x < 5:'),

        ("while nimani takrorlaydi?", ["kod", "amallar", "kodni"],
         "while kod blokini takrorlaydi.",
         'while x < 5:')
    ],

    12: [
        ("Takrorlash uchun ishlatiladigan sikl?", ["for"],
         "for takrorlash uchun ishlatiladi.",
         'for i in range(5):'),

        ("for nima uchun kerak?", ["takror", "takrorlash"],
         "for takroriy vazifalarni bajaradi.",
         'for i in range(3):')
    ],

    13: [
        ("range(5) oxirgi qaysi sonni beradi?", ["4"],
         "range(5) 0 dan 4 gacha boradi.",
         'range(5)'),

        ("range() nima yaratadi?", ["ketma-ketlik", "sonlar"],
         "range() sonlar ketma-ketligini yaratadi.",
         'range(1, 6)')
    ],

    14: [
        ("List indeksi nechadan boshlanadi?", ["0"],
         "List indeksi 0 dan boshlanadi.",
         'mevalar[0]'),

        ("List qaysi qavsdan foydalanadi?", ["[]"],
         "List [] bilan yoziladi.",
         'x = [1, 2, 3]')
    ],

    15: [
        ("List oxiriga element qo‘shish metodi?", ["append"],
         "append() elementni oxiriga qo‘shadi.",
         'x.append(5)'),

        ("Listni tartiblash metodi?", ["sort"],
         "sort() listni tartiblaydi.",
         'x.sort()')
    ],

    16: [
        ("Tuple o‘zgartiriladimi?", ["yo'q", "yoq"],
         "Tuple elementlarini o‘zgartirib bo‘lmaydi.",
         'x = (1, 2)'),

        ("Tuple qaysi qavs bilan yoziladi?", ["()"],
         "Tuple () bilan yoziladi.",
         'x = (1, 2)')
    ],

    17: [
        ("Set takroriy qiymatlarni saqlaydimi?", ["yo'q", "yoq"],
         "Set takroriy qiymatlarni saqlamaydi.",
         'x = {1, 2, 3}'),

        ("Set qanday qiymatlarni saqlaydi?", ["takrorlanmaydigan", "unique"],
         "Set unique qiymatlarni saqlaydi.",
         'x = {1, 2, 3}')
    ],

    18: [
        ("Dictionary qanday shaklda saqlaydi?", ["key value", "kalit qiymat", "key:value"],
         "Dictionary key:value shaklida ishlaydi.",
         '{"ism": "Ali"}'),

        ("Dictionary qaysi qavs bilan yoziladi?", ["{}"],
         "Dictionary {} bilan yoziladi.",
         'x = {"ism": "Ali"}')
    ],

    19: [
        ("String nima?", ["matn", "str"],
         "String — matn.",
         'ism = "Ali"'),

        ("String indeksi nechadan boshlanadi?", ["0"],
         "String indeksi 0 dan boshlanadi.",
         'ism[0]')
    ],

    20: [
        ("Matnni katta harfga aylantiruvchi metod?", ["upper"],
         "upper() katta harfga o‘tkazadi.",
         '"ali".upper()'),

        ("Matnni kichik harfga aylantiruvchi metod?", ["lower"],
         "lower() kichik harfga o‘tkazadi.",
         '"ALI".lower()')
    ],

    21: [
        ("Funksiya yaratish kalit so‘zi?", ["def"],
         "def funksiya yaratadi.",
         'def salom():'),

        ("Funksiya nima?", ["kod", "kod bloki"],
         "Funksiya qayta ishlatiladigan kod blokidir.",
         'def salom():')
    ],

    22: [
        ("Funksiya natijasini qaytarish uchun nima ishlatiladi?", ["return"],
         "return natijani qaytaradi.",
         'return a + b'),

        ("return nima qiladi?", ["qaytar", "natija"],
         "return qiymatni qaytaradi.",
         'return 10')
    ],

    23: [
        ("Funksiyaga ma'lumot uzatish nima deyiladi?", ["parametr", "parameter"],
         "Parametr funksiya ichiga ma'lumot uzatadi.",
         'def salom(ism):'),

        ("def salom(ism) dagi ism nima?", ["ism", "parametr"],
         "ism — parametr.",
         'def salom(ism):')
    ],

    24: [
        ("Modulni ulash uchun nima ishlatiladi?", ["import"],
         "import modulni ulaydi.",
         'import math'),

        ("Matematik modul nomi?", ["math"],
         "math matematik funksiyalar uchun ishlatiladi.",
         'import math')
    ],

    25: [
        ("Xatoni boshqarish uchun nima ishlatiladi?", ["try", "except", "try except"],
         "try/except xatolarni boshqaradi.",
         'try:\n    x = int("a")\nexcept:\n    print("Xato")'),

        ("Xato yuz berganda qaysi blok ishlaydi?", ["except"],
         "except xato paytida ishlaydi.",
         'except:')
    ],

    26: [
        ("Fayl ochish funksiyasi?", ["open"],
         "open() fayl ochadi.",
         'open("test.txt", "r")'),

        ("Faylga yozish metodi?", ["write"],
         "write() faylga yozadi.",
         'f.write("Salom")')
    ],

    27: [
        ("Class yaratish kalit so‘zi?", ["class"],
         "class yangi class yaratadi.",
         'class Odam:'),

        ("Class nima uchun kerak?", ["obyekt", "object"],
         "Class obyektlar uchun qolipdir.",
         'class Odam:')
    ],

    28: [
        ("Class asosida yaratilgan narsa?", ["obyekt", "object"],
         "Class asosida obyekt yaratiladi.",
         'odam = Odam()'),

        ("Odam() nima yaratadi?", ["obyekt", "object"],
         "Odam() obyekt yaratadi.",
         'odam = Odam()')
    ],

    29: [
        ("Mini loyiha nima?", ["loyiha", "dastur", "project"],
         "Mini loyiha bilimlarni amalda qo‘llashdir.",
         'print("Loyiha")'),

        ("Kalkulyator Python loyihasi bo‘la oladimi?", ["ha"],
         "Ha, kalkulyator oddiy Python loyihasi.",
         'a + b')
    ],

    30: [
        ("Python kursida nechta dars bor?", ["30", "30 ta"],
         "Kurs 30 ta darsdan iborat.",
         'print("Python")'),

        ("Kursdan keyingi eng yaxshi qadam nima?", ["loyiha", "project", "amaliyot"],
         "O‘rgangan bilimlarni loyiha orqali amalda ishlatish kerak.",
         'def main():')
    ]
}


# =========================================================
# FOYDALANUVCHI HOLATI
# =========================================================

users = {}


def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "lesson": 1,
            "question": 0,
            "score": 0,
            "completed": set()
        }

    return users[user_id]


# =========================================================
# KLAVIATURALAR
# =========================================================

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🐍 Python")],
            [KeyboardButton(text="💻 C++")],
            [KeyboardButton(text="📊 Progress")]
        ],
        resize_keyboard=True
    )


def python_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Darslar")],
            [KeyboardButton(text="▶️ Davom etish")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )


def lessons_keyboard():
    rows = []

    for i in range(1, 31, 3):
        row = []

        for j in range(i, min(i + 3, 31)):
            row.append(
                KeyboardButton(text=f"{j}-dars")
            )

        rows.append(row)

    rows.append([KeyboardButton(text="🔙 Orqaga")])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True
    )


# =========================================================
# AI — FAQAT QO‘SHIMCHA TUSHUNTIRISH
# =========================================================

async def ask_ai_lesson(lesson_number):
    if not ai:
        return None

    title = PYTHON_LESSONS[lesson_number - 1]

    prompt = f"""
Sen Python o‘qituvchisisan.

Mavzu: {title}

O‘zbek tilida juda tushunarli qo‘shimcha tushuntirish ber.
Asosiy tushuncha, sintaksis va 1-2 ta kod misolini ko‘rsat.
150 so‘zdan oshmasin.
"""

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                ai.models.generate_content,
                model="gemini-3.8-flash",
                contents=prompt
            ),
            timeout=6
        )

        if response and response.text:
            return response.text

    except Exception:
        return None

    return None


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):
    get_user(message.from_user.id)

    await message.answer(
        "🚀 CODE MASTER ga xush kelibsiz!\n\n"
        "🐍 Python — 30 ta batafsil dars\n"
        "📝 Har dars — 2 ta test\n"
        "🤖 AI o‘qituvchi\n"
        "📊 Progress tizimi\n"
        "⚡ Tezkor test tekshiruvi\n\n"
        "Boshlash uchun Python'ni tanlang.",
        reply_markup=main_keyboard()
    )


# =========================================================
# PYTHON MENU
# =========================================================

@dp.message(F.text == "🐍 Python")
async def python_menu(message: Message):
    await message.answer(
        "🐍 PYTHON KURSI\n\n"
        "Bu kurs 30 ta darsdan iborat.\n\n"
        "Har darsda:\n"
        "📖 Batafsil tushuntirish\n"
        "💻 Kod misollari\n"
        "📝 2 ta test\n"
        "❌ Xato javobga izoh\n"
        "📊 Natija\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=python_keyboard()
    )


# =========================================================
# DARSLAR
# =========================================================

@dp.message(F.text == "📚 Darslar")
async def lessons(message: Message):
    await message.answer(
        "📚 PYTHON DARSLARI\n\n"
        "🔓 Darslar ketma-ket ochiladi.\n"
        "Darsni tanlang:",
        reply_markup=lessons_keyboard()
    )


# =========================================================
# DAVOM ETISH
# =========================================================

@dp.message(F.text == "▶️ Davom etish")
async def continue_lesson(message: Message):
    user = get_user(message.from_user.id)

    if user["lesson"] > 30:
        await message.answer(
            "🏆 Siz barcha 30 ta darsni tugatgansiz!",
            reply_markup=python_keyboard()
        )
        return

    await start_lesson(message, user["lesson"])


# =========================================================
# DARSNI BOSHLASH
# =========================================================

async def start_lesson(message: Message, lesson_number: int):
    user = get_user(message.from_user.id)

    user["lesson"] = lesson_number
    user["question"] = 0
    user["score"] = 0

    title = PYTHON_LESSONS[lesson_number - 1]

    await message.answer(
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📖 {lesson_number}-DARS\n"
        f"📌 {title}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"{LESSON_TEXTS[lesson_number]}"
    )

    ai_text = await ask_ai_lesson(lesson_number)

    if ai_text:
        await message.answer(
            "🤖 AI O‘QITUVCHINING QO‘SHIMCHA IZOHİ:\n\n"
            + ai_text
        )

    await send_question(message, lesson_number, 1)


# =========================================================
# TEST SAVOLI
# =========================================================

async def send_question(message: Message, lesson_number: int, question_number: int):
    user = get_user(message.from_user.id)

    question, accepted, explanation, example = QUESTIONS[
        lesson_number
    ][question_number - 1]

    user["question"] = question_number

    await message.answer(
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 TEST {question_number}/2\n"
        f"📚 {lesson_number}-dars\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"❓ {question}\n\n"
        "✍️ Javobingizni yozing:"
    )


# =========================================================
# JAVOBNI TEKSHIRISH
# =========================================================

def check_local_answer(user_answer, accepted_answers):
    answer = user_answer.lower().strip()

    for correct in accepted_answers:
        correct = correct.lower().strip()

        if answer == correct:
            return True

        if len(correct) >= 4 and correct in answer:
            return True

    return False


# =========================================================
# BARCHA XABARLAR
# =========================================================

@dp.message()
async def handle_message(message: Message):

    text = message.text

    if text == "💻 C++":
        await cpp(message)
        return

    if text == "📊 Progress":
        await progress(message)
        return

    if text == "🔙 Orqaga":
        await back(message)
        return

    if text == "📚 Darslar":
        await lessons(message)
        return

    if text == "▶️ Davom etish":
        await continue_lesson(message)
        return

    if text == "🐍 Python":
        await python_menu(message)
        return

    if text.endswith("-dars"):
        try:
            number = int(text.replace("-dars", ""))

            if 1 <= number <= 30:
                await choose_lesson(message, number)
                return

        except ValueError:
            pass

    user = get_user(message.from_user.id)

    lesson_number = user["lesson"]
    question_number = user["question"]

    if question_number == 0:
        await message.answer(
            "📚 Avval darsni boshlang.\n\n"
            "▶️ Davom etish tugmasini bosing."
        )
        return

    question, accepted, explanation, example = QUESTIONS[
        lesson_number
    ][question_number - 1]

    correct = check_local_answer(
        text,
        accepted
    )

    if correct:

        user["score"] += 1

        await message.answer(
            "━━━━━━━━━━━━━━━━━━\n"
            "✅ TO‘G‘RI!\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👏 Juda yaxshi!"
        )

    else:

        correct_answer = accepted[0]

        await message.answer(
            "━━━━━━━━━━━━━━━━━━\n"
            "❌ NOTO‘G‘RI!\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ To‘g‘ri javob: {correct_answer}\n\n"
            f"📖 TUSHUNTIRISH:\n"
            f"{explanation}\n\n"
            f"💡 MISOL:\n"
            f"{example}"
        )

    if question_number == 1:

        await send_question(
            message,
            lesson_number,
            2
        )

        return

    score = user["score"]

    user["completed"].add(
        lesson_number
    )

    if lesson_number < 30:
        user["lesson"] = lesson_number + 1

    else:
        user["lesson"] = 31

    user["question"] = 0

    result_text = ""

    if score == 2:
        result_text = "🔥 Mukammal! 2/2!"
    elif score == 1:
        result_text = "👍 Yaxshi! 1/2."
    else:
        result_text = "💪 Xafa bo‘lmang. Xatolardan o‘rganamiz."

    await message.answer(
        "━━━━━━━━━━━━━━━━━━\n"
        f"🎉 {lesson_number}-DARS TUGADI!\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Natija: {score}/2\n\n"
        f"{result_text}\n\n"
        + (
            f"➡️ Keyingi dars: {lesson_number + 1}"
            if lesson_number < 30
            else "🏆 Barcha darslar tugadi!"
        ),
        reply_markup=python_keyboard()
    )


# =========================================================
# DARS TANLASH
# =========================================================

async def choose_lesson(message: Message, number: int):
    user = get_user(message.from_user.id)

    if number > 1 and number - 1 not in user["completed"]:

        await message.answer(
            f"🔒 {number}-DARS YOPIQ!\n\n"
            f"Avval {number - 1}-darsni tugating."
        )

        return

    await start_lesson(
        message,
        number
    )


# =========================================================
# PROGRESS
# =========================================================

async def progress(message: Message):
    user = get_user(message.from_user.id)

    completed = len(
        user["completed"]
    )

    percent = int(
        completed / 30 * 100
    )

    await message.answer(
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 SIZNING PROGRESSINGIZ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ Tugatilgan: {completed}/30\n"
        f"📈 Progress: {percent}%\n"
        f"📚 Keyingi dars: "
        f"{user['lesson'] if user['lesson'] <= 30 else 'TUGAGAN'}"
    )


# =========================================================
# C++
# =========================================================

async def cpp(message: Message):
    await message.answer(
        "💻 C++ KURSI\n\n"
        "C++ kursi hozircha ishlab chiqilmoqda.\n\n"
        "🚧 Tez orada qo‘shiladi."
    )


# =========================================================
# ORQAGA
# =========================================================

async def back(message: Message):
    await message.answer(
        "🏠 ASOSIY MENYU",
        reply_markup=main_keyboard()
    )


# =========================================================
# BOTNI ISHGA TUSHIRISH
# =========================================================

async def main():

    bot = Bot(
        token=BOT_TOKEN
    )

    print("🚀 CODE MASTER ishga tushdi!")
    print("📚 30 ta batafsil Python darsi tayyor.")
    print("⚡ Tezkor test rejimi yoqilgan.")

    try:

        await dp.start_polling(
            bot,
            polling_timeout=30
        )

    finally:

        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

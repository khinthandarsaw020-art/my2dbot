import os
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import pytz
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread

# ==========================================
# (၁) Render အတွက် Dummy Web Server တည်ဆောက်ခြင်း
# ==========================================
app = Flask(__name__)
@app.route('/')
def home():
    return "2D Prediction Bot is Running 24/7!"

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# (၂) AI Model တည်ဆောက်ခြင်း (Server တက်သည်နှင့် အလိုအလျောက် Train မည်)
# ==========================================
def train_model():
    print("Training Model...")
    ticker = yf.Ticker('^SET.BK')
    df = ticker.history(period='60d', interval='5m')
    
    if df.empty:
        return None

    df['Change'] = df['Close'] - df['Close'].shift(1)
    df = df.dropna()
    df['Head'] = df['Close'].apply(lambda x: f"{abs(float(x)):.2f}"[-1])
    
    df['RSI_14'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
    df['MACD_Diff'] = ta.trend.MACD(close=df['Close']).macd_diff()
    df['BB_Width'] = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2).bollinger_wband()
    df['Lag_1_Head'] = df['Head'].shift(1)
    df['Lag_2_Head'] = df['Head'].shift(2)
    
    df = df.dropna()
    X = df[['RSI_14', 'MACD_Diff', 'BB_Width', 'Lag_1_Head', 'Lag_2_Head']]
    y = df['Head'].astype(str)
    
    model = RandomForestClassifier(n_estimators=150, random_state=42, max_depth=7)
    model.fit(X, y)
    return model

global_model = None

# ==========================================
# (၃) Telegram Bot Commands များ
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ! ⚡ Real-Time 2D Prediction Bot အသင့်ဖြစ်ပါပြီ။ /predict ဟု ရိုက်ပါ။")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if global_model is None:
        await update.message.reply_text("⚠️ Model အသင့်မဖြစ်သေးပါ။")
        return

    await update.message.reply_text("🔄 Live Data တွက်ချက်နေပါသည်...")
    
    try:
        live_ticker = yf.Ticker('^SET.BK')
        live_df = live_ticker.history(period='5d', interval='5m')
        
        live_df['Change'] = live_df['Close'] - live_df['Close'].shift(1)
        live_df = live_df.dropna()
        live_df['Head'] = live_df['Close'].apply(lambda x: f"{abs(float(x)):.2f}"[-1])
        
        live_df['RSI_14'] = ta.momentum.RSIIndicator(close=live_df['Close'], window=14).rsi()
        live_df['MACD_Diff'] = ta.trend.MACD(close=live_df['Close']).macd_diff()
        live_df['BB_Width'] = ta.volatility.BollingerBands(close=live_df['Close'], window=20, window_dev=2).bollinger_wband()
        live_df['Lag_1_Head'] = live_df['Head'].shift(1)
        live_df['Lag_2_Head'] = live_df['Head'].shift(2)
        live_df = live_df.dropna()
        
        latest_features = live_df[['RSI_14', 'MACD_Diff', 'BB_Width', 'Lag_1_Head', 'Lag_2_Head']].iloc[-1:]
        
        probabilities = global_model.predict_proba(latest_features)[0]
        classes = global_model.classes_
        top_2_indices = np.argsort(probabilities)[::-1][:2]
        
        tz = pytz.timezone('Asia/Yangon')
        current_time = datetime.now(tz).strftime("%I:%M %p")
        
        reply_text = (
            f"⚡ **Real-Time ခန့်မှန်းချက်** ⚡\n"
            f"🕒 အချိန်: {current_time}\n\n"
            f"🥇 **အကောင်းဆုံး ထိပ်စီး:** [ {classes[top_2_indices[0]]} ] (Win: {probabilities[top_2_indices[0]]*100:.1f}%)\n"
            f"🥈 **အရံ ထိပ်စီး:** [ {classes[top_2_indices[1]]} ] (Win: {probabilities[top_2_indices[1]]*100:.1f}%)"
        )
        await update.message.reply_text(reply_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text("⚠️ ဒေတာဆွဲယူ၍ မရပါ။ စျေးကွက်ပိတ်နေခြင်း ဖြစ်နိုင်ပါသည်။")

# ==========================================
# (၄) Server နှင့် Bot ကို တစ်ပြိုင်နက်တည်း Run ခြင်း
# ==========================================
if __name__ == '__main__':
    # ၁။ Model ကို အရင် Train မည်
    global_model = train_model()
    
    # ၂။ Web Server ကို နောက်ကွယ် (Thread) ဖြင့် ဖွင့်မည်
    t = Thread(target=run_http_server)
    t.start()
    
    # ၃။ Bot ကို ဖွင့်မည်
    TOKEN = "8823632853:AAGyL901l62FnpXLUgto8XvDXZ0UBp1CFSA" # ဤနေရာတွင် သင့် Token ထည့်ပါ
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.run_polling()

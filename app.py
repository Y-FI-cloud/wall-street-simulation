import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import datetime
import random
import time

# --- ΡΥΘΜΙΣΕΙΣ ---
st.set_page_config(page_title="Wall Street RPG", page_icon="🗽", layout="wide")
SAVE_FILE = "stock_game_web_save.json"

# --- ΠΛΗΡΟΦΟΡΙΕΣ ETF (Εγκυκλοπαίδεια) ---
ETF_INFO = {
    "VOO": """
    **🔹 S&P 500 ETF (VOO)**
    * **Τι είναι:** Οι 500 μεγαλύτερες εταιρείες των ΗΠΑ. Ο "βασιλιάς" των δεικτών.
    * **Κλάδοι:** Τεχνολογία, Υγεία, Τράπεζες.
    * **Top Holdings:** Apple, Microsoft, NVIDIA, Amazon, Meta.
    * **Ρίσκο:** Μεσαίο (ακολουθεί την αγορά).
    """,
    "QQQ": """
    **🔹 Nasdaq 100 ETF (QQQ)**
    * **Τι είναι:** Οι 100 μεγαλύτερες non-financial εταιρείες. Πολύ heavy στην Τεχνολογία.
    * **Κλάδοι:** Tech (50%+), AI, Software.
    * **Top Holdings:** Apple, NVIDIA, Microsoft, Tesla.
    * **Ρίσκο:** Υψηλότερο από S&P 500, αλλά με μεγαλύτερα κέρδη στην άνοδο.
    """,
    "DIA": """
    **🔹 Dow Jones (DIA)**
    * **Τι είναι:** 30 ιστορικές "Blue Chip" βιομηχανίες και εταιρείες.
    * **Στυλ:** Πιο συντηρητικό, μερίσματα, σταθερότητα.
    """,
    "GLD": """
    **🔹 Gold (GLD)**
    * **Τι είναι:** Φυσικός Χρυσός.
    * **Χρήση:** Ασφάλεια σε κρίσεις και πληθωρισμό. Συνήθως ανεβαίνει όταν οι μετοχές πέφτουν.
    """,
    "SLV": """
    **🔹 Silver (SLV)**
    * **Τι είναι:** Ασήμι.
    * **Χρήση:** Πολύτιμο μέταλλο αλλά και βιομηχανικό υλικό (chips, panels). Πιο ευμετάβλητο από τον χρυσό.
    """
}

# --- ΔΕΔΟΜΕΝΑ ΑΓΟΡΑΣ ---
MARKET_DATA = {
    "🇺🇸 US Giants": {
        "Apple Inc. (AAPL)": "AAPL",
        "Microsoft Corp. (MSFT)": "MSFT",
        "NVIDIA Corp. (NVDA)": "NVDA",
        "Tesla Inc. (TSLA)": "TSLA",
        "Amazon.com (AMZN)": "AMZN",
        "Meta Platforms (META)": "META",
        "Alphabet/Google (GOOGL)": "GOOGL",
        "Netflix (NFLX)": "NFLX",
        "AMD (AMD)": "AMD",
        "Intel Corp. (INTC)": "INTC",
        "Coca-Cola (KO)": "KO",
        "PepsiCo (PEP)": "PEP",
        "McDonald's (MCD)": "MCD",
        "Walt Disney (DIS)": "DIS",
        "Visa Inc. (V)": "V",
        "Mastercard (MA)": "MA",
        "JPMorgan Chase (JPM)": "JPM",
        "Uber Technologies (UBER)": "UBER",
        "Palantir Tech (PLTR)": "PLTR",
        "Coinbase (COIN)": "COIN"
    },
    "₿ Cryptocurrencies": {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD",
        "XRP (XRP)": "XRP-USD",
        "Dogecoin (DOGE)": "DOGE-USD",
        "Cardano (ADA)": "ADA-USD",
        "Shiba Inu (SHIB)": "SHIB-USD",
        "Polkadot (DOT)": "DOT-USD",
        "Litecoin (LTC)": "LTC-USD",
        "Chainlink (LINK)": "LINK-USD"
    },
    "🌐 ETFs (US Market)": {
        "S&P 500 ETF (VOO)": "VOO",
        "Nasdaq 100 ETF (QQQ)": "QQQ",
        "Dow Jones ETF (DIA)": "DIA",
        "Gold Trust (GLD)": "GLD",
        "Silver Trust (SLV)": "SLV"
    }
}

# --- ΣΥΝΑΡΤΗΣΕΙΣ ---
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f: return json.load(f)
    return None

def save_data():
    data = {
        "wallet": st.session_state.wallet,
        "portfolio": st.session_state.portfolio,
        "history": st.session_state.history,
        "xp": st.session_state.xp,
        "level": st.session_state.level,
        "achievements": st.session_state.achievements,
        "bots": st.session_state.bots
    }
    with open(SAVE_FILE, "w") as f: json.dump(data, f)

def check_level_up():
    if st.session_state.xp >= st.session_state.level * 100:
        st.session_state.level += 1
        st.toast(f"🎉 LEVEL UP! Level {st.session_state.level}!", icon="🆙")

def unlock_achievement(name):
    if name not in st.session_state.achievements:
        st.session_state.achievements.append(name)
        st.toast(f"🏆 Unlocked: {name}", icon="🏆")

def get_crypto_symbol(sym):
    cryptos = ["BTC", "ETH", "DOGE", "SOL", "XRP", "ADA", "SHIB", "LTC", "DOT", "LINK"]
    sym = sym.upper().strip()
    if sym in cryptos: return f"{sym}-USD"
    return sym

# --- STATE ---
if 'initialized' not in st.session_state:
    d = load_data()
    if d:
        st.session_state.wallet = d['wallet']
        st.session_state.portfolio = d['portfolio']
        st.session_state.history = d['history']
        st.session_state.xp = d.get('xp', 0)
        st.session_state.level = d.get('level', 1)
        st.session_state.achievements = d.get('achievements', [])
        st.session_state.bots = d.get('bots', {"Warren B.": {"wealth": 12000, "risk": "low"}, "Elon M.": {"wealth": 9500, "risk": "high"}, "Ape 🚀": {"wealth": 5000, "risk": "crazy"}})
    else:
        st.session_state.wallet = 10000.0
        st.session_state.portfolio = {}
        st.session_state.history = []
        st.session_state.xp = 0
        st.session_state.level = 1
        st.session_state.achievements = []
        st.session_state.bots = {"Warren B.": {"wealth": 12000, "risk": "low"}, "Elon M.": {"wealth": 9500, "risk": "high"}, "Ape 🚀": {"wealth": 5000, "risk": "crazy"}}
    st.session_state.initialized = True

# --- SIDEBAR ---
st.sidebar.title(f"👤 Level {st.session_state.level}")
st.sidebar.progress(min((st.session_state.xp % 100)/100, 1.0))
st.sidebar.caption(f"XP: {st.session_state.xp} / {st.session_state.level*100}")
menu = st.sidebar.radio("Menu", ["🛒 Trade", "📉 Portfolio Manage", "📊 Dashboard", "🏆 Profile", "⚙️ Reset"])
st.sidebar.markdown("---")
st.sidebar.metric("💰 Cash", f"${st.session_state.wallet:,.2f}")

# --- MAIN ---

# 1. TRADE (BUY/SHORT)
if menu == "🛒 Trade":
    st.header("🛒 Trade Stocks & Crypto (USD)")
    
    tab1, tab2 = st.tabs(["🔥 Quick List", "🔎 Search Symbol"])
    symbol = None
    
    with tab1:
        category = st.selectbox("Market:", list(MARKET_DATA.keys()))
        display_name = st.selectbox("Asset:", list(MARKET_DATA[category].keys()))
        symbol = MARKET_DATA[category][display_name]
        
    with tab2:
        custom_input = st.text_input("Symbol (e.g. PLTR, COIN):").upper()
        if custom_input: symbol = get_crypto_symbol(custom_input)

    st.divider()

    if symbol:
        try:
            with st.spinner(f"Fetching data for {symbol}..."):
                # Εγκυκλοπαίδεια
                if symbol in ETF_INFO:
                    st.info(ETF_INFO[symbol])
                
                stock = yf.Ticker(symbol)
                hist = stock.history(period="5d") 
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    st.success(f"Asset: **{symbol}**")
                    st.metric("Price", f"${current_price:,.2f}")
                    st.line_chart(hist['Close'])

                    col_action, col_amount = st.columns(2)
                    with col_action:
                        action = st.radio("Action:", ["🟢 Long (Buy)", "🔴 Short (Sell/Bet Down)"])
                    with col_amount:
                        amount = st.number_input("Amount ($):", min_value=1.0)

                    if action == "🟢 Long (Buy)":
                        btn_txt = "💸 Buy (Long)"
                        btn_type = "primary"
                    else:
                        btn_txt = "📉 Short (Sell)"
                        btn_type = "secondary"

                    if st.button(btn_txt, type=btn_type):
                        if action == "🟢 Long (Buy)" and amount > st.session_state.wallet:
                            st.error("Insufficient funds!")
                        else:
                            shares = amount / current_price
                            
                            if action == "🔴 Short (Sell/Bet Down)":
                                shares = -shares
                                st.session_state.wallet += amount
                                st.toast("Short position opened!", icon="📉")
                            else:
                                st.session_state.wallet -= amount
                            
                            if symbol in st.session_state.portfolio:
                                st.session_state.portfolio[symbol]['shares'] += shares
                                st.session_state.portfolio[symbol]['buy_price'] = current_price 
                            else:
                                st.session_state.portfolio[symbol] = {'shares': shares, 'buy_price': current_price}
                            
                            st.session_state.xp += 10
                            check_level_up()
                            if abs(amount) > 2000: unlock_achievement("Big Spender")
                            if action.startswith("🔴"): unlock_achievement("Bear Market")
                            
                            save_data()
                            time.sleep(1)
                            st.rerun()
                else: st.error("No data found.")
        except Exception as e: # <--- ΕΔΩ ΕΓΙΝΕ Η ΔΙΟΡΘΩΣΗ (Exception)
             # Αγνοούμε το σφάλμα αν είναι απλή επανεκκίνηση (που δεν είναι σφάλμα!)
            if "script control" not in str(e).lower():
                st.error(f"Connection error or invalid symbol. Details: {e}")

# 2. MANAGE POSITIONS
elif menu == "📉 Portfolio Manage":
    st.header("📉 Manage Positions")
    if not st.session_state.portfolio: st.info("Portfolio is empty.")
    else:
        sym = st.selectbox("Select Position:", list(st.session_state.portfolio.keys()))
        
        stock = yf.Ticker(sym)
        hist = stock.history(period="5d")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            
            shares = st.session_state.portfolio[sym]['shares']
            entry_price = st.session_state.portfolio[sym]['buy_price']
            
            is_short = shares < 0
            position_type = "🔴 SHORT" if is_short else "🟢 LONG"
            shares_abs = abs(shares)
            
            close_cost = shares_abs * current_price
            
            if not is_short:
                profit_usd = close_cost - (shares_abs * entry_price)
                profit_pct = (current_price - entry_price) / entry_price * 100
                st.info(f"Type: **{position_type}** | Shares: {shares:.4f}")
                st.write(f"Current Value: **${close_cost:,.2f}**")
                btn_txt = "💰 Sell (Close)"
            else:
                profit_usd = (shares_abs * entry_price) - close_cost
                profit_pct = (entry_price - current_price) / entry_price * 100
                st.error(f"Type: **{position_type}** | Owed Shares: {shares_abs:.4f}")
                st.write(f"Cost to Cover: **${close_cost:,.2f}**")
                btn_txt = "🔄 Cover (Close)"

            color = "green" if profit_usd >= 0 else "red"
            st.markdown(f"P/L: :{color}[${profit_usd:,.2f} ({profit_pct:+.2f}%)]")
            
            pct_close = st.slider("Close Amount (%):", 0.0, 100.0, 100.0) / 100.0
            
            if st.button(btn_txt):
                if pct_close > 0:
                    shares_to_close = shares_abs * pct_close
                    cost_to_close = shares_to_close * current_price
                    
                    if not is_short:
                        st.session_state.wallet += cost_to_close
                        st.session_state.portfolio[sym]['shares'] -= shares_to_close
                    else:
                        st.session_state.wallet -= cost_to_close
                        st.session_state.portfolio[sym]['shares'] += shares_to_close

                    realized_profit = profit_usd * pct_close
                    if realized_profit > 0:
                        st.session_state.xp += 50
                        if realized_profit > 50: unlock_achievement("Shark")
                        st.toast(f"Profit ${realized_profit:.2f}!", icon="🤑")
                    else: st.session_state.xp += 5
                    
                    if abs(st.session_state.portfolio[sym]['shares']) < 0.0001:
                        del st.session_state.portfolio[sym]
                    
                    check_level_up()
                    save_data()
                    st.success("Order Executed!")
                    time.sleep(1)
                    st.rerun()
        else: st.warning("Loading price failed.")

# 3. DASHBOARD
elif menu == "📊 Dashboard":
    st.header("📊 Dashboard (USD)")
    total_wealth_calc = st.session_state.wallet
    items = []
    
    if st.session_state.portfolio:
        for s, d in st.session_state.portfolio.items():
            try:
                r_hist = yf.Ticker(s).history(period="5d")
                if not r_hist.empty:
                    p = r_hist['Close'].iloc[-1]
                    
                    shares = d['shares']
                    val = shares * p 
                    total_wealth_calc += val 
                    
                    type_pos = "🔴 SHORT" if shares < 0 else "🟢 LONG"
                    if shares > 0: 
                        prof = (p - d['buy_price']) / d['buy_price'] * 100
                    else: 
                        prof = (d['buy_price'] - p) / d['buy_price'] * 100

                    items.append({
                        "Type": type_pos, "Symbol": s, "Shares": f"{shares:.3f}", 
                        "Value/Debt": f"${val:,.2f}", "Return": f"{prof:+.2f}%"
                    })
            except: pass
            
    c1, c2 = st.columns(2)
    c1.metric("Net Worth", f"${total_wealth_calc:,.2f}")
    c2.metric("Cash Available", f"${st.session_state.wallet:,.2f}")
    
    current_time = datetime.datetime.now().strftime("%H:%M")
    if not st.session_state.history or st.session_state.history[-1]['value'] != total_wealth_calc:
        st.session_state.history.append({"time": current_time, "value": total_wealth_calc})
    
    st.markdown("---")
    if items: st.dataframe(pd.DataFrame(items))
    
    st.subheader("📈 Wealth Chart")
    if len(st.session_state.history) > 0:
        st.line_chart(pd.DataFrame(st.session_state.history), x="time", y="value")

    st.markdown("---")
    st.subheader("🏆 Leaderboard")
    lb = [{"Player": "😎 YOU", "Net Worth": total_wealth_calc}]
    for n, b in st.session_state.bots.items():
        b['wealth'] *= (1 + random.uniform(-0.02, 0.03))
        lb.append({"Player": n, "Net Worth": b['wealth']})
    lb.sort(key=lambda x: x['Net Worth'], reverse=True)
    st.table(pd.DataFrame(lb))
    save_data()

# 4/5. PROFILE & RESET
elif menu == "🏆 Profile":
    st.header("Profile")
    st.metric("Level", st.session_state.level)
    st.progress(min((st.session_state.xp % 100)/100, 1.0))
    for a in st.session_state.achievements: st.success(f"⭐ {a}")
elif menu == "⚙️ Reset":
    if st.button("❌ RESET GAME"):
        if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
        st.session_state.clear()
        st.rerun()
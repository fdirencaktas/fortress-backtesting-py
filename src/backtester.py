import pandas as pd
import pandas_ta as ta
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from backtesting import Strategy, Backtest
from backtesting.lib import crossover

# ─────────────────────────────────────────────
# 📊 CONFIGURATION
# ─────────────────────────────────────────────
TICKER = "SPY"
START_DATE = "2000-01-01"
INITIAL_CASH = 10_000
COMMISSION = 0.002
SHOW_DETAILED = True
SAVE_RESULTS_TO_CSV = False

# ─────────────────────────────────────────────
# 📥 DATA LOADING
# ─────────────────────────────────────────────
def download_data(ticker: str, start: str) -> pd.DataFrame:
    """Download historical OHLCV data from Yahoo Finance."""
    data = yf.download(ticker, start=start, progress=False, multi_level_index=False)
    data.dropna(inplace=True)
    return data

df = download_data(TICKER, START_DATE)

# ─────────────────────────────────────────────
# 📈 TECHNICAL INDICATORS
# ─────────────────────────────────────────────
def ema(values,n): 
    """Compute Exponential Moving Average (EMA).""" 
    return pd.DataFrame(values).ta.ema(length=n)

# ─────────────────────────────────────────────
# ⚙️ STRATEGY DEFINITIONS
# ─────────────────────────────────────────────
class EmaCross(Strategy):
    """Classic dual EMA crossover strategy."""
    n_fast = 50
    n_slow = 200

    def init(self):
        self.ema_fast = self.I(ema, self.data.Close, self.n_fast)
        self.ema_slow = self.I(ema, self.data.Close, self.n_slow)

    def next(self):
        if crossover(self.ema_fast, self.ema_slow):
            self.buy()
        elif crossover(self.ema_slow, self.ema_fast):
            self.position.close()


class PriceEmaCross(Strategy):
    """Price crossing a single EMA."""
    n_period = 50

    def init(self):
        self.ema = self.I(ema, self.data.Close, self.n_period)

    def next(self):
        if crossover(self.data.Close, self.ema):
            self.buy()
        elif crossover(self.ema, self.data.Close):
            self.position.close()

# ─────────────────────────────────────────────
# 🚀 BACKTESTING
# ─────────────────────────────────────────────
bt_ema_cross = Backtest(df, EmaCross, cash=INITIAL_CASH, commission=COMMISSION)
bt_price_ema_cross = Backtest(df, PriceEmaCross, cash=INITIAL_CASH, commission=COMMISSION)

stats_ema = bt_ema_cross.run()
stats_price_ema = bt_price_ema_cross.run()

# ─────────────────────────────────────────────
# 📉 EQUITY CURVE COMPARISON
# ─────────────────────────────────────────────
equity_df = pd.DataFrame({
    "EMA Crossover": stats_ema["_equity_curve"]["Equity"].values,
    "Price/EMA": stats_price_ema["_equity_curve"]["Equity"].values,
    "Benchmark": (df["Close"] / df["Close"].iloc[0]) * INITIAL_CASH,
}, index=df.index[-len(stats_ema["_equity_curve"]):])

plt.figure(figsize=(12, 6))
equity_df.plot(ax=plt.gca(), title=f"{TICKER} Strategy Comparison", linewidth=1.5)
plt.ylabel("Portfolio Value ($)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ─────────────────────────────────────────────
# 📊 PERFORMANCE SUMMARY
# ─────────────────────────────────────────────
def summarize_stats(name: str, stats: pd.Series):
    """Print key performance metrics from Backtesting.py results."""
    print(f"\n📈 {name} Strategy Results")
    print(f"Total Return: {stats['Return [%]']:.2f}%")
    print(f"CAGR: {stats['CAGR [%]']:.2f}%")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
    print(f"Sortino Ratio: {stats['Sortino Ratio']:.2f}")
    print(f"Calmar Ratio: {stats['Calmar Ratio']:.2f}")

summarize_stats("EMA Crossover", stats_ema)
summarize_stats("Price/EMA", stats_price_ema)

# ─────────────────────────────────────────────
# 🧭 OPTIONAL: DETAILED PLOTS
# ─────────────────────────────────────────────
if SHOW_DETAILED:
    print("\nGenerating detailed Backtesting.py plots...")
    bt_ema_cross.plot()
    bt_price_ema_cross.plot()

# ─────────────────────────────────────────────
# 💾 OPTIONAL: SAVE RESULTS
# ─────────────────────────────────────────────
if SAVE_RESULTS_TO_CSV:
    equity_df.to_csv("equity_curves.csv", index=True)
    print("✅ Equity curves saved to equity_curves.csv")

if __name__ == "__main__":
    pass

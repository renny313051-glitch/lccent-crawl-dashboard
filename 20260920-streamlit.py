import streamlit as st 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup
import jieba
from collections import Counter

# ---------------------------------------------------------
# 1. 頁面配置
# ---------------------------------------------------------
st.set_page_config(page_title="個股動態與社群焦點儀表板", layout="wide")
st.title("📊 個股價量走勢 ✕ PTT 輿情焦點互動監控")
st.caption("展示 Plotly 雙座標軸複合圖表、週末斷線修復與向量互動文字雲實戰")

# ---------------------------------------------------------
# 2. 準備模擬資料集 (含 OHLCV 與 Lesson 9 NLP 斷詞/情緒成果)
# ---------------------------------------------------------
# 建立 10 個交易日的價量與情緒資料
trade_dates = pd.date_range("2026-09-01", periods=14, freq="D")
trade_dates = trade_dates[trade_dates.dayofweek < 5][:10] # 僅保留工作日

stock_df = pd.DataFrame({
    "date": trade_dates,
    "open":  [1010.0, 1015.0, 1025.0, 1020.0, 1030.0, 1035.0, 1025.0, 1040.0, 1050.0, 1045.0],
    "high":  [1020.0, 1030.0, 1035.0, 1025.0, 1040.0, 1045.0, 1030.0, 1055.0, 1060.0, 1055.0],
    "low":   [1005.0, 1010.0, 1015.0, 1010.0, 1025.0, 1020.0, 1015.0, 1035.0, 1040.0, 1035.0],
    "close": [1015.0, 1025.0, 1020.0, 1030.0, 1035.0, 1025.0, 1040.0, 1050.0, 1045.0, 1050.0],
    "volume": [32000, 41000, 28000, 35000, 48000, 39000, 52000, 61000, 45000, 43000],
    "sentiment": [+0.45, +0.78, -0.12, +0.35, +0.82, -0.41, +0.65, +0.91, +0.22, +0.54],
    "top_keyword": ["法說看好", "營收新高", "外資調節", "散戶進場", "護國神山", "短線獲利", "多頭重啟", "狂飆暴賺", "量縮整理", "主力回補"]
})

# 模擬 PTT 股市版針對該標的之熱搜詞彙庫 (詞頻 + 情緒極性)
# ---------------------------------------------------------
# 取得 3 個聯成電腦學員故事文章
# ---------------------------------------------------------
urls = [
    "https://www.lccnet.com.tw/lccnet/student-stories/details/322",
    "https://www.lccnet.com.tw/lccnet/student-stories/details/321",
    "https://www.lccnet.com.tw/lccnet/student-stories/details/320"
]

all_text = ""

for url in urls:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # 取得網頁所有文字
    text = soup.get_text(" ", strip=True)

    all_text += text + " "


# ---------------------------------------------------------
# 中文斷詞
# ---------------------------------------------------------
words = jieba.lcut(all_text)

# 過濾太短的詞
words = [
    word.strip()
    for word in words
    if len(word.strip()) >= 2
]


# ---------------------------------------------------------
# 計算詞頻
# ---------------------------------------------------------
word_counts = Counter(words)

wordcloud_df = pd.DataFrame(
    word_counts.most_common(30),
    columns=["word", "count"]
)

# 模擬情緒值，先讓文字雲可以使用
wordcloud_df["sentiment"] = 0.0
# ---------------------------------------------------------
# 3. 分頁結構設計 (Tabs)
# ---------------------------------------------------------
tab_finance, tab_wordcloud = st.tabs(["📈 價量與社群情緒雙軸圖", "💬 PTT 焦點向量互動文字雲"])

# =========================================================
# 【分頁一】：複合金融走勢圖
# =========================================================
with tab_finance:
    # 👉 【學員填空處 1】：建立 2 列 1 欄畫布，第一列開啟 secondary_y，上下兩圖共用 X 軸
    fig_finance = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": True}], [{}]]
    )

    # 主軸：K 線圖 (Candlestick)
    fig_finance.add_trace(
        go.Candlestick(
            x=stock_df["date"], open=stock_df["open"], high=stock_df["high"],
            low=stock_df["low"], close=stock_df["close"], name="股價走勢",
            increasing_line_color="#ef4444", decreasing_line_color="#10b981"
        ),
        row=1, col=1, secondary_y=False
    )

    # 👉 【學員填空處 2】：次軸加入社群情緒折線 (secondary_y=True)
    fig_finance.add_trace(
        go.Scatter(
            x=stock_df["date"], y=stock_df["sentiment"], name="社群情緒指數",
            line=dict(color="#f59e0b", width=2.5),
            marker=dict(size=7, symbol="diamond"),
            customdata=stock_df["top_keyword"],
            hovertemplate="<b>日期</b>: %{x|%Y-%m-%d}<br><b>情緒分數</b>: %{y:+.2f}<br><b>當日焦點</b>: %{customdata}<extra></extra>"
        ),
        row=1, col=1, secondary_y=True
    )

    # 下排：成交量柱狀圖 (動態紅綠著色)
    bar_colors = np.where(stock_df["close"] >= stock_df["open"], "#ef4444", "#10b981")
    fig_finance.add_trace(
        go.Bar(x=stock_df["date"], y=stock_df["volume"], name="成交量 (張)", marker=dict(color=bar_colors, opacity=0.8)),
        row=2, col=1
    )

    # 優化座標軸與消除週末斷線
    fig_finance.update_layout(height=600, hovermode="x unified", margin=dict(l=30, r=30, t=40, b=30))
    fig_finance.update_yaxes(title_text="股價 (TWD)", row=1, col=1, secondary_y=False)
    fig_finance.update_yaxes(title_text="社群情緒", row=1, col=1, secondary_y=True, range=[-1.2, 1.2])
    fig_finance.update_yaxes(title_text="成交量", row=2, col=1)
    
    # 👉 【學員填空處 3】：剔除週末休市裂縫 (rangebreaks)
    fig_finance.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig_finance.update_xaxes(rangeslider_visible=False)

    st.plotly_chart(fig_finance, use_container_width=True)

# =========================================================
# 【分頁二】：Plotly 向量互動文字雲
# =========================================================
with tab_wordcloud:
    st.subheader("聯成電腦學員故事熱門關鍵詞文字雲")
    
    # 阿基米德螺線演算法：計算排版座標
    def calculate_spiral_layout(n_words: int):
        theta = np.linspace(0, 4.5 * np.pi, n_words)
        radius = np.linspace(0, 1.1, n_words)
        np.random.seed(42) # 固定隨機種子確保佈局穩定
        jitter_theta = theta + np.random.uniform(-0.15, 0.15, n_words)
        return radius * np.cos(jitter_theta), radius * np.sin(jitter_theta)

    x_pos, y_pos = calculate_spiral_layout(len(wordcloud_df))
    wordcloud_df["x"] = x_pos
    wordcloud_df["y"] = y_pos

    # 詞頻映射為字體大小 (16px ~ 46px)
    c_min, c_max = wordcloud_df["count"].min(), wordcloud_df["count"].max()
    wordcloud_df["font_size"] = 16 + (wordcloud_df["count"] - c_min) / (c_max - c_min) * (46 - 16)

    # 情緒正負動態色彩 (正向綠色、負向紅色)
    wordcloud_df["color"] = wordcloud_df["sentiment"].apply(lambda s: "#10b981" if s >= 0 else "#ef4444")

    # 👉 【學員填空處 4】：建立文字雲畫布並使用 go.Scatter 文字模式 (mode="text")
    fig_wc = go.Figure()
    fig_wc.add_trace(
        go.Scatter(
            x=wordcloud_df["x"],
            y=wordcloud_df["y"],
            mode="text",
            text=wordcloud_df["word"],
            textfont=dict(
                size=wordcloud_df["font_size"],
                color=wordcloud_df["color"],
                family="system-ui, -apple-system, sans-serif"
            ),
            customdata=np.stack((wordcloud_df["count"], wordcloud_df["sentiment"]), axis=-1),
            hovertemplate="<b>焦點關鍵詞</b>: %{text}<br>" +
                          "<b>PTT 出現頻次</b>: %{customdata[0]} 次<br>" +
                          "<b>社群情緒分數</b>: %{customdata[1]:+.2f}<extra></extra>"
        )
    )

    # 隱藏座標軸與格線，營造乾淨現代的文字雲視覺
    fig_wc.update_layout(
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-1.4, 1.4]),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[-1.4, 1.4]),
        plot_bgcolor="rgba(241, 245, 249, 0.6)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        height=520,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    # 👉 【學員填空處 5】：響應式嵌入 Streamlit
    st.plotly_chart(fig_wc, use_container_width=True)


import datetime
import re
from dataclasses import dataclass

import requests
import streamlit as st
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

st.set_page_config(
    page_title="全球宏观监控面板",
    page_icon="🌍",
    layout="wide",
)


@dataclass
class MetricRow:
    label: str
    value: str
    change: str
    status: str
    tone: str


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(27, 67, 50, 0.08), transparent 28%),
                linear-gradient(180deg, #fbfcf8 0%, #f2f4ec 100%);
            color: #1d241d;
        }
        .block-container {
            max-width: 1320px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .hero {
            background: linear-gradient(135deg, #1f3324 0%, #314b34 55%, #4c6748 100%);
            border-radius: 20px;
            padding: 24px 28px;
            color: #f4f7ef;
            box-shadow: 0 18px 45px rgba(24, 34, 24, 0.16);
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        .hero-subtitle {
            font-size: 0.95rem;
            color: rgba(244, 247, 239, 0.78);
            margin-top: 0.25rem;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 10px;
            margin-top: 16px;
        }
        .summary-chip {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 12px;
            padding: 10px 12px;
        }
        .summary-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            opacity: 0.72;
        }
        .summary-value {
            font-size: 1rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .section-card {
            background: rgba(255, 255, 255, 0.72);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(42, 56, 44, 0.08);
            border-radius: 18px;
            padding: 18px 20px 12px;
            box-shadow: 0 12px 30px rgba(29, 36, 29, 0.06);
            margin-bottom: 16px;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #213122;
            margin-bottom: 12px;
        }
        table.macro-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.94rem;
        }
        .macro-table th {
            text-align: left;
            color: #5b685d;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            padding: 10px 10px;
            border-bottom: 1px solid rgba(60, 77, 60, 0.14);
        }
        .macro-table td {
            padding: 11px 10px;
            border-bottom: 1px solid rgba(60, 77, 60, 0.08);
            vertical-align: middle;
        }
        .metric-label {
            font-weight: 600;
            color: #233224;
        }
        .metric-value {
            font-variant-numeric: tabular-nums;
            color: #1b241d;
        }
        .metric-change {
            font-variant-numeric: tabular-nums;
            font-weight: 600;
        }
        .tone-up { color: #12834d; }
        .tone-down { color: #c1493f; }
        .tone-flat { color: #64715e; }
        .status-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 9px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-right: 8px;
        }
        .pill-ok {
            color: #146c43;
            background: rgba(24, 131, 77, 0.12);
        }
        .pill-watch {
            color: #8b5a11;
            background: rgba(236, 173, 59, 0.18);
        }
        .pill-alert {
            color: #8d2c23;
            background: rgba(204, 81, 68, 0.16);
        }
        .status-text {
            color: #59665a;
        }
        .footer-note {
            color: #667568;
            font-size: 0.86rem;
            margin-top: 8px;
        }
        @media (max-width: 1100px) {
            .summary-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fetch_with_retry(url: str, parser_func, retries: int = 3):
    session = requests.Session()
    for attempt in range(retries):
        try:
            response = session.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
                verify=False,
            )
            parsed = parser_func(response.text)
            if parsed[0] is not None:
                return parsed
        except Exception:
            pass
        if attempt < retries - 1:
            import time

            time.sleep(0.5)
    return None, None


def parse_cnbc(text: str):
    price, pct = None, None
    match_price = re.search(r'"last":"(\d+\.?\d*)"', text)
    if match_price:
        price = float(match_price.group(1))

    match_pct = re.search(r'"change_pct":"(.*?)"', text)
    if match_pct:
        try:
            pct = float(match_pct.group(1).replace("%", ""))
        except ValueError:
            pct = 0.0

    if price is None:
        soup = BeautifulSoup(text, "html.parser")
        tag = soup.find("span", class_="QuoteStrip-lastPrice")
        if tag:
            price = float(tag.text.strip().replace("%", "").replace(",", ""))

    return price, pct


def parse_fred(text: str):
    match = re.search(r'series-meta-observation-value">\s*([\d\.,]+)', text)
    if match:
        return float(match.group(1).replace(",", "")), None
    return None, None


def fetch_cnbc(symbol: str):
    return fetch_with_retry(f"https://www.cnbc.com/quotes/{symbol}", parse_cnbc)


def fetch_fred(series_id: str):
    return fetch_with_retry(f"https://fred.stlouisfed.org/series/{series_id}", parse_fred)


def format_value(value, unit: str = "") -> str:
    if value is None:
        return "---"
    if unit == "$":
        return f"{value:,.2f} $"
    if unit == "%":
        return f"{value:,.2f}%"
    if unit == "bp":
        return f"{value:,.2f} bp"
    if unit == "B":
        return f"$ {value:,.0f} B"
    return f"{value:,.2f}"


def format_change(change) -> tuple[str, str]:
    if change is None:
        return "---", "tone-flat"
    if change > 0:
        return f"+{change:.2f}%", "tone-up"
    if change < 0:
        return f"{change:.2f}%", "tone-down"
    return f"{change:.2f}%", "tone-flat"


def tone_to_pill(tone: str) -> str:
    if tone == "ok":
        return "pill-ok"
    if tone == "watch":
        return "pill-watch"
    return "pill-alert"


def analyze_kwave(gold, cg_ratio):
    if gold is None or cg_ratio is None:
        return "数据不足", "watch"
    if gold > 3000 and cg_ratio < 0.15:
        return "康波冬：秩序重建", "alert"
    if cg_ratio > 0.25:
        return "康波春：复苏繁荣", "ok"
    return "康波秋：衰退过渡", "watch"


def analyze_kuznets(curve_10y2y, hy_spread):
    if curve_10y2y is None or hy_spread is None:
        return "数据不足", "watch"
    if curve_10y2y > 50 and hy_spread > 4.0:
        return "信用去杠杆", "watch"
    if hy_spread > 8.0:
        return "信用崩塌风险", "alert"
    if curve_10y2y < 0:
        return "信贷收缩前夜", "alert"
    return "信用扩张", "ok"


def analyze_debt_cycle(gold, dxy):
    if gold is None or dxy is None:
        return "数据不足", "watch"
    if gold > 3500:
        return "货币信用危机", "alert"
    if dxy > 105 and gold > 2500:
        return "大去杠杆末期", "watch"
    return "债务温和扩张", "ok"


def analyze_4th_turning(vix, gold):
    if vix is None or gold is None:
        return "数据不足", "watch"
    if gold > 3000 and vix < 20:
        return "秩序重组/地缘风险", "alert"
    if vix > 30:
        return "冲突爆发", "alert"
    return "秩序相对稳定", "ok"


@st.cache_data(ttl=900, show_spinner=False)
def load_dashboard_data():
    btc, btc_chg = fetch_cnbc("BTC.CB=")
    gold, gold_chg = fetch_cnbc("@GC.1")
    silver, silver_chg = fetch_cnbc("@SI.1")
    copper, copper_chg = fetch_cnbc("@HG.1")
    oil, oil_chg = fetch_cnbc("@CL.1")
    us10y, us10y_chg = fetch_cnbc("US10Y")
    us2y, us2y_chg = fetch_cnbc("US2Y")
    jp10y, jp10y_chg = fetch_cnbc("JP10Y")
    dxy, dxy_chg = fetch_cnbc(".DXY")
    usdcnh, usdcnh_chg = fetch_cnbc("CNH=")
    vix, vix_chg = fetch_cnbc(".VIX")
    hy_spread, _ = fetch_fred("BAMLH0A0HYM2")
    real_yield_10y, _ = fetch_fred("DFII10")
    rrp_liq, _ = fetch_fred("RRPONTSYD")

    cg_ratio = (copper * 100) / gold if copper and gold else None
    curve_10y2y = (us10y - us2y) * 100 if us10y and us2y else None

    return {
        "btc": (btc, btc_chg),
        "gold": (gold, gold_chg),
        "silver": (silver, silver_chg),
        "copper": (copper, copper_chg),
        "oil": (oil, oil_chg),
        "us10y": (us10y, us10y_chg),
        "us2y": (us2y, us2y_chg),
        "jp10y": (jp10y, jp10y_chg),
        "dxy": (dxy, dxy_chg),
        "usdcnh": (usdcnh, usdcnh_chg),
        "vix": (vix, vix_chg),
        "hy_spread": hy_spread,
        "real_yield_10y": real_yield_10y,
        "rrp_liq": rrp_liq,
        "cg_ratio": cg_ratio,
        "curve_10y2y": curve_10y2y,
    }


def make_row(label: str, value, change, unit: str, status: str, tone: str) -> MetricRow:
    change_text, change_class = format_change(change)
    return MetricRow(label, format_value(value, unit), f'<span class="{change_class}">{change_text}</span>', status, tone)


def render_table(title: str, rows: list[MetricRow], note: str | None = None) -> None:
    body = []
    for row in rows:
        pill_class = tone_to_pill(row.tone)
        body.append(
            f"""
            <tr>
              <td class="metric-label">{row.label}</td>
              <td class="metric-value">{row.value}</td>
              <td class="metric-change">{row.change}</td>
              <td><span class="status-pill {pill_class}">{'正常' if row.tone == 'ok' else '警戒' if row.tone == 'watch' else '预警'}</span><span class="status-text">{row.status}</span></td>
            </tr>
            """
        )

    note_html = f'<div class="footer-note">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="section-card">
          <div class="section-title">{title}</div>
          <table class="macro-table">
            <thead>
              <tr>
                <th>指标</th>
                <th>数值</th>
                <th>日内</th>
                <th>状态评估</th>
              </tr>
            </thead>
            <tbody>
              {''.join(body)}
            </tbody>
          </table>
          {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    inject_styles()

    st.title("🌍 全球宏观监控面板")
    st.caption("Streamlit 版 | 数据源：CNBC / FRED | 建议每次打开后点击刷新")

    col_left, col_right = st.columns([1, 0.18])
    with col_right:
        if st.button("刷新数据", use_container_width=True):
            load_dashboard_data.clear()
            st.rerun()

    with st.spinner("正在连接全球金融市场..."):
        data = load_dashboard_data()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    kw_text, kw_tone = analyze_kwave(data["gold"][0], data["cg_ratio"])
    kz_text, kz_tone = analyze_kuznets(data["curve_10y2y"], data["hy_spread"])
    dc_text, dc_tone = analyze_debt_cycle(data["gold"][0], data["dxy"][0])
    ft_text, ft_tone = analyze_4th_turning(data["vix"][0], data["gold"][0])

    summary_items = [
        ("BTC", format_value(data["btc"][0], "$")),
        ("黄金", format_value(data["gold"][0], "$")),
        ("美债10Y", format_value(data["us10y"][0], "%")),
        ("美元指数", format_value(data["dxy"][0])),
        ("VIX", format_value(data["vix"][0])),
        ("更新时间", now_str),
    ]

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-title">全球风险与流动性雷达</div>
          <div class="hero-subtitle">保留原项目的监控分组与判断逻辑，改为更适合浏览器阅读的 Streamlit 面板。</div>
          <div class="summary-grid">
            {''.join(f'<div class="summary-chip"><div class="summary-label">{label}</div><div class="summary-value">{value}</div></div>' for label, value in summary_items)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_table(
        "🧭 周期罗盘",
        [
            make_row("康波周期", None, None, "", kw_text, kw_tone),
            make_row("库兹涅茨周期", None, None, "", kz_text, kz_tone),
            make_row("长期债务周期", None, None, "", dc_text, dc_tone),
            make_row("第四次转折", None, None, "", ft_text, ft_tone),
        ],
    )

    render_table(
        "🅰️ 核心资产",
        [
            make_row("比特币", data["btc"][0], data["btc"][1], "$", "数字黄金", "ok"),
            make_row("黄金", data["gold"][0], data["gold"][1], "$", "---", "ok"),
            make_row("白银", data["silver"][0], data["silver"][1], "$", "---", "ok"),
            make_row("铜", data["copper"][0], data["copper"][1], "$", "---", "ok"),
            make_row("WTI原油", data["oil"][0], data["oil"][1], "$", "---", "ok"),
        ],
    )

    ratio_rows = []
    gold = data["gold"][0]
    silver = data["silver"][0]
    oil = data["oil"][0]
    copper = data["copper"][0]
    cg_ratio = data["cg_ratio"]

    if gold and silver:
        gs = gold / silver
        status = "通缩/避险" if gs > 85 else ("需关注" if gs > 70 else "复苏/通胀")
        tone = "alert" if gs > 85 else ("watch" if gs > 70 else "ok")
        ratio_rows.append(make_row("金银比", gs, None, "", status, tone))
    if gold and oil:
        go = gold / oil
        status = "极度衰退/战争" if go > 50 else ("避险主导" if go > 30 else "需求正常")
        tone = "alert" if go > 50 else ("watch" if go > 30 else "ok")
        ratio_rows.append(make_row("金油比", go, None, "", status, tone))
    if cg_ratio:
        status = "经济周期强" if cg_ratio > 0.20 else ("增长放缓" if cg_ratio > 0.15 else "衰退风险")
        tone = "ok" if cg_ratio > 0.20 else ("watch" if cg_ratio > 0.15 else "alert")
        ratio_rows.append(make_row("铜金比", cg_ratio, None, "", status, tone))
    if gold and copper:
        gc = gold / copper
        status = "避险爆表" if gc > 750 else ("避险升温" if gc > 650 else "情绪稳定")
        tone = "alert" if gc > 750 else ("watch" if gc > 650 else "ok")
        ratio_rows.append(make_row("金铜比", gc, None, "", status, tone))

    render_table("🅱️ 宏观比价", ratio_rows)

    liq_rows = []
    real_yield = data["real_yield_10y"]
    if real_yield is not None:
        tone = "ok" if real_yield < 0.5 else ("alert" if real_yield > 2.0 else "watch")
        status = "利率宽松/金牛" if real_yield < 1.0 else "紧缩/杀估值"
        liq_rows.append(make_row("10Y真实利率(TIPS)", real_yield, None, "%", status, tone))
    else:
        liq_rows.append(make_row("10Y真实利率(TIPS)", None, None, "%", "FRED数据缺失", "watch"))

    rrp_liq = data["rrp_liq"]
    if rrp_liq is not None:
        tone = "alert" if rrp_liq < 300 else "ok"
        status = "流动性枯竭" if rrp_liq < 300 else "资金充裕"
        liq_rows.append(make_row("逆回购规模(RRP)", rrp_liq, None, "B", status, tone))
    else:
        liq_rows.append(make_row("逆回购规模(RRP)", None, None, "B", "FRED数据缺失", "watch"))

    render_table("💧 流动性与通胀", liq_rows)

    rates_rows = [
        make_row("美债 10Y", data["us10y"][0], data["us10y"][1], "%", "---", "ok"),
        make_row("美债 2Y", data["us2y"][0], data["us2y"][1], "%", "---", "ok"),
        make_row("日债 10Y", data["jp10y"][0], data["jp10y"][1], "%", "---", "ok"),
    ]
    if data["us10y"][0] and data["jp10y"][0]:
        spread = (data["us10y"][0] - data["jp10y"][0]) * 100
        rates_rows.append(make_row("美日利差", spread, None, "bp", "资金流向", "watch"))
    if data["curve_10y2y"] is not None:
        if data["curve_10y2y"] < 0:
            rates_rows.append(make_row("10Y-2Y 利差", data["curve_10y2y"], None, "bp", "倒挂中", "alert"))
        else:
            rates_rows.append(make_row("10Y-2Y 利差", data["curve_10y2y"], None, "bp", "正常陡峭", "ok"))

    curve_note = None
    if data["curve_10y2y"] is not None and data["curve_10y2y"] < 0:
        days = (datetime.date.today() - datetime.date(2022, 7, 5)).days
        curve_note = f"当前收益率曲线倒挂累计 {days} 天，需关注衰退预警。"

    render_table("🆎 债市利率", rates_rows, note=curve_note)

    dxy = data["dxy"][0]
    cnh = data["usdcnh"][0]
    vix = data["vix"][0]
    hy_spread = data["hy_spread"]
    risk_rows = [
        make_row("美元指数(DXY)", dxy, data["dxy"][1], "", "极度紧缩" if dxy and dxy > 106 else ("流动性紧" if dxy and dxy > 103 else "宽裕"), "alert" if dxy and dxy > 106 else ("watch" if dxy and dxy > 103 else "ok")),
        make_row("USD/CNH(离岸)", cnh, data["usdcnh"][1], "", "贬值压力" if cnh and cnh > 7.30 else ("汇率承压" if cnh and cnh > 7.10 else "汇率稳健"), "alert" if cnh and cnh > 7.30 else ("watch" if cnh and cnh > 7.10 else "ok")),
        make_row("VIX恐慌指数", vix, data["vix"][1], "", "极度恐慌" if vix and vix > 30 else ("波动加剧" if vix and vix > 20 else "市场平稳"), "alert" if vix and vix > 30 else ("watch" if vix and vix > 20 else "ok")),
        make_row("高收益债利差", hy_spread, None, "%", "违约爆发" if hy_spread and hy_spread > 10 else ("信用收紧" if hy_spread and hy_spread > 5 else "风险低"), "alert" if hy_spread and hy_spread > 10 else ("watch" if hy_spread and hy_spread > 5 else "ok")),
    ]
    render_table("🅾️ 风险风向", risk_rows)


if __name__ == "__main__":
    render_dashboard()

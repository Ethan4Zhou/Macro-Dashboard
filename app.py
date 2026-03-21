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
        :root {
            --bg-main: #f4f5ef;
            --bg-soft: rgba(255, 255, 255, 0.78);
            --ink-strong: #1f291f;
            --ink-soft: #5e6a5f;
            --line-soft: rgba(49, 64, 50, 0.10);
            --green-600: #14754e;
            --green-100: rgba(20, 117, 78, 0.14);
            --amber-600: #996515;
            --amber-100: rgba(219, 171, 74, 0.18);
            --red-600: #b34c3f;
            --red-100: rgba(198, 88, 72, 0.18);
            --hero-a: #1d3022;
            --hero-b: #3c563d;
            --hero-c: #80956d;
        }
        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(74, 127, 88, 0.18), transparent 24%),
                radial-gradient(circle at 88% 12%, rgba(227, 191, 111, 0.15), transparent 20%),
                linear-gradient(180deg, #fbfbf7 0%, var(--bg-main) 100%);
            color: var(--ink-strong);
            font-family: "Avenir Next", "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", sans-serif;
        }
        .block-container {
            max-width: 1320px;
            padding-top: 1.3rem;
            padding-bottom: 2rem;
        }
        .hero-shell {
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.85fr);
            gap: 16px;
            margin-bottom: 1rem;
        }
        .hero {
            background:
                radial-gradient(circle at 84% 18%, rgba(235, 216, 134, 0.17), transparent 22%),
                linear-gradient(135deg, var(--hero-a) 0%, var(--hero-b) 52%, var(--hero-c) 100%);
            border-radius: 24px;
            padding: 26px 28px;
            color: #f4f7ef;
            box-shadow: 0 24px 52px rgba(24, 34, 24, 0.16);
            min-height: 244px;
        }
        .hero-title {
            font-size: 2.1rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            line-height: 1.08;
        }
        .hero-subtitle {
            font-size: 0.98rem;
            color: rgba(244, 247, 239, 0.78);
            margin-top: 0.45rem;
            max-width: 42rem;
        }
        .hero-band {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 18px;
        }
        .hero-band-chip {
            background: rgba(255, 255, 255, 0.09);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.82rem;
        }
        .hero-meta {
            display: flex;
            gap: 18px;
            flex-wrap: wrap;
            margin-top: 18px;
        }
        .hero-meta-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            opacity: 0.64;
        }
        .hero-meta-value {
            margin-top: 3px;
            font-size: 1rem;
            font-weight: 700;
        }
        .hero-side {
            display: grid;
            gap: 16px;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
        }
        .summary-chip {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(39, 54, 39, 0.08);
            border-radius: 16px;
            padding: 14px 14px 13px;
            min-height: 96px;
            box-shadow: 0 14px 36px rgba(32, 45, 32, 0.05);
        }
        .summary-label {
            font-size: 0.73rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--ink-soft);
        }
        .summary-value {
            font-size: 1.15rem;
            font-weight: 700;
            margin-top: 8px;
            color: var(--ink-strong);
        }
        .summary-change {
            margin-top: 6px;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .summary-card {
            background: var(--bg-soft);
            backdrop-filter: blur(10px);
            border: 1px solid var(--line-soft);
            border-radius: 20px;
            padding: 18px 18px 16px;
            box-shadow: 0 16px 36px rgba(29, 36, 29, 0.06);
        }
        .summary-card-title {
            color: var(--ink-soft);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .summary-card-main {
            color: var(--ink-strong);
            font-size: 1.45rem;
            font-weight: 700;
            margin-top: 8px;
            line-height: 1.16;
        }
        .summary-card-text {
            color: var(--ink-soft);
            font-size: 0.9rem;
            margin-top: 8px;
            line-height: 1.5;
        }
        .pulse-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
            margin-bottom: 14px;
        }
        .pulse-card {
            background: rgba(255, 255, 255, 0.76);
            border: 1px solid var(--line-soft);
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 12px 26px rgba(29, 36, 29, 0.045);
        }
        .pulse-title {
            color: var(--ink-soft);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .pulse-value {
            color: var(--ink-strong);
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 8px;
            font-variant-numeric: tabular-nums;
        }
        .pulse-sub {
            margin-top: 7px;
            font-size: 0.84rem;
            color: var(--ink-soft);
        }
        .insight-card {
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(248, 249, 243, 0.92));
            border: 1px solid var(--line-soft);
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: 0 16px 34px rgba(29, 36, 29, 0.055);
            margin-bottom: 14px;
        }
        .insight-title {
            color: var(--ink-soft);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .insight-main {
            color: var(--ink-strong);
            font-size: 1.18rem;
            font-weight: 700;
            line-height: 1.4;
            margin-top: 8px;
        }
        .signal-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-top: 14px;
        }
        .signal-item {
            background: rgba(245, 247, 241, 0.94);
            border: 1px solid rgba(47, 66, 49, 0.08);
            border-radius: 14px;
            padding: 12px 13px;
        }
        .signal-item-title {
            font-size: 0.82rem;
            color: var(--ink-soft);
            margin-bottom: 6px;
        }
        .signal-item-value {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--ink-strong);
        }
        .section-card {
            background: rgba(255, 255, 255, 0.74);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(42, 56, 44, 0.07);
            border-radius: 18px;
            padding: 18px 20px 12px;
            box-shadow: 0 12px 30px rgba(29, 36, 29, 0.06);
            margin-bottom: 16px;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--ink-strong);
            margin-bottom: 12px;
        }
        table.macro-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.94rem;
        }
        .macro-table th {
            text-align: left;
            color: var(--ink-soft);
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
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            margin-bottom: 0.85rem;
        }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(47, 66, 49, 0.08);
            border-radius: 999px;
            padding: 0.55rem 0.95rem;
            color: #516052;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background: #213525 !important;
            color: #f1f6eb !important;
            border-color: #213525 !important;
        }
        div.stButton > button {
            border-radius: 999px;
            background: #263b29;
            color: #f4f7ef;
            border: none;
            font-weight: 700;
            padding: 0.5rem 1rem;
            box-shadow: 0 12px 24px rgba(28, 44, 30, 0.14);
        }
        div.stButton > button:hover {
            background: #314d36;
            color: #ffffff;
        }
        @media (max-width: 1100px) {
            .hero-shell {
                grid-template-columns: 1fr;
            }
            .summary-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .pulse-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .signal-grid {
                grid-template-columns: 1fr;
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


def render_pulse_cards(cards: list[tuple[str, str, str, str]]) -> None:
    st.markdown(
        f"""
        <div class="pulse-grid">
          {''.join(
              f'''
              <div class="pulse-card">
                <div class="pulse-title">{title}</div>
                <div class="pulse-value">{value}</div>
                <div class="pulse-sub {tone_class}">{subtext}</div>
              </div>
              '''
              for title, value, subtext, tone_class in cards
          )}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(title: str, main_text: str, signals: list[tuple[str, str]]) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-title">{title}</div>
          <div class="insight-main">{main_text}</div>
          <div class="signal-grid">
            {''.join(
                f'''
                <div class="signal-item">
                  <div class="signal-item-title">{label}</div>
                  <div class="signal-item-value">{value}</div>
                </div>
                '''
                for label, value in signals
            )}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    with st.spinner("正在连接全球金融市场..."):
        data = load_dashboard_data()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    kw_text, kw_tone = analyze_kwave(data["gold"][0], data["cg_ratio"])
    kz_text, kz_tone = analyze_kuznets(data["curve_10y2y"], data["hy_spread"])
    dc_text, dc_tone = analyze_debt_cycle(data["gold"][0], data["dxy"][0])
    ft_text, ft_tone = analyze_4th_turning(data["vix"][0], data["gold"][0])

    all_tones = [kw_tone, kz_tone, dc_tone, ft_tone]
    alert_count = sum(1 for tone in all_tones if tone == "alert")
    watch_count = sum(1 for tone in all_tones if tone == "watch")
    if alert_count >= 2:
        main_bias = "防御优先，周期与信用面信号偏紧。"
    elif alert_count == 1 or watch_count >= 2:
        main_bias = "多空交织，适合重点观察利率、美元与波动率。"
    else:
        main_bias = "整体环境偏稳，暂未出现系统性挤兑信号。"

    summary_cards = [
        ("BTC", format_value(data["btc"][0], "$"), format_change(data["btc"][1])[0], format_change(data["btc"][1])[1]),
        ("黄金", format_value(data["gold"][0], "$"), format_change(data["gold"][1])[0], format_change(data["gold"][1])[1]),
        ("美债10Y", format_value(data["us10y"][0], "%"), format_change(data["us10y"][1])[0], format_change(data["us10y"][1])[1]),
        ("美元指数", format_value(data["dxy"][0]), format_change(data["dxy"][1])[0], format_change(data["dxy"][1])[1]),
        ("VIX", format_value(data["vix"][0]), format_change(data["vix"][1])[0], format_change(data["vix"][1])[1]),
        ("更新时间", now_str, "15 分钟缓存", "tone-flat"),
    ]

    st.markdown(
        f"""
        <div class="hero-shell">
          <div class="hero">
            <div class="hero-title">全球风险与流动性雷达</div>
            <div class="hero-subtitle">保留原项目的宏观监控逻辑，但把终端信息重组为更适合浏览器长期查看的仪表盘。你现在可以先看结论，再向下拆解资产、利率和风险层。</div>
            <div class="hero-band">
              <div class="hero-band-chip">CNBC Quotes</div>
              <div class="hero-band-chip">FRED Series</div>
              <div class="hero-band-chip">周期 / 资产 / 流动性 / 风险</div>
            </div>
            <div class="hero-meta">
              <div>
                <div class="hero-meta-label">市场判断</div>
                <div class="hero-meta-value">{main_bias}</div>
              </div>
              <div>
                <div class="hero-meta-label">数据刷新</div>
                <div class="hero-meta-value">{now_str}</div>
              </div>
            </div>
          </div>
          <div class="hero-side">
            <div class="summary-card">
              <div class="summary-card-title">风险温度</div>
              <div class="summary-card-main">{alert_count} 个预警 / {watch_count} 个警戒</div>
              <div class="summary-card-text">预警主要来自信用、地缘或收益率曲线倒挂；警戒代表暂未失控，但需要持续跟踪。</div>
            </div>
            <div class="summary-card">
              <div class="summary-card-title">使用说明</div>
              <div class="summary-card-text">页面默认缓存 15 分钟，避免频繁抓取外部网页导致卡顿。若你想看最新一轮抓取结果，点击右上角“刷新数据”。</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    top_controls = st.columns([1, 0.22])
    with top_controls[1]:
        if st.button("刷新数据", use_container_width=True):
            load_dashboard_data.clear()
            st.rerun()

    render_pulse_cards(summary_cards)

    render_insight_card(
        "当前要点",
        main_bias,
        [
            ("康波周期", kw_text),
            ("信用周期", kz_text),
            ("债务周期", dc_text),
            ("第四转折", ft_text),
        ],
    )

    core_asset_rows = [
        make_row("比特币", data["btc"][0], data["btc"][1], "$", "数字黄金", "ok"),
        make_row("黄金", data["gold"][0], data["gold"][1], "$", "---", "ok"),
        make_row("白银", data["silver"][0], data["silver"][1], "$", "---", "ok"),
        make_row("铜", data["copper"][0], data["copper"][1], "$", "---", "ok"),
        make_row("WTI原油", data["oil"][0], data["oil"][1], "$", "---", "ok"),
    ]

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
    cycle_rows = [
        make_row("康波周期", None, None, "", kw_text, kw_tone),
        make_row("库兹涅茨周期", None, None, "", kz_text, kz_tone),
        make_row("长期债务周期", None, None, "", dc_text, dc_tone),
        make_row("第四次转折", None, None, "", ft_text, ft_tone),
    ]

    tab_overview, tab_assets, tab_risk = st.tabs(["总览", "资产与利率", "风险与周期"])

    with tab_overview:
        col_a, col_b = st.columns(2)
        with col_a:
            render_table("🧭 周期罗盘", cycle_rows)
            render_table("💧 流动性与通胀", liq_rows)
        with col_b:
            render_table("🅾️ 风险风向", risk_rows)
            render_table("🅱️ 宏观比价", ratio_rows)

    with tab_assets:
        col_a, col_b = st.columns(2)
        with col_a:
            render_table("🅰️ 核心资产", core_asset_rows)
            render_table("🅱️ 宏观比价", ratio_rows)
        with col_b:
            render_table("🆎 债市利率", rates_rows, note=curve_note)
            render_table("💧 流动性与通胀", liq_rows)

    with tab_risk:
        col_a, col_b = st.columns(2)
        with col_a:
            render_table("🧭 周期罗盘", cycle_rows)
            render_table("🅾️ 风险风向", risk_rows)
        with col_b:
            render_insight_card(
                "风险聚焦",
                "把这里当成每日检查清单：先看美元与真实利率，再看 VIX 和高收益债利差，最后确认收益率曲线是否继续倒挂。",
                [
                    ("美元指数", format_value(dxy)),
                    ("真实利率", format_value(real_yield, "%")),
                    ("VIX", format_value(vix)),
                    ("高收益债利差", format_value(hy_spread, "%")),
                ],
            )
            render_table("🆎 债市利率", rates_rows, note=curve_note)


if __name__ == "__main__":
    render_dashboard()

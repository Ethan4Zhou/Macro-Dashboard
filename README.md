# Macro Dashboard

基于 Streamlit 的全球宏观监控面板。

## 本地运行

```bash
pip install -r requirements.txt
export FRED_API_KEY=你的_FRED_API_KEY
streamlit run app.py
```

## 数据来源

- CNBC Quotes
- FRED

说明：

- CNBC 继续使用网页抓取，负责实时价格
- FRED 现支持官方 API，负责高收益债利差、10Y TIPS 实际利率、RRP
- 建议通过环境变量 `FRED_API_KEY` 或 Streamlit Secrets 配置 FRED key
- 若未配置 FRED key，或官方 API 临时不可用，程序会自动回退到旧网页抓取
- 如果外部网页响应较慢，首次加载可能会有等待

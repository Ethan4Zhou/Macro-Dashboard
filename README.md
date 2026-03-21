# Macro Dashboard

基于 Streamlit 的全球宏观监控面板。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 数据来源

- CNBC Quotes
- FRED

说明：

- 当前版本沿用原始项目的网页抓取方式，不需要额外 API Key
- 如果外部网页响应较慢，首次加载可能会有等待

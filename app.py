import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="PDF 完整顯示版", layout="wide")
st.title("💰 帳單資料提取 (寬鬆顯示版)")

uploaded_file = st.file_uploader("請上傳 PDF", type="pdf")
password = st.text_input("密碼：", type="password")

if uploaded_file is not None:
    try:
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            all_rows = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_rows.extend(table)
            
            if all_rows:
                raw_df = pd.DataFrame(all_rows)
                
                st.write("### 1. 原始資料檢查")
                st.dataframe(raw_df)
                
                st.divider()
                
                # 讓使用者選欄位
                cols = list(raw_df.columns)
                c1, c2, c3 = st.columns(3)
                with c1:
                    date_idx = st.selectbox("哪一欄是『日期』？", cols, index=0)
                with c2:
                    detail_idx = st.selectbox("哪一欄是『明細』？", cols, index=1 if len(cols)>1 else 0)
                with c3:
                    amount_idx = st.selectbox("哪一欄是『金額』？", cols, index=2 if len(cols)>2 else 0)

                # --- 這裡開始改為「寬鬆模式」 ---
                # 只單純提取，不進行任何過濾刪除
                final_df = raw_df[[date_idx, detail_idx, amount_idx]].copy()
                final_df.columns = ['日期', '消費明細', '金額']

                st.write("### 2. 整理後的結果 (不進行過濾)")
                st.dataframe(final_df, use_container_width=True)
                
                # 計算總金額的邏輯
                def force_amount(val):
                    if val is None: return 0.0
                    s = str(val)
                    # 留下數字、點、負號
                    cleaned = "".join(re.findall(r'[0-9\.\-]', s))
                    try: 
                        return float(cleaned)
                    except: 
                        return 0.0

                total_sum = final_df['金額'].apply(force_amount).sum()
                st.metric("本月合計 (包含可能的標題雜訊)", f"${total_sum:,.2f}")
                
                # 下載按鈕
                csv = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載此表 (CSV)", csv, "report.csv", "text/csv")
                
            else:
                st.error("找不到表格資料。")
    except Exception as e:
        st.error(f"發生錯誤：{e}")

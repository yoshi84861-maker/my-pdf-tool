import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="PDF 消費整理器", layout="wide")
st.title("💰 帳單資料提取 (金額修正版)")

uploaded_file = st.file_uploader("請上傳 PDF", type="pdf")
password = st.text_input("密碼：", type="password")

if uploaded_file is not None:
    try:
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            all_data = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_data.extend(table)
            
            if all_data:
                raw_df = pd.DataFrame(all_data)
                st.write("### 1. 原始資料檢查")
                st.dataframe(raw_df)
                
                st.divider()
                
                cols = list(raw_df.columns)
                c1, c2, c3 = st.columns(3)
                with c1:
                    date_idx = st.selectbox("哪一欄是『日期』？", cols, index=0)
                with c2:
                    detail_idx = st.selectbox("哪一欄是『明細』？", cols, index=1 if len(cols)>1 else 0)
                with c3:
                    amount_idx = st.selectbox("哪一欄是『金額』？", cols, index=2 if len(cols)>2 else 0)

                # 提取並清理
                final_df = raw_df[[date_idx, detail_idx, amount_idx]].copy()
                final_df.columns = ['日期', '消費明細', '金額']
                
                # 去掉空列
                final_df = final_df.dropna()

                # --- 核心修正：金額轉換邏輯 ---
                def force_amount_to_float(val):
                    if val is None: return 0.0
                    # 1. 轉成字串
                    s = str(val)
                    # 2. 只留下數字、點(.)、負號(-)
                    # 這一行會過濾掉 $ , TWD 等雜質
                    cleaned = "".join(re.findall(r'[0-9\.\-]', s))
                    try:
                        return float(cleaned)
                    except:
                        return 0.0

                # 建立一個計算用的數值欄位
                final_df['數值金額'] = final_df['金額'].apply(force_amount_to_float)
                
                # 過濾掉「數值為 0」的列 (通常是標題列或雜訊)
                final_df = final_df[final_df['數值金額'] != 0]

                st.write("### 2. 整理後的結果")
                st.dataframe(final_df[['日期', '消費明細', '金額']], use_container_width=True)
                
                # 計算總金額
                total_sum = final_df['數值金額'].sum()
                st.metric("本月消費總計", f"${total_sum:,.2f}")
                
                # 下載按鈕
                csv = final_df[['日期', '消費明細', '金額']].to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載 Excel (CSV)", csv, "report.csv", "text/csv")
                
            else:
                st.error("找不到表格。")
    except Exception as e:
        st.error(f"發生錯誤：{e}")

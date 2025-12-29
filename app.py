import streamlit as st
import pdfplumber
import pandas as pd

st.set_page_config(page_title="PDF 強力整理器", layout="wide")
st.title("💰 帳單資料提取測試")

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
                # 轉成原始 DataFrame 顯示
                raw_df = pd.DataFrame(all_data)
                
                st.write("### 1. 原始資料檢查 (看看資料在第幾欄)")
                st.dataframe(raw_df) # 這裡會顯示所有內容，包含標題
                
                st.divider()
                
                st.write("### 2. 設定欄位並清理")
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
                
                # 強力清理：去掉空值、去掉跟標題一模一樣的文字
                final_df = final_df.dropna()
                # 只要那一列的內容包含「日期」兩個字，就刪掉
                final_df = final_df[~final_df['日期'].astype(str).contains("日期")]

                st.write("### 3. 整理後的結果")
                st.dataframe(final_df, use_container_width=True)
                
                # 嘗試計算總金額
                def clean_amount(x):
                    try:
                        # 只留下數字、點、負號
                        s = "".join(c for c in str(x) if c.isdigit() or c in ".-")
                        return float(s)
                    except:
                        return 0.0

                total_sum = final_df['金額'].apply(clean_amount).sum()
                st.metric("本月合計", f"${total_sum:,.2f}")
                
            else:
                st.error("找不到表格，請確認 PDF 內容是否為文字格式。")
                
    except Exception as e:
        st.error(f"發生錯誤：{e}")

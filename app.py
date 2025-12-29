import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="PDF 多頁面整理器", layout="wide")
st.title("💰 跨頁面帳單資料提取")

uploaded_file = st.file_uploader("請上傳 PDF", type="pdf")
password = st.text_input("密碼：", type="password")

if uploaded_file is not None:
    try:
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            all_rows = []
            # 遍歷每一頁
            for i, page in enumerate(pdf.pages):
                table = page.extract_table()
                if table:
                    # 只要這頁有表格，就把它存進來
                    all_rows.extend(table)
            
            if all_rows:
                # 把所有頁面的表格合併成一個大的 DataFrame
                raw_df = pd.DataFrame(all_rows)
                
                st.write("### 1. 原始資料檢查 (已合併所有頁面)")
                st.dataframe(raw_df)
                
                st.divider()
                
                # 欄位選擇
                cols = list(raw_df.columns)
                c1, c2, c3 = st.columns(3)
                with c1:
                    date_idx = st.selectbox("哪一欄是『日期』？", cols, index=0)
                with c2:
                    detail_idx = st.selectbox("哪一欄是『明細』？", cols, index=1 if len(cols)>1 else 0)
                with c3:
                    amount_idx = st.selectbox("哪一欄是『金額』？", cols, index=2 if len(cols)>2 else 0)

                # 提取指定欄位
                final_df = raw_df[[date_idx, detail_idx, amount_idx]].copy()
                final_df.columns = ['日期', '消費明細', '金額']
                
                # 清理：轉數字
                def force_amount(val):
                    if val is None: return 0.0
                    s = str(val)
                    cleaned = "".join(re.findall(r'[0-9\.\-]', s))
                    try: return float(cleaned)
                    except: return 0.0

                final_df['數值金額'] = final_df['金額'].apply(force_amount)
                
                # 過濾掉「日期」欄位裡不是日期格式或是空的資料
                # 這裡假設日期通常包含斜線 / 或連字號 -
                final_df = final_df[final_df['日期'].astype(str).str.contains(r'[0-9]', na=False)]
                final_df = final_df[final_df['數值金額'] != 0]

                st.write("### 2. 最終整理結果")
                st.dataframe(final_df[['日期', '消費明細', '金額']], use_container_width=True)
                
                total_sum = final_df['數值金額'].sum()
                st.balloons() # 成功抓到資料時噴點氣球慶祝！
                st.metric("所有頁面消費總計", f"${total_sum:,.2f}")
                
            else:
                st.error("在所有頁面中都找不到表格資料。")
    except Exception as e:
        st.error(f"發生錯誤：{e}")

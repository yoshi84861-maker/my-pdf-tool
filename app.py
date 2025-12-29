import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="PDF 欄位拆分版", layout="wide")
st.title("💰 帳單資料提取 (自動拆分欄位)")

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
                st.write("### 1. 原始資料檢查 (資料全都擠在第 0 欄)")
                st.dataframe(raw_df)

                # --- 核心邏輯：拆分第 0 欄 ---
                def split_combined_row(row):
                    text = str(row[0]) # 抓取第 0 欄的內容
                    # 邏輯：用多個空格來切分
                    parts = re.split(r'\s{2,}', text.strip()) 
                    
                    # 如果切不開（空格太少），嘗試用最後一個數字（可能是金額）來切
                    if len(parts) < 3:
                        # 這是一個備用邏輯：尋找結尾的數字作為金額
                        match = re.search(r'(.*)\s+(\d+[\d,.]*)$', text)
                        if match:
                            return [None, match.group(1), match.group(2)]
                    
                    return parts

                # 建立新的 DataFrame
                split_data = []
                for _, row in raw_df.iterrows():
                    parts = split_combined_row(row)
                    if len(parts) >= 2: # 至少要有資料才放進去
                        split_data.append(parts)
                
                if split_data:
                    # 重新整理成表格，手動給它標題
                    # 我們取最後三欄，假設是 日期/明細/金額
                    final_df = pd.DataFrame(split_data)
                    
                    st.divider()
                    st.write("### 2. 嘗試拆分後的結果")
                    st.dataframe(final_df, use_container_width=True)

                    # 這裡讓使用者選拆分後的欄位
                    split_cols = list(final_df.columns)
                    st.info("請根據上方「拆分後的結果」，重新選擇正確的欄位編號：")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        d_idx = st.selectbox("哪一欄是『日期』？", split_cols, index=0)
                    with c2:
                        m_idx = st.selectbox("哪一欄是『明細』？", split_cols, index=1 if len(split_cols)>1 else 0)
                    with c3:
                        a_idx = st.selectbox("哪一欄是『金額』？", split_cols, index=len(split_cols)-1)

                    # 計算與下載... (略，維持之前邏輯)
                else:
                    st.warning("無法自動拆分欄位內容，請確認資料格式。")
            else:
                st.error("找不到表格。")
    except Exception as e:
        st.error(f"發生錯誤：{e}")

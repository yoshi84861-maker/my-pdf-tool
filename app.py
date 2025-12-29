import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="每月消費自動整理器", layout="wide")
st.title("💰 每月消費明細自動整理")
st.markdown("上傳 PDF 後，程式會自動提取：**日期、金額、消費明細** 並合併成表。")

uploaded_file = st.file_uploader("請上傳本月 PDF 帳單", type="pdf")
password = st.text_input("密碼 (若無則留空)：", type="password")

if uploaded_file is not None:
    all_rows = []
    
    try:
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # 轉成 DataFrame 處理
                    df = pd.DataFrame(table)
                    all_rows.append(df)
            
            if all_rows:
                # 1. 合併所有頁面
                combined_df = pd.concat(all_rows, ignore_index=True)
                
                # 2. 清理資料：刪除全空的列
                combined_df = combined_df.dropna(how='all')

                st.success("✅ 讀取成功！請從下方下拉選單確認欄位：")
                
                # 讓使用者手動確認一下哪一欄是哪一個（因為不同銀行的 PDF 順序可能不同）
                all_columns = list(combined_df.columns)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    date_col = st.selectbox("哪一欄是『日期』？", all_columns, index=0)
                with col2:
                    detail_col = st.selectbox("哪一欄是『消費明細/摘要』？", all_columns, index=1 if len(all_columns)>1 else 0)
                with col3:
                    amount_col = st.selectbox("哪一欄是『金額』？", all_columns, index=2 if len(all_columns)>2 else 0)

                # 3. 提取指定的欄位並重新命名
                final_df = combined_df[[date_col, detail_col, amount_col]].copy()
                final_df.columns = ['日期', '消費明細', '金額']

                # 4. 進階清理：過濾掉標題列（例如：日期 欄位裡剛好寫著 "日期" 兩個字的人）
                # 這邊會過濾掉非日期格式或重複標題的雜質
                final_df = final_df[final_df['日期'] != '日期']
                final_df = final_df.dropna()

                st.write("### 📊 本月整理結果預覽")
                st.dataframe(final_df, use_container_width=True)
                
                # 5. 計算總金額（選用功能）
                try:
                    # 先把金額裡的逗號、錢字號去掉，轉成數字計算
                    temp_amount = final_df['金額'].astype(str).str.replace(',', '').str.replace('$', '').str.extract(r'(\d+)')[0]
                    total = pd.to_numeric(temp_amount).sum()
                    st.metric("本月消費總計", f"${total:,.0f}")
                except:
                    pass

                # 6. 下載 CSV (適合 Excel 開啟)
                csv = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 下載本月整理報表 (Excel格式)",
                    data=csv,
                    file_name="monthly_expenses.csv",
                    mime='text/csv'
                )
            else:
                st.warning("找不到任何表格資料。")
                
    except Exception as e:
        st.error(f"解析發生錯誤：{e}")
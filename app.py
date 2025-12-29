import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="帳單精準拆分器", layout="wide")
st.title("💰 帳單資料提取 (格式化拆分版)")

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
                # 建立存放拆分後資料的清單
                refined_data = []
                
                for row in all_rows:
                    # 把整列合併成一個字串處理
                    text = " ".join([str(item) for item in row if item is not None])
                    
                    # 使用正則表達式抓取：日期 (114/11/10) + 入帳日 + 明細 + 金額
                    # 邏輯：尋找兩個日期開頭，中間夾文字，後面跟著數字
                    pattern = r'(\d+/\d+/\d+)\s+(\d+/\d+/\d+)\s+(.*?)\s+(\d+[\d,]*)\s+TW'
                    match = re.search(pattern, text)
                    
                    if match:
                        date = match.group(1)      # 消費日
                        detail = match.group(3)    # 明細
                        amount = match.group(4)    # 金額
                        refined_data.append([date, detail, amount])

                if refined_data:
                    final_df = pd.DataFrame(refined_data, columns=['日期', '消費明細', '金額'])
                    
                    # 清理金額變成數字以便加總
                    final_df['數值金額'] = final_df['金額'].str.replace(',', '').astype(float)
                    
                    st.success(f"✅ 成功辨識出 {len(final_df)} 筆消費紀錄！")
                    st.write("### 📊 整理後的帳單明細")
                    st.dataframe(final_df[['日期', '消費明細', '金額']], use_container_width=True)
                    
                    total = final_df['數值金額'].sum()
                    st.metric("本月總計", f"${total:,.0f}")
                    
                    # 下載按鈕
                    csv = final_df[['日期', '消費明細', '金額']].to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 下載 Excel (CSV)", csv, "monthly_report.csv", "text/csv")
                else:
                    st.warning("抓到了文字但無法拆分欄位。請檢查原始資料區。")
                    st.write("原始偵測文字範例：", text if 'text' in locals() else "無")
                    
            else:
                st.error("找不到表格內容。")
    except Exception as e:
        st.error(f"發生錯誤：{e}")

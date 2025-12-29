import streamlit as st
import pdfplumber
import pandas as pd
import re
import plotly.express as px # 這是畫圖用的零件

st.set_page_config(page_title="消費分析 App", layout="wide")
st.title("📊 帳單消費大數據分析")

# --- 設定分類規則 (你可以自行修改或增加) ---
CATEGORIES = {
    "餐飲美食": ["肉排", "餐", "飯", "麵", "星巴克", "麥當勞", "飲料", "食"],
    "交通運輸": ["中油", "台鐵", "高鐵", "計程車", "LINE TAXI", "停車", "加油"],
    "線上購物": ["蝦皮", "MOMO", "PCHOME", "亞馬遜", "街口", "藍新"],
    "生活繳費": ["電信", "水費", "電費", "保險"],
    "休閒娛樂": ["電影", "Netflix", "Spotify", "KTV", "飯店"]
}

def auto_category(detail):
    for cat, keywords in CATEGORIES.items():
        if any(k in detail for k in keywords):
            return cat
    return "其他"

uploaded_file = st.file_uploader("上傳本月 PDF", type="pdf")
password = st.text_input("密碼：", type="password")

if uploaded_file is not None:
    try:
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            refined_data = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        text = " ".join([str(item) for item in row if item is not None])
                        pattern = r'(\d+/\d+/\d+)\s+(\d+/\d+/\d+)\s+(.*?)\s+(\d+[\d,]*)\s+TW'
                        match = re.search(pattern, text)
                        if match:
                            date, detail, amount = match.group(1), match.group(3), match.group(4)
                            refined_data.append([date, detail, amount])

            if refined_data:
                df = pd.DataFrame(refined_data, columns=['日期', '消費明細', '金額'])
                df['數值金額'] = df['金額'].str.replace(',', '').astype(float)
                
                # --- 自動分類 ---
                df['分類'] = df['消費明細'].apply(auto_category)

                # --- 顯示數據摘要 ---
                total_sum = df['數值金額'].sum()
                st.metric("本月消費總計", f"${total_sum:,.0f}")

                # --- 建立視覺化圖表 ---
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write("### 🍱 分類統計")
                    cat_df = df.groupby('分類')['數值金額'].sum().reset_index()
                    fig = px.pie(cat_df, values='數值金額', names='分類', hole=0.4, title="消費佔比圖")
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.write("### 📝 明細表")
                    st.dataframe(df[['日期', '消費明細', '分類', '金額']], use_container_width=True)

                # --- 額外：支出排行 ---
                st.write("### 🔝 本月前三大支出")
                top_3 = df.nlargest(3, '數值金額')
                for i, row in top_3.iterrows():
                    st.warning(f"第 {i+1} 名: {row['消費明細']} - ${row['數值金額']:,.0f}")

            else:
                st.error("無法解析內容。")
    except Exception as e:
        st.error(f"分析出錯：{e}")

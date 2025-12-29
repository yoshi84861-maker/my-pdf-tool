import streamlit as st
import pdfplumber
import pandas as pd
import re
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

st.set_page_config(page_title="消費大數據分析", layout="wide")
st.title("📊 帳單深度分析報告")

# --- 店家名稱精簡化邏輯 ---
def clean_shop_name(name):
    # 移除常見的雜質
    name = re.sub(r'(TAIPEI|TAICHUNG|KAOHSIUNG|TW|－|—)', '', name) # 移除城市名與橫線
    name = re.sub(r'\d+.*店', '', name) # 移除像「參店」、「012店」等分店資訊
    name = name.strip()
    return name[:15] # 取前15個字，避免太長

# --- 設定分類規則 ---
CATEGORIES = {
    "餐飲美食": ["肉排", "餐", "飯", "麵", "星巴克", "麥當勞", "飲料", "食", "咖啡", "壽司"],
    "交通運輸": ["中油", "台鐵", "高鐵", "計程車", "LINE TAXI", "停車", "加油", "悠遊卡"],
    "線上購物": ["蝦皮", "MOMO", "PCHOME", "亞馬遜", "街口", "藍新", "支付"],
    "生活繳費": ["電信", "水費", "電費", "保險", "醫院"],
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
                        # 這裡使用你之前成功的精準切片模式
                        pattern = r'(\d+/\d+/\d+)\s+(\d+/\d+/\d+)\s+(.*?)\s+(\d+[\d,]*)\s+TW'
                        match = re.search(pattern, text)
                        if match:
                            date, detail, amount = match.group(1), match.group(3), match.group(4)
                            refined_data.append([date, detail, amount])

            if refined_data:
                df = pd.DataFrame(refined_data, columns=['日期', '消費明細', '金額'])
                df['數值金額'] = df['金額'].str.replace(',', '').astype(float)
                df['分類'] = df['消費明細'].apply(auto_category)
                df['精簡店家'] = df['消費明細'].apply(clean_shop_name)

                # --- 頂部指標 ---
                st.metric("本月消費總額", f"${df['數值金額'].sum():,.0f}")
                st.divider()

                # --- 第一區：圖表分析 ---
                col1, col2 = st.columns(2)
                with col1:
                    st.write("### 🍱 消費類別佔比")
                    if HAS_PLOTLY:
                        cat_df = df.groupby('分類')['數值金額'].sum().reset_index()
                        fig_pie = px.pie(cat_df, values='數值金額', names='分類', hole=0.4)
                        st.plotly_chart(fig_pie, use_container_width=True)

                with col2:
                    st.write("### 🏪 常去店家排行 (次數)")
                    # 統計店家出現次數
                    shop_counts = df['精簡店家'].value_counts().reset_index()
                    shop_counts.columns = ['店家名稱', '消費次數']
                    if HAS_PLOTLY:
                        fig_bar = px.bar(shop_counts.head(10), x='消費次數', y='店家名稱', 
                                         orientation='h', color='消費次數',
                                         color_continuous_scale='Viridis')
                        # 讓座標軸由大到小排
                        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_bar, use_container_width=True)

                # --- 第二區：店家消費金額排行 ---
                st.divider()
                st.write("### 💰 店家貢獻度 (誰賺你最多錢？)")
                shop_money = df.groupby('精簡店家')['數值金額'].sum().sort_values(ascending=False).reset_index()
                shop_money.columns = ['店家名稱', '累計金額']
                
                # 顯示前五名
                top_cols = st.columns(5)
                for i, row in shop_money.head(5).iterrows():
                    with top_cols[i]:
                        st.info(f"**{row['店家名稱']}**\n\n${row['累計金額']:,.0f}")

                # --- 第三區：完整清單 ---
                with st.expander("查看完整明細清單"):
                    st.dataframe(df[['日期', '消費明細', '分類', '金額']], use_container_width=True)

            else:
                st.error("無法解析內容，請確認 PDF 格式。")
    except Exception as e:
        st.error(f"分析出錯：{e}")

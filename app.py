import streamlit as st
from supabase import create_client, Client

# 1. KẾT NỐI (Dùng st.secrets để bảo mật)
@st.cache_resource
def init_connection() -> Client:
    # Nếu chạy local, ông tạo file .streamlit/secrets.toml
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

class DatabaseManager:
    def __init__(self, client: Client):
        self.client = client
        # Thay cái UUID này bằng ID user ông đã tạo trong Supabase Auth
        self.user_id = "c1b89663-eb6a-462c-b55f-9a12dc10596b" 

    def get_balance(self):
        res = self.client.table("transactions").select("amount").eq("user_id", self.user_id).execute()
        return sum(item['amount'] for item in res.data) if res.data else 0

    def get_habits(self):
        res = self.client.table("habits").select("*").eq("user_id", self.user_id).execute()
        return res.data if res.data else []

    def log_habit(self, habit_id: str):
        # CHỈ CẦN INSERT VÀO LOG - TRIGGER TỰ CỘNG TIỀN TRONG DB
        return self.client.table("habit_logs").insert({
            "habit_id": habit_id,
            "status": "done"
        }).execute()

    def add_habit(self, name, goal, reward):
        return self.client.table("habits").insert({
            "user_id": self.user_id,
            "name": name,
            "identity_goal": goal,
            "incentive_amount": reward
        }).execute()

    def get_stats(self):
        res = self.client.table("transactions").select("amount, created_at").eq("user_id", self.user_id).execute()
        return res.data if res.data else []

# 2. GIAO DIỆN
st.set_page_config(page_title="Atomic Finance", page_icon="💜", layout="centered")

# Custom CSS cho "gu" của ông (Màu tím nhẹ và tối giản)
st.markdown("""
    <style>
    .stButton>button { background-color: #6c5ce7; color: white; border-radius: 10px; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

db = DatabaseManager(init_connection())

st.title("💜 Atomic Finance")

# Sidebar hiển thị số dư
with st.sidebar:
    st.metric("Tổng tích lũy", f"{db.get_balance():,.0f} VNĐ")
    st.divider()
    st.caption("Identity Goals:")
    for h in db.get_habits():
        if h['identity_goal']: st.write(f"✨ {h['identity_goal']}")

# Tabs tính năng
tab1, tab2, tab3 = st.tabs(["🔥 Habits", "📈 Stats", "⚙️ Setup"])

with tab1:
    habits = db.get_habits()
    if not habits: st.info("Chưa có thói quen nào.")
    for h in habits:
        col1, col2 = st.columns([3, 1])
        col1.markdown(f"**{h['name']}** \n`+{h['incentive_amount']:,} VNĐ`")
        if col2.button("Xong", key=h['id']):
            db.log_habit(h['id'])
            st.balloons()
            st.rerun()

with tab2:
    data = db.get_stats()
    if data:
        import pandas as pd
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        chart_data = df.groupby('date')['amount'].sum()
        st.bar_chart(chart_data)
    else:
        st.write("Chưa có dữ liệu thống kê.")

with tab3:
    with st.form("new_habit"):
        n = st.text_input("Tên thói quen")
        g = st.text_input("Identity Goal (VD: Tôi là người kỷ luật)")
        r = st.number_input("Tiền thưởng (VNĐ)", min_value=0, step=1000)
        if st.form_submit_button("Thêm mới"):
            db.add_habit(n, g, r)
            st.rerun()
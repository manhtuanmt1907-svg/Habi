import streamlit as st
import pandas as pd
import plotly.express as px # Thêm để vẽ biểu đồ tròn chuyên nghiệp
from supabase import create_client

# 1. KẾT NỐI
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()
USER_ID = "c1b89663-eb6a-462c-b55f-9a12dc10596b"

st.set_page_config(page_title="Atomic Finance Pro", layout="wide")

# Danh mục chi tiêu gợi ý cho sinh viên
EXPENSE_CATS = ["Ăn uống", "Học tập (Sách/Khóa học)", "Đi lại/Gửi xe", "Nhà trọ/Điện nước", "Giải trí", "Sức khỏe", "Khác"]
INCOME_CATS = ["Thưởng Habit", "Bố mẹ chu cấp", "Làm thêm", "Khác"]

tab_habit, tab_finance = st.tabs(["✅ Habit Manager", "💰 Finance Manager"])

# --- [Giữ nguyên Tab Habit Manager từ bản trước] ---
with tab_habit:
    # (Phần code Habit Manager không thay đổi)
    st.subheader("Lộ trình Kỷ luật")
    habits = supabase.table("habits").select("*").eq("user_id", USER_ID).execute().data
    for h in habits:
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(f"**{h['name']}** (+{h['incentive_amount']:,}đ)")
        if col2.button("Xong", key=f"done_{h['id']}"):
            supabase.table("habit_logs").insert({"habit_id": h['id'], "status": "done"}).execute()
            st.rerun()
        if col3.button("🗑️", key=f"del_{h['id']}"):
            supabase.table("habits").delete().eq("id", h['id']).execute()
            st.rerun()

# ==========================================
# TAB 2: FINANCE MANAGER (Nâng cấp Phân loại)
# ==========================================
with tab_finance:
    accounts = supabase.table("accounts").select("*").eq("user_id", USER_ID).execute().data
    
    # 1. Dashboard nhanh
    total_assets = sum([a['balance'] for a in accounts])
    st.metric("Tổng tài sản thực tế", f"{total_assets:,.0f} VNĐ")
    
    col_input, col_report = st.columns([1, 1])
    
    with col_input:
        st.write("### 📝 Ghi chép chi tiêu")
        with st.form("pro_trans_form", clear_on_submit=True):
            acc_choice = st.selectbox("Chọn ví", options=[a['name'] for a in accounts])
            t_type = st.radio("Loại giao dịch", ["Chi tiêu (-)", "Thu nhập (+)"], horizontal=True)
            
            # Tự động đổi danh mục dựa trên loại giao dịch
            cats = EXPENSE_CATS if t_type == "Chi tiêu (-)" else INCOME_CATS
            category = st.selectbox("Phân loại", options=cats)
            
            amount = st.number_input("Số tiền", min_value=0, step=1000)
            note = st.text_input("Ghi chú (Ví dụ: Ăn trưa Canteen C9)")
            
            if st.form_submit_button("Lưu vào sổ"):
                selected_acc = next(a for a in accounts if a['name'] == acc_choice)
                final_amt = -amount if t_type == "Chi tiêu (-)" else amount
                
                # Cập nhật DB
                supabase.table("accounts").update({"balance": float(selected_acc['balance']) + final_amt}).eq("id", selected_acc['id']).execute()
                supabase.table("transactions").insert({
                    "user_id": USER_ID, "account_id": selected_acc['id'], 
                    "amount": amount, "transaction_type": "expense" if t_type == "Chi tiêu (-)" else "income",
                    "category": category, "description": note
                }).execute()
                st.success("Đã ghi nhận!")
                st.rerun()

    with col_report:
        st.write("### 📊 Phân tích chi tiêu tháng này")
        trans_data = supabase.table("transactions").select("*").eq("user_id", USER_ID).eq("transaction_type", "expense").execute().data
        
        if trans_data:
            df = pd.DataFrame(trans_data)
            # Biểu đồ tròn phân bổ chi tiêu
            fig = px.pie(df, values='amount', names='category', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu chi tiêu để báo cáo.")

    # 2. Quản lý ví (Giữ nguyên logic cũ nhưng giao diện gọn hơn)
    with st.expander("🏦 Quản lý ví tiền của tôi"):
        for acc in accounts:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{acc['name']}**: {acc['balance']:,} VNĐ")
            if c2.button("Xóa ví", key=f"del_acc_{acc['id']}"):
                supabase.table("accounts").delete().eq("id", acc['id']).execute()
                st.rerun()
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
# ==========================================
# TAB 1: HABIT MANAGER
# ==========================================
with tab_habit:
    st.subheader("Lộ trình Kỷ luật")
    
    # 1. FORM THÊM THÓI QUEN MỚI
    with st.expander("➕ Thêm thói quen mới", expanded=True): # Mở sẵn
        with st.form("new_habit", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            name = c1.text_input("Tên thói quen (VD: Giải bài tập Giải tích II)")
            reward = c2.number_input("Thưởng (VNĐ)", min_value=0, step=1000)
            if st.form_submit_button("Lưu thói quen"):
                if name:
                    supabase.table("habits").insert({"user_id": USER_ID, "name": name, "incentive_amount": reward}).execute()
                    st.rerun()
                else:
                    st.warning("Ông phải nhập tên thói quen chứ!")

    # 2. DANH SÁCH CHECKLIST
    habits = supabase.table("habits").select("*").eq("user_id", USER_ID).execute().data
    if not habits:
        st.info("Chưa có thói quen nào. Hãy thêm ở form phía trên nhé!")
    else:
        for h in habits:
            col1, col2, col3 = st.columns([4, 2, 1])
            col1.write(f"**{h['name']}** (+{h['incentive_amount']:,}đ)")
            
            if col2.button("Xong", key=f"done_{h['id']}"):
                # Kiểm tra xem hôm nay đã log chưa để tránh lỗi ấn 2 lần
                res = supabase.table("habit_logs").select("*").eq("habit_id", h['id']).eq("log_date", pd.Timestamp.now().date()).execute()
                if not res.data:
                    supabase.table("habit_logs").insert({"habit_id": h['id'], "status": "done"}).execute()
                    st.toast(f"Tốt lắm! Đã cộng thưởng cho {h['name']}")
                    st.rerun()
                else:
                    st.warning("Hôm nay ông đã làm thói quen này rồi!")

            if col3.button("🗑️", key=f"del_{h['id']}"):
                supabase.table("habits").delete().eq("id", h['id']).execute()
                st.rerun()

# ==========================================
# TAB 2: FINANCE MANAGER (Nâng cấp Phân loại)
# ==========================================
# 2. Quản lý & Thêm ví tiền
    # Nếu chưa có ví nào (empty list), tự động mở tung expander này ra
    with st.expander("🏦 Quản lý & Thêm ví tiền", expanded=not bool(accounts)):
        
        # Form tạo ví mới
        st.markdown("**🆕 Tạo ví mới**")
        with st.form("new_wallet", clear_on_submit=True):
            col_w1, col_w2, col_w3 = st.columns([2, 2, 1])
            new_acc_name = col_w1.text_input("Tên ví (VD: Tiền mặt, BIDV)")
            init_bal = col_w2.number_input("Số dư ban đầu", min_value=0, step=1000)
            if col_w3.form_submit_button("Tạo ví"):
                if new_acc_name:
                    supabase.table("accounts").insert({"user_id": USER_ID, "name": new_acc_name, "balance": init_bal}).execute()
                    st.rerun()
                
        st.divider()
        
        # Danh sách ví hiện tại
        st.markdown("**💳 Ví hiện tại của ông**")
        if not accounts:
            st.info("Ông chưa có ví nào. Hãy tạo một cái ở trên để bắt đầu ghi chép nhé.")
        else:
            for acc in accounts:
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{acc['name']}**: {acc['balance']:,} VNĐ")
                if c2.button("Xóa ví", key=f"del_acc_{acc['id']}"):
                    supabase.table("accounts").delete().eq("id", acc['id']).execute()
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
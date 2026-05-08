# ============ التبويب 2: الإخراج ============
with tabs[1]:
    st.subheader("📤 إخراج بضاعة جديدة")
    with st.form("out_form"):
        col1, col2, col3 = st.columns(3)
        homes = [h for h in df['المنزل'].unique() if h not in ["", "-"]]
        products = [p for p in df['المنتج'].unique() if p not in ["", "-"]]
        with col1:
            out_home = st.selectbox("اسم المنزل", options=homes if homes else [""])
        with col2:
            out_product = st.selectbox("اسم المنتج", options=products if products else [""])
        with col3:
            out_qty = st.number_input("الكمية", min_value=1)
        out_status = st.radio("الحالة", ["خياطة (ct)", "انتهاء (fn)"], horizontal=True)
        status_map = {"خياطة (ct)": "ct", "انتهاء (fn)": "fn"}
        if st.form_submit_button("🔔 تسجيل الخروج"):
            if out_qty > 0 and out_product and out_home:
                row = [out_qty, out_product, out_home, datetime.now().strftime("%Y-%m-%d %H:%M"), status_map[out_status]]
                if manager.add_row(row):
                    st.session_state.df = manager.get_data()
                    st.success("✅ تم تسجيل العملية بنجاح!")
                    st.rerun()
            else:
                st.warning("⚠️ يرجى إدخال جميع البيانات")

# ============ التبويب 3: المخزن ============
with tabs[2]:
    st.subheader("📊 رصيد الشركة")
    if not df.empty:
        stock_in = df[df['الحالة'] == 'st'].groupby('المنتج')['الكمية'].sum()
        stock_out = df[df['الحالة'] == 'cl'].groupby('المنتج')['الكمية'].sum()
        stock = stock_in.subtract(stock_out, fill_value=0).reset_index()
        stock.columns = ['المنتج', 'الكمية']
        total = stock['الكمية'].sum()
        st.metric("إجمالي الرصيد", f"{int(total)} قطعة")
        st.dataframe(stock, use_container_width=True)
    else:
        st.info("📭 لا توجد بيانات")

# ============ التبويب 4: كشف الحساب ============
with tabs[3]:
    st.subheader("📈 كشف حساب المنازل")
    if not df.empty:
        summary = df.pivot_table(
            index='المنزل',
            columns='الحالة',
            values='الكمية',
            aggfunc='sum',
            fill_value=0
        )
        st.dataframe(summary, use_container_width=True)
    else:
        st.info("📭 لا توجد بيانات")

# ============ التبويب 5: السجل ============
with tabs[4]:
    st.subheader("📜 سجل المعاملات")
    if not df.empty:
        history = df.iloc[::-1].head(50)
        st.dataframe(history, use_container_width=True)
    else:
        st.info("📭 السجل فارغ")

# ============ التبويب 6: الإنجاز ============
with tabs[5]:
    st.subheader("✅ إنجاز المنازل")
    if not df.empty:
        completed = df.groupby("المنزل").agg(
            عدد_المنتجات=("المنتج", "nunique"),
            مجموع_الكمية=("الكمية", "sum")
        ).reset_index()
        st.dataframe(completed, use_container_width=True)
    else:
        st.info("📭 لا توجد بيانات")

# ============ التذييل ============
st.divider()
st.markdown("""
<div style="text-align: center; padding: 20px; color: #999;">
    <p>🛡️ نظام الرقابة الذكية - Bébé Sympa</p>
    <p>© 2026 جميع الحقوق محفوظة</p>
    <p>تم التطوير بواسطة: <strong>hosinmariya-netizen</strong></p>
</div>
""", unsafe_allow_html=True)

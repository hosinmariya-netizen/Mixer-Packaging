    # --- TAB 5: السجل (History) - تصميم إكسل أفقي تماماً ---
    with tabs[4]:
        st.subheader("📜 سجل العمليات (تصميم أفقي)")
        if not df.empty:
            # ترتيب البيانات: الأحدث أولاً
            history_df = df.iloc[::-1].head(50)
            
            # بناء الجدول باستخدام HTML لضمان العرض الأفقي
            table_html = """
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; direction: rtl; font-family: sans-serif;">
                    <thead>
                        <tr style="background-color: #ffa500; color: black;">
                            <th style="border: 1px solid #444; padding: 10px;">المنزل</th>
                            <th style="border: 1px solid #444; padding: 10px;">المنتج</th>
                            <th style="border: 1px solid #444; padding: 10px;">الحالة</th>
                            <th style="border: 1px solid #444; padding: 10px;">الكمية</th>
                            <th style="border: 1px solid #444; padding: 10px;">التاريخ</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for i, row in history_df.iterrows():
                # تلوين الصفوف متبادل
                bg_color = "#D6C1A6" if i % 2 == 0 else "#1e2124"
                text_color = "black" if i % 2 == 0 else "white"
                status_style = "background-color: #ffa500; font-weight: bold; color: black;" if row['الحالة'] in ['ct', 'fn'] else ""
                
                table_html += f"""
                    <tr style="background-color: {bg_color}; color: {text_color};">
                        <td style="border: 1px solid #444; padding: 8px; text-align: center;">{row['المنزل']}</td>
                        <td style="border: 1px solid #444; padding: 8px; text-align: center;">{row['المنتج']}</td>
                        <td style="border: 1px solid #444; padding: 8px; text-align: center; {status_style}">{row['الحالة']}</td>
                        <td style="border: 1px solid #444; padding: 8px; text-align: center;">{int(row['الكمية'])}</td>
                        <td style="border: 1px solid #444; padding: 8px; text-align: center;">{row['التاريخ']}</td>
                    </tr>
                """
            
            table_html += "</tbody></table></div>"
            
            # عرض الجدول
            st.markdown(table_html, unsafe_allow_html=True)
            
            st.divider()
            st.caption("ملاحظة: لتصفير كمية منزل معين، يرجى استخدام زر 'تسوية' في تبويب 'استلام' أو 'كشف الحساب'.")
            
        else:
            st.info("لا توجد بيانات سجل.")
            

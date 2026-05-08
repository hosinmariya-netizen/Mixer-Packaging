    # --- TAB 5: السجل (HISTORY) بتصميم EXCEL ---
    with tabs[4]:
        st.subheader("📜 سجل المعاملات (Excel Style)")
        if not df.empty:
            history_df = df.iloc[::-1].head(60) # عرض آخر 60 عملية

            # تعريف ستايل الجدول (CSS)
            st.markdown("""
                <style>
                .excel-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 13px;
                    direction: rtl;
                    border: 1px solid #444;
                }
                .excel-table th {
                    background-color: #ffa500;
                    color: black;
                    border: 1px solid #444;
                    padding: 8px;
                    text-align: center;
                }
                .excel-table td {
                    border: 1px solid #444;
                    padding: 4px 8px;
                    text-align: center;
                }
                /* ألوان الصفوف المتبادلة */
                .excel-table tr:nth-child(even) { background-color: #D6C1A6; color: black; }
                .excel-table tr:nth-child(odd) { background-color: #1e2124; color: white; }
                
                .settle-btn-style {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 2px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                }
                </style>
            """, unsafe_allow_html=True)

            # إنشاء رأس الجدول
            cols = st.columns([1.5, 1.5, 1, 1, 2, 1])
            fields = ["المنزل", "المنتج", "الحالة", "الكمية", "التاريخ", "الإجراء"]
            
            # عرض البيانات بطريقة تشبه الخلايا
            for i, row in history_df.iterrows():
                # تحديد لون الصف بناءً على الفردي والزوجي يدويًا لتوافق Streamlit
                bg_color = "#D6C1A6" if i % 2 == 0 else "transparent"
                text_color = "black" if i % 2 == 0 else "white"
                border_style = "1px solid #444"
                
                with st.container():
                    # محاكاة صف الإكسل باستخدام columns مع ستايل مخصص
                    c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.5, 1, 1, 2, 1])
                    
                    # عرض البيانات داخل حاويات ملونة
                    c1.markdown(f'<div style="background:{bg_color}; color:{text_color}; border:{border_style}; padding:5px; text-align:center;">{row["المنزل"]}</div>', unsafe_allow_html=True)
                    c2.markdown(f'<div style="background:{bg_color}; color:{text_color}; border:{border_style}; padding:5px; text-align:center;">{row["المنتج"]}</div>', unsafe_allow_html=True)
                    
                    # تلوين الحالة (CT/FN بلون أورنج)
                    status_bg = "#ffa500" if row['الحالة'] in ['ct', 'fn'] else bg_color
                    c3.markdown(f'<div style="background:{status_bg}; color:black; border:{border_style}; padding:5px; text-align:center; font-weight:bold;">{row["الحالة"]}</div>', unsafe_allow_html=True)
                    
                    c4.markdown(f'<div style="background:{bg_color}; color:{text_color}; border:{border_style}; padding:5px; text-align:center;">{int(row["الكمية"])}</div>', unsafe_allow_html=True)
                    c5.markdown(f'<div style="background:{bg_color}; color:{text_color}; border:{border_style}; padding:5px; text-align:center;">{row["التاريخ"]}</div>', unsafe_allow_html=True)
                    
                    # زر التسوية
                    if row['الحالة'] in ['ct', 'fn'] and row['المنزل'] != "-":
                        if c6.button("تسوية", key=f"exc_set_{i}"):
                            p_data = df[(df['المنزل'] == row['المنزل']) & (df['المنتج'] == row['المنتج'])]
                            actual_rem = p_data[p_data['الحالة'].isin(['ct', 'fn'])]['الكمية'].sum() - p_data[p_data['الحالة'] == 'st']['الكمية'].sum()
                            if actual_rem > 0:
                                append_row([actual_rem, row['المنتج'], row['المنزل'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "st"])
                                st.cache_resource.clear()
                                st.success("✅ تمت التسوية")
                                st.rerun()
                    else:
                        c6.markdown(f'<div style="background:{bg_color}; border:{border_style}; padding:5px; text-align:center;">-</div>', unsafe_allow_html=True)

        else:
            st.info("لا توجد بيانات لعرضها.")
                    

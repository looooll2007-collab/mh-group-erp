with col_chart1:
        st.subheader("الرسم البياني للمالية (إيرادات ومصروفات)")
        if not df_fin.empty:
            # إنشاء الرسم البياني
            fig1 = px.bar(
                df_fin,
                x='التصنيف',
                y='المبلغ',
                color='النوع',
                barmode='group',
                color_discrete_map={'إيراد': '#64ffda', 'مصروف': '#ff007f'}
            )
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=active_theme['text']
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("لا توجد بيانات مالية للعرض حالياً.")

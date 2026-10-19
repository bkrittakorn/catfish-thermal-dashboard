
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


RFD = {
    "Cr": 0.003,
    "Pb": 0.0035,
    "Ni": 0.020,
    "Cd": 0.001,
}

METALS = {
    "Cr": "โครเมียมรวม (Cr)",
    "Pb": "ตะกั่ว (Pb)",
    "Ni": "นิกเกิล (Ni)",
    "Cd": "แคดเมียม (Cd)",
}


def sediment_model(initial, years, input_rate, decay):
    """Illustrative sediment concentration scenario."""
    result = []
    for year in range(years + 1):
        if decay == 0:
            value = initial + input_rate * year
        else:
            value = (
                initial * np.exp(-decay * year)
                + input_rate / decay
                * (1 - np.exp(-decay * year))
            )
        result.append(max(0.0, float(value)))
    return result


def run_aquamonitor():
    st.title("💧 AquaMonitor")
    st.subheader(
        "วิเคราะห์คุณภาพน้ำและความเสี่ยงจากโลหะหนักในปลา"
    )

    st.write(
        "กรอกผลตรวจโลหะหนักในกล้ามเนื้อปลา "
        "เพื่อคำนวณค่าคัดกรอง HQ และ HI "
        "พร้อมดูสถานการณ์จำลอง Cr ในตะกอน"
    )

    st.info(
        "เครื่องมือนี้เป็นการคัดกรองเบื้องต้นและการจำลอง "
        "ไม่ใช่การรับรองความปลอดภัยของอาหาร "
        "กรุณาตรวจสอบค่า RfD และสมการกับเอกสารอ้างอิง "
        "ก่อนใช้ประกอบการตัดสินใจจริง"
    )

    st.markdown("### 1. ผลตรวจโลหะหนักในกล้ามเนื้อปลา")
    st.caption(
        "หน่วย mg/kg น้ำหนักเปียก "
        "เว้นว่างหากไม่มีผลตรวจ ห้ามถือว่าค่าที่ขาดหายเป็นศูนย์"
    )

    c1, c2 = st.columns(2)
    concentrations = {}

    with c1:
        concentrations["Cr"] = st.number_input(
            "โครเมียมรวม Cr (mg/kg)",
            min_value=0.0, value=None,
            step=0.01, format="%.4f",
            key="am_cr"
        )
        concentrations["Ni"] = st.number_input(
            "นิกเกิล Ni (mg/kg)",
            min_value=0.0, value=None,
            step=0.01, format="%.4f",
            key="am_ni"
        )

    with c2:
        concentrations["Pb"] = st.number_input(
            "ตะกั่ว Pb (mg/kg)",
            min_value=0.0, value=None,
            step=0.01, format="%.4f",
            key="am_pb"
        )
        concentrations["Cd"] = st.number_input(
            "แคดเมียม Cd (mg/kg)",
            min_value=0.0, value=None,
            step=0.01, format="%.4f",
            key="am_cd"
        )

    body_weight = st.number_input(
        "น้ำหนักตัวผู้บริโภค (kg)",
        min_value=1.0,
        value=50.0,
        step=1.0,
        key="am_weight"
    )

    st.markdown("### 2. ผลตรวจ Cr ในตะกอน (ไม่บังคับ)")
    sediment_cr = st.number_input(
        "Cr ในตะกอน (mg/kg)",
        min_value=0.0,
        value=None,
        step=0.1,
        format="%.4f",
        key="am_sediment"
    )

    horizon = st.selectbox(
        "ระยะเวลาจำลอง",
        [1, 5, 10],
        index=1,
        format_func=lambda x: f"{x} ปี",
        key="am_horizon"
    )

    if not st.button(
        "🔎 วิเคราะห์ผล",
        type="primary",
        key="am_analyze"
    ):
        st.caption("กรอกผลตรวจ แล้วกดวิเคราะห์ผล")
        return

    measured = {
        k: v for k, v in concentrations.items()
        if v is not None
    }

    if not measured and sediment_cr is None:
        st.error(
            "กรุณากรอกผลตรวจโลหะอย่างน้อยหนึ่งรายการ "
            "หรือกรอกค่า Cr ในตะกอน"
        )
        return

    # HQ screening calculation:
    # concentration × fish consumption / body weight / RfD
    # Assumed fish consumption = 0.0215 kg/day.
    hq = {
        metal: concentration * 0.0215
        / body_weight / RFD[metal]
        for metal, concentration in measured.items()
    }
    hi = sum(hq.values()) if hq else None

    st.divider()
    st.markdown("### 3. สรุปผลการคัดกรอง")

    m1, m2, m3 = st.columns(3)
    m1.metric("จำนวนโลหะที่มีผลตรวจ", f"{len(measured)}/4")
    m2.metric(
        "ดัชนีอันตราย HI",
        f"{hi:.4f}" if hi is not None else "ไม่มีข้อมูล"
    )
    m3.metric(
        "จำนวน HQ ที่เกิน 1",
        str(sum(value > 1 for value in hq.values()))
        if hq else "ไม่มีข้อมูล"
    )

    if hi is not None:
        if hi > 1:
            st.warning(
                "HI มากกว่า 1 ภายใต้สมมติฐานที่ใช้ "
                "ควรให้ผู้เชี่ยวชาญประเมินเพิ่มเติม"
            )
        else:
            st.info(
                "HI ไม่เกิน 1 สำหรับโลหะที่มีผลตรวจ "
                "ผลนี้ไม่ได้ยืนยันว่าปลอดภัย "
                "และไม่ครอบคลุมโลหะที่ไม่มีข้อมูล"
            )

    if measured:
        st.markdown("### 4. กราฟความเข้มข้นโลหะในปลา")

        concentration_df = pd.DataFrame({
            "โลหะ": list(measured.keys()),
            "ความเข้มข้น (mg/kg)": list(measured.values())
        })

        fig1 = px.bar(
            concentration_df,
            x="โลหะ",
            y="ความเข้มข้น (mg/kg)",
            color="โลหะ",
            title="ความเข้มข้นโลหะในกล้ามเนื้อปลา"
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("### 5. กราฟ Hazard Quotient (HQ)")

        hq_df = pd.DataFrame({
            "โลหะ": list(hq.keys()),
            "HQ": list(hq.values())
        })

        fig2 = px.bar(
            hq_df,
            x="โลหะ",
            y="HQ",
            color="โลหะ",
            title="ค่า HQ แยกตามโลหะ"
        )
        fig2.add_hline(
            y=1,
            line_dash="dash",
            line_color="red",
            annotation_text="HQ = 1"
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(
            pd.DataFrame([
                {
                    "โลหะ": metal,
                    "ความเข้มข้น (mg/kg)": measured[metal],
                    "RfD ที่ตั้งไว้": RFD[metal],
                    "HQ": hq[metal],
                }
                for metal in measured
            ]),
            use_container_width=True,
            hide_index=True
        )

    scenario_df = None

    if sediment_cr is not None:
        st.markdown("### 6. สถานการณ์จำลอง Cr ในตะกอน")
        st.caption(
            "เส้นกราฟเป็นสถานการณ์สมมติ ไม่ใช่การพยากรณ์ "
            "และยังไม่ได้สอบเทียบกับข้อมูลเฉพาะพื้นที่"
        )

        # Illustrative parameters adapted from the supplied HTML.
        scenarios = [
            ("A · ไม่แทรกแซง", 1.715, 0.05),
            ("B · ลดแหล่งกำเนิด", 1.715 * 0.85, 0.07),
            ("C · ควบคุมเข้มข้น", 0.0, 0.10),
        ]

        rows = []
        for name, input_rate, decay in scenarios:
            values = sediment_model(
                sediment_cr, horizon, input_rate, decay
            )
            for year, value in enumerate(values):
                rows.append({
                    "ปีที่": year,
                    "สถานการณ์": name,
                    "Cr ในตะกอน (mg/kg)": value
                })

        scenario_df = pd.DataFrame(rows)

        fig3 = px.line(
            scenario_df,
            x="ปีที่",
            y="Cr ในตะกอน (mg/kg)",
            color="สถานการณ์",
            markers=True,
            title="แนวโน้ม Cr ในตะกอนตามสถานการณ์"
        )
        st.plotly_chart(fig3, use_container_width=True)

        final_df = (
            scenario_df[scenario_df["ปีที่"] == horizon]
            .sort_values("สถานการณ์")
        )
        st.markdown(f"**ค่าจำลองเมื่อสิ้นสุดปีที่ {horizon}**")
        st.dataframe(
            final_df,
            use_container_width=True,
            hide_index=True
        )

    st.markdown("### 7. ดาวน์โหลดผลวิเคราะห์")

    export_rows = [
        {
            "รายการ": f"ความเข้มข้น_{metal}",
            "ค่า": value,
            "หน่วย": "mg/kg wet weight"
        }
        for metal, value in measured.items()
    ]

    export_rows += [
        {
            "รายการ": f"HQ_{metal}",
            "ค่า": value,
            "หน่วย": "dimensionless"
        }
        for metal, value in hq.items()
    ]

    export_rows.append({
        "รายการ": "HI",
        "ค่า": hi if hi is not None else "",
        "หน่วย": "dimensionless"
    })

    if scenario_df is not None:
        for _, row in scenario_df.iterrows():
            export_rows.append({
                "รายการ": (
                    f"Cr ตะกอน ปี {row['ปีที่']} "
                    f"({row['สถานการณ์']})"
                ),
                "ค่า": row["Cr ในตะกอน (mg/kg)"],
                "หน่วย": "mg/kg"
            })

    export_df = pd.DataFrame(export_rows)
    st.download_button(
        "⬇️ ดาวน์โหลด CSV",
        data=export_df.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="AquaMonitor_results.csv",
        mime="text/csv",
        key="am_download"
    )

    st.warning(
        "ข้อจำกัด: ค่า HQ/HI ขึ้นอยู่กับอัตราบริโภค "
        "น้ำหนักตัว และค่า RfD ที่ตั้งไว้ "
        "การวัด Cr รวมไม่สามารถใช้ระบุ Cr(VI) ได้ "
        "ผลนี้ไม่ใช่การประเมินความเสี่ยงที่ผ่านการตรวจสอบ "
        "และไม่ใช้แทนข้อกำหนดของหน่วยงานรัฐ"
    )


import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ============================================================
# 1. LANGUAGE SUPPORT
# ============================================================

def tr(en, th):
    """Use the language selected in app.py."""
    language = st.session_state.get("language", "English")
    return th if language == "ไทย" else en


def metal_label(metal):
    """Return the metal label in the selected language."""
    labels_en = {
        "Cr": "Total Chromium (Cr)",
        "Pb": "Lead (Pb)",
        "Ni": "Nickel (Ni)",
        "Cd": "Cadmium (Cd)",
    }

    labels_th = {
        "Cr": "โครเมียมรวม (Cr)",
        "Pb": "ตะกั่ว (Pb)",
        "Ni": "นิกเกิล (Ni)",
        "Cd": "แคดเมียม (Cd)",
    }

    language = st.session_state.get("language", "English")

    if language == "ไทย":
        return labels_th.get(metal, metal)

    return labels_en.get(metal, metal)


# ============================================================
# 2. MODEL PARAMETERS
# ============================================================

RFD = {
    "Cr": 0.003,
    "Pb": 0.0035,
    "Ni": 0.020,
    "Cd": 0.001,
}

FISH_CONSUMPTION_RATE = 0.0215  # kg/day; assumed model input


# ============================================================
# 3. SEDIMENT MODEL
# ============================================================

def sediment_model(initial, years, input_rate, decay):
    """
    Illustrative sediment concentration model.

    This model is hypothetical and is not a site-calibrated forecast.
    Concentrations and rates must be validated before real-world use.
    """
    results = []

    for year in range(years + 1):
        if decay == 0:
            concentration = initial + input_rate * year
        else:
            concentration = (
                initial * np.exp(-decay * year)
                + (input_rate / decay)
                * (1 - np.exp(-decay * year))
            )

        results.append(max(0.0, float(concentration)))

    return results


# ============================================================
# 4. DISPLAY HELPERS
# ============================================================

def show_dataframe(df):
    """Display a dataframe with compatibility across Streamlit versions."""
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )


def make_bar_chart(df, x, y, title, x_title, y_title):
    """Create a bar chart with consistent formatting."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
    )

    fig.update_traces(
        texttemplate="%{y:.4f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        margin=dict(t=65, b=40, l=30, r=25),
    )

    return fig


# ============================================================
# 5. MAIN APPLICATION
# ============================================================

def run_aquamonitor():

    is_thai = st.session_state.get("language", "English") == "ไทย"

    # --------------------------------------------------------
    # Page title and introduction
    # --------------------------------------------------------

    st.title("💧 AquaMonitor")

    st.subheader(
        tr(
            "Water Quality & Heavy Metal Risk Assessment in Fish",
            "การประเมินคุณภาพน้ำและความเสี่ยงจากโลหะหนักในปลา",
        )
    )

    st.write(
        tr(
            "Enter available laboratory measurements from fish muscle "
            "to calculate preliminary Hazard Quotients (HQ) and the "
            "Hazard Index (HI).",
            "กรอกผลตรวจวิเคราะห์จากกล้ามเนื้อปลาเพื่อคำนวณค่า "
            "Hazard Quotient (HQ) และ Hazard Index (HI) "
            "สำหรับการคัดกรองเบื้องต้น",
        )
    )

    st.info(
        tr(
            "This prototype is for preliminary screening and scenario "
            "exploration only. It does not certify food safety. "
            "Verify reference doses, exposure assumptions, units, and "
            "calculation methods against appropriate scientific sources "
            "before using results for decisions.",
            "เครื่องมือต้นแบบนี้ใช้สำหรับการคัดกรองเบื้องต้นและการสำรวจ "
            "สถานการณ์เท่านั้น ไม่ใช่การรับรองความปลอดภัยของอาหาร "
            "ควรตรวจสอบค่าอ้างอิงความเป็นพิษ สมมติฐานการรับสัมผัส หน่วย "
            "และวิธีคำนวณกับแหล่งข้อมูลทางวิชาการที่เหมาะสมก่อนนำผลไปใช้",
        )
    )

    # --------------------------------------------------------
    # Section 1: Fish muscle measurements
    # --------------------------------------------------------

    st.header(
        tr(
            "1. Heavy Metal Concentrations in Fish Muscle",
            "1. ความเข้มข้นโลหะหนักในกล้ามเนื้อปลา",
        )
    )

    st.caption(
        tr(
            "Unit: mg/kg wet weight. Select the metals for which "
            "measurements are available. Unmeasured metals are excluded "
            "from the calculations, not treated as zero.",
            "หน่วย: mg/kg น้ำหนักเปียก เลือกเฉพาะโลหะที่มีผลตรวจวัด "
            "โลหะที่ไม่มีผลตรวจจะไม่ถูกนำมาคำนวณและจะไม่ถือว่ามีค่าเป็นศูนย์",
        )
    )

    col_left, col_right = st.columns(2)

    # Initialize measurement availability flags.
    # These flags prevent blank measurements from being confused with zero.
    with col_left:
        has_cr = st.checkbox(
            tr("Cr measurement available", "มีผลตรวจโครเมียม (Cr)"),
            key="am_has_cr",
        )

        cr = None

        if has_cr:
            cr = st.number_input(
                tr("Total Chromium, Cr (mg/kg)", "โครเมียมรวม Cr (mg/kg)"),
                min_value=0.0,
                value=0.0,
                step=0.001,
                format="%.4f",
                key="am_cr",
            )

        has_ni = st.checkbox(
            tr("Ni measurement available", "มีผลตรวจนิกเกิล (Ni)"),
            key="am_has_ni",
        )

        ni = None

        if has_ni:
            ni = st.number_input(
                tr("Nickel, Ni (mg/kg)", "นิกเกิล Ni (mg/kg)"),
                min_value=0.0,
                value=0.0,
                step=0.001,
                format="%.4f",
                key="am_ni",
            )

    with col_right:
        has_pb = st.checkbox(
            tr("Pb measurement available", "มีผลตรวจตะกั่ว (Pb)"),
            key="am_has_pb",
        )

        pb = None

        if has_pb:
            pb = st.number_input(
                tr("Lead, Pb (mg/kg)", "ตะกั่ว Pb (mg/kg)"),
                min_value=0.0,
                value=0.0,
                step=0.001,
                format="%.4f",
                key="am_pb",
            )

        has_cd = st.checkbox(
            tr("Cd measurement available", "มีผลตรวจแคดเมียม (Cd)"),
            key="am_has_cd",
        )

        cd = None

        if has_cd:
            cd = st.number_input(
                tr("Cadmium, Cd (mg/kg)", "แคดเมียม Cd (mg/kg)"),
                min_value=0.0,
                value=0.0,
                step=0.001,
                format="%.4f",
                key="am_cd",
            )

    # --------------------------------------------------------
    # Section 2: Exposure assumptions
    # --------------------------------------------------------

    st.header(
        tr(
            "2. Exposure Assumptions",
            "2. สมมติฐานการรับสัมผัส",
        )
    )

    body_weight = st.number_input(
        tr("Consumer body weight (kg)", "น้ำหนักตัวผู้บริโภค (kg)"),
        min_value=1.0,
        value=50.0,
        step=1.0,
        key="am_weight",
    )

    st.caption(
        tr(
            f"Assumed daily fish consumption: "
            f"{FISH_CONSUMPTION_RATE:.4f} kg/day.",
            f"ปริมาณการบริโภคปลาต่อวันที่สมมติ: "
            f"{FISH_CONSUMPTION_RATE:.4f} kg/day",
        )
    )

    # --------------------------------------------------------
    # Section 3: Optional sediment scenario
    # --------------------------------------------------------

    st.header(
        tr(
            "3. Optional Sediment Chromium Scenario",
            "3. สถานการณ์โครเมียมในตะกอน (ไม่บังคับ)",
        )
    )

    use_sediment = st.checkbox(
        tr(
            "Enable sediment scenario analysis",
            "เปิดใช้การวิเคราะห์สถานการณ์โครเมียมในตะกอน",
        ),
        key="am_has_sediment",
    )

    sediment_cr = None

    if use_sediment:
        sediment_cr = st.number_input(
            tr(
                "Initial sediment chromium concentration (mg/kg)",
                "ความเข้มข้นโครเมียมเริ่มต้นในตะกอน (mg/kg)",
            ),
            min_value=0.0,
            value=0.0,
            step=0.01,
            format="%.4f",
            key="am_sediment",
        )

        horizon = st.selectbox(
            tr("Simulation period", "ระยะเวลาจำลอง"),
            options=[1, 5, 10],
            index=1,
            format_func=lambda year: tr(
                f"{year} years",
                f"{year} ปี",
            ),
            key="am_horizon",
        )
    else:
        horizon = 5

    # --------------------------------------------------------
    # Analysis button
    # --------------------------------------------------------

    st.divider()

    analyze = st.button(
        tr("Analyze Results", "วิเคราะห์ผล"),
        type="primary",
        key="am_analyze",
        use_container_width=True,
    )

    if not analyze:
        st.caption(
            tr(
                "Select the available measurements and click Analyze "
                "Results to calculate the screening indicators.",
                "เลือกข้อมูลที่มีผลตรวจ แล้วกดปุ่มวิเคราะห์ผล "
                "เพื่อคำนวณตัวชี้วัดการคัดกรอง",
            )
        )
        return

    # --------------------------------------------------------
    # Validate inputs
    # --------------------------------------------------------

    measured = {
        "Cr": cr,
        "Pb": pb,
        "Ni": ni,
        "Cd": cd,
    }

    measured = {
        metal: float(value)
        for metal, value in measured.items()
        if value is not None
    }

    has_sediment_data = sediment_cr is not None

    if not measured and not has_sediment_data:
        st.error(
            tr(
                "No measurements selected. Select at least one measured "
                "metal or enable the sediment scenario.",
                "ยังไม่มีข้อมูล โปรดเลือกโลหะที่มีผลตรวจอย่างน้อยหนึ่งรายการ "
                "หรือเปิดใช้การวิเคราะห์ตะกอน",
            )
        )
        return

    if body_weight <= 0:
        st.error(
            tr(
                "Body weight must be greater than zero.",
                "น้ำหนักตัวต้องมากกว่าศูนย์",
            )
        )
        return

    # --------------------------------------------------------
    # Calculate HQ and HI
    # --------------------------------------------------------

    hq = {}

    for metal, concentration in measured.items():
        hq[metal] = (
            concentration
            * FISH_CONSUMPTION_RATE
            / body_weight
            / RFD[metal]
        )

    hi = sum(hq.values()) if hq else None

    # --------------------------------------------------------
    # Section 4: Screening summary
    # --------------------------------------------------------

    st.header(
        tr(
            "4. Screening Summary",
            "4. สรุปผลการคัดกรอง",
        )
    )

    metric1, metric2, metric3 = st.columns(3)

    metric1.metric(
        tr("Metals measured", "จำนวนโลหะที่มีผลตรวจ"),
        len(measured),
    )

    metric2.metric(
        tr("Hazard Index (HI)", "ดัชนีความเป็นอันตราย (HI)"),
        f"{hi:.4f}" if hi is not None else "N/A",
    )

    above_one = sum(value > 1 for value in hq.values())

    metric3.metric(
        tr("HQ values above 1", "จำนวนค่า HQ ที่มากกว่า 1"),
        above_one,
    )

    if hi is not None and hi > 1:
        st.warning(
            tr(
                "The calculated HI exceeds 1 under the selected "
                "assumptions. This is a screening signal, not proof of "
                "harm. Seek qualified toxicological risk assessment.",
                "ค่า HI มากกว่า 1 ภายใต้สมมติฐานที่เลือก เป็นสัญญาณ "
                "สำหรับการคัดกรอง ไม่ใช่หลักฐานยืนยันว่าจะเกิดอันตราย "
                "ควรให้ผู้เชี่ยวชาญประเมินความเสี่ยงทางพิษวิทยา",
            )
        )

    elif hi is not None:
        st.info(
            tr(
                "The calculated HI is at or below 1 under the selected "
                "assumptions. This does not establish that the fish is "
                "safe. Results depend on exposure assumptions, reference "
                "doses, and the metals measured.",
                "ค่า HI ไม่เกิน 1 ภายใต้สมมติฐานที่เลือก แต่ไม่ได้ยืนยัน "
                "ว่าปลอดภัย ผลขึ้นอยู่กับสมมติฐานการรับสัมผัส "
                "ค่าอ้างอิงความเป็นพิษ และโลหะที่ตรวจวัด",
            )
        )

    if not measured:
        st.info(
            tr(
                "No fish-muscle metal measurements were provided. "
                "HQ and HI were not calculated.",
                "ไม่มีผลตรวจโลหะหนักในกล้ามเนื้อปลา จึงไม่ได้คำนวณ HQ และ HI",
            )
        )

    # --------------------------------------------------------
    # Section 5: Concentration chart
    # --------------------------------------------------------

    if measured:
        st.header(
            tr(
                "5. Heavy Metal Concentrations",
                "5. ความเข้มข้นโลหะหนัก",
            )
        )

        concentration_df = pd.DataFrame(
            [
                {
                    "Metal": metal_label(metal),
                    "Concentration (mg/kg)": concentration,
                }
                for metal, concentration in measured.items()
            ]
        )

        fig_conc = make_bar_chart(
            concentration_df,
            x="Metal",
            y="Concentration (mg/kg)",
            title=tr(
                "Measured concentrations in fish muscle",
                "ความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
            ),
            x_title=tr("Metal", "โลหะ"),
            y_title=tr(
                "Concentration (mg/kg)",
                "ความเข้มข้น (mg/kg)",
            ),
        )

        st.plotly_chart(
            fig_conc,
            use_container_width=True,
        )

        # ----------------------------------------------------
        # Section 6: HQ chart and results table
        # ----------------------------------------------------

        st.header(
            tr(
                "6. Hazard Quotient (HQ)",
                "6. ค่าดัชนีอันตรายรายสาร (HQ)",
            )
        )

        hq_df = pd.DataFrame(
            [
                {
                    "Metal": metal_label(metal),
                    "HQ": value,
                }
                for metal, value in hq.items()
            ]
        )

        fig_hq = make_bar_chart(
            hq_df,
            x="Metal",
            y="HQ",
            title=tr(
                "Screening Hazard Quotient by metal",
                "ค่า HQ สำหรับการคัดกรองแยกตามโลหะ",
            ),
            x_title=tr("Metal", "โลหะ"),
            y_title="HQ",
        )

        fig_hq.add_hline(
            y=1,
            line_dash="dash",
            annotation_text="HQ = 1",
        )

        st.plotly_chart(
            fig_hq,
            use_container_width=True,
        )

        results_df = pd.DataFrame(
            [
                {
                    "Metal": metal_label(metal),
                    "Concentration (mg/kg)": measured[metal],
                    "Assumed RfD": RFD[metal],
                    "HQ": hq[metal],
                }
                for metal in measured
            ]
        )

        st.subheader(
            tr(
                "Screening Results Table",
                "ตารางผลการคัดกรอง",
            )
        )

        formatted_results = results_df.copy()

        for column in [
            "Concentration (mg/kg)",
            "Assumed RfD",
            "HQ",
        ]:
            formatted_results[column] = formatted_results[column].map(
                lambda value: f"{value:.4f}"
            )

        show_dataframe(formatted_results)

    # --------------------------------------------------------
    # Section 7: Sediment scenario analysis
    # --------------------------------------------------------

    sediment_scenarios_df = None

    if has_sediment_data:
        st.header(
            tr(
                "7. Sediment Chromium Scenario Analysis",
                "7. การวิเคราะห์สถานการณ์โครเมียมในตะกอน",
            )
        )

        st.warning(
            tr(
                "These are hypothetical scenarios, not validated "
                "environmental forecasts. The parameters should be "
                "calibrated using site-specific measurements.",
                "สถานการณ์เหล่านี้เป็นการจำลองสมมติ ไม่ใช่การพยากรณ์ "
                "สิ่งแวดล้อมที่ผ่านการตรวจสอบ พารามิเตอร์ควรปรับเทียบ "
                "ด้วยข้อมูลตรวจวัดจากพื้นที่จริง",
            )
        )

        scenarios = [
            {
                "id": "A",
                "name": tr(
                    "A - No Intervention",
                    "A - ไม่ดำเนินมาตรการ",
                ),
                "input_rate": float(sediment_cr),
                "decay": 0.05,
            },
            {
                "id": "B",
                "name": tr(
                    "B - Source Reduction",
                    "B - ลดแหล่งกำเนิด",
                ),
                "input_rate": float(sediment_cr) * 0.85,
                "decay": 0.07,
            },
            {
                "id": "C",
                "name": tr(
                    "C - Intensive Control",
                    "C - ควบคุมเข้มข้น",
                ),
                "input_rate": 0.0,
                "decay": 0.10,
            },
        ]

        scenario_records = []

        for scenario in scenarios:
            values = sediment_model(
                initial=float(sediment_cr),
                years=int(horizon),
                input_rate=scenario["input_rate"],
                decay=scenario["decay"],
            )

            for year, concentration in enumerate(values):
                scenario_records.append(
                    {
                        "Scenario": scenario["name"],
                        "Year": year,
                        "Sediment chromium (mg/kg)": concentration,
                    }
                )

        sediment_scenarios_df = pd.DataFrame(scenario_records)

        fig_sediment = px.line(
            sediment_scenarios_df,
            x="Year",
            y="Sediment chromium (mg/kg)",
            color="Scenario",
            markers=True,
            title=tr(
                "Illustrative sediment chromium scenarios",
                "สถานการณ์จำลองโครเมียมในตะกอน",
            ),
        )

        fig_sediment.update_layout(
            xaxis_title=tr("Year", "ปี"),
            yaxis_title=tr(
                "Sediment chromium (mg/kg)",
                "โครเมียมในตะกอน (mg/kg)",
            ),
        )

        st.plotly_chart(
            fig_sediment,
            use_container_width=True,
        )

        final_year_df = sediment_scenarios_df[
            sediment_scenarios_df["Year"] == int(horizon)
        ].copy()

        st.subheader(
            tr(
                f"Scenario summary at year {horizon}",
                f"สรุปสถานการณ์ในปีที่ {horizon}",
            )
        )

        final_display = final_year_df.copy()

        final_display["Sediment chromium (mg/kg)"] = (
            final_display["Sediment chromium (mg/kg)"].map(
                lambda value: f"{value:.4f}"
            )
        )

        show_dataframe(final_display)

    # --------------------------------------------------------
    # Section 8: Export results
    # --------------------------------------------------------

    st.header(
        tr(
            "8. Export Results",
            "8. ส่งออกผลลัพธ์",
        )
    )

    export_rows = []

    for metal, concentration in measured.items():
        export_rows.append(
            {
                "Record type": "Fish muscle concentration",
                "Metal": metal,
                "Concentration (mg/kg)": concentration,
                "Assumed RfD": RFD[metal],
                "HQ": hq[metal],
                "HI": hi,
                "Body weight (kg)": body_weight,
                "Assumed fish consumption (kg/day)": (
                    FISH_CONSUMPTION_RATE
                ),
                "Sediment scenario": "",
                "Year": np.nan,
                "Sediment chromium (mg/kg)": np.nan,
            }
        )

    if sediment_scenarios_df is not None:
        for _, row in sediment_scenarios_df.iterrows():
            export_rows.append(
                {
                    "Record type": "Sediment scenario",
                    "Metal": "Cr",
                    "Concentration (mg/kg)": np.nan,
                    "Assumed RfD": np.nan,
                    "HQ": np.nan,
                    "HI": np.nan,
                    "Body weight (kg)": body_weight,
                    "Assumed fish consumption (kg/day)": (
                        FISH_CONSUMPTION_RATE
                    ),
                    "Sediment scenario": row["Scenario"],
                    "Year": int(row["Year"]),
                    "Sediment chromium (mg/kg)": (
                        row["Sediment chromium (mg/kg)"]
                    ),
                }
            )

    if not export_rows:
        export_rows.append(
            {
                "Record type": "Summary",
                "Metal": "",
                "Concentration (mg/kg)": np.nan,
                "Assumed RfD": np.nan,
                "HQ": np.nan,
                "HI": hi if hi is not None else np.nan,
                "Body weight (kg)": body_weight,
                "Assumed fish consumption (kg/day)": (
                    FISH_CONSUMPTION_RATE
                ),
                "Sediment scenario": "",
                "Year": np.nan,
                "Sediment chromium (mg/kg)": np.nan,
            }
        )

    export_df = pd.DataFrame(export_rows)

    st.download_button(
        label=tr(
            "Download Results (CSV)",
            "ดาวน์โหลดผลลัพธ์ (CSV)",
        ),
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="AquaMonitor_results.csv",
        mime="text/csv",
        key="am_download",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # Section 9: Limitations
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        tr(
            "Important Limitations",
            "ข้อจำกัดสำคัญ",
        )
    )

    st.warning(
        tr(
            "HQ and HI depend on the assumed exposure rate, body weight, "
            "reference doses, units, and calculation method. The reference "
            "doses in this prototype must be independently verified for "
            "the intended exposure pathway. Summing HQ values is a screening "
            "approach and may not account for all toxicological interactions. "
            "Total chromium does not distinguish Cr(VI) from other chromium "
            "species. The sediment model is hypothetical and is not validated "
            "for a specific site. This tool does not replace applicable "
            "standards, laboratory quality assurance, or professional "
            "risk assessment.",
            "ค่า HQ และ HI ขึ้นอยู่กับอัตราการรับสัมผัส น้ำหนักตัว "
            "ค่าอ้างอิงความเป็นพิษ หน่วย และวิธีคำนวณ ค่าอ้างอิงความเป็นพิษ "
            "ในต้นแบบนี้ต้องได้รับการตรวจสอบอย่างอิสระให้เหมาะสมกับช่องทาง "
            "การรับสัมผัสที่ต้องการศึกษา การรวมค่า HQ เป็น HI เป็นวิธีคัดกรอง "
            "และอาจไม่ครอบคลุมปฏิสัมพันธ์ทางพิษวิทยาทั้งหมด การตรวจโครเมียมรวม "
            "ไม่สามารถแยก Cr(VI) ออกจากรูปแบบอื่นได้ แบบจำลองตะกอนเป็นสถานการณ์ "
            "สมมติและยังไม่ได้ตรวจสอบสำหรับพื้นที่เฉพาะ เครื่องมือนี้ไม่สามารถ "
            "ใช้แทนมาตรฐานที่เกี่ยวข้อง การประกันคุณภาพห้องปฏิบัติการ "
            "หรือการประเมินความเสี่ยงโดยผู้เชี่ยวชาญได้",
        )
    )

    st.caption(
        tr(
            "AquaMonitor | Preliminary screening and scenario exploration only.",
            "AquaMonitor | ใช้สำหรับการคัดกรองเบื้องต้นและสำรวจสถานการณ์เท่านั้น",
        )
    )

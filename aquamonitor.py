
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ============================================================
# 1. LANGUAGE HELPER
# ============================================================
def tr(en, th):
    """Translate interface text using the language selected in app.py."""
    return th if st.session_state.get("language", "English") == "ไทย" else en


# ============================================================
# 2. REFERENCE DOSES AND METALS
# ============================================================
RFD = {
    "Cr": 0.003,
    "Pb": 0.0035,
    "Ni": 0.020,
    "Cd": 0.001,
}

METALS = {
    "Cr": "Total Chromium (Cr)",
    "Pb": "Lead (Pb)",
    "Ni": "Nickel (Ni)",
    "Cd": "Cadmium (Cd)",
}

METAL_LABELS_TH = {
    "Cr": "โครเมียมรวม (Cr)",
    "Pb": "ตะกั่ว (Pb)",
    "Ni": "นิกเกิล (Ni)",
    "Cd": "แคดเมียม (Cd)",
}

# Assumed daily fish consumption in kg/day.
# This is a model assumption and should be verified before real use.
FISH_CONSUMPTION_RATE = 0.0215


def metal_label(metal):
    """Return the metal name in the currently selected language."""
    if st.session_state.get("language", "English") == "ไทย":
        return METAL_LABELS_TH.get(metal, metal)
    return METALS.get(metal, metal)


# ============================================================
# 3. SEDIMENT MODEL
# ============================================================
def sediment_model(initial, years, input_rate, decay):
    """
    Illustrative sediment concentration scenario.

    Parameters
    ----------
    initial : float
        Initial concentration.
    years : int
        Number of years to simulate.
    input_rate : float
        Illustrative annual input rate.
    decay : float
        Illustrative decay coefficient.

    Returns
    -------
    list[float]
        Concentration for year 0 through the selected final year.
    """
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


# ============================================================
# 4. MAIN AQUAMONITOR INTERFACE
# ============================================================
def run_aquamonitor():

    is_thai = st.session_state.get("language", "English") == "ไทย"

    # --------------------------------------------------------
    # Page introduction
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
            "Enter measured heavy metal concentrations in fish muscle "
            "to calculate screening-level Hazard Quotients (HQ) "
            "and the Hazard Index (HI).",
            "กรอกค่าความเข้มข้นโลหะหนักที่ตรวจวัดได้ในกล้ามเนื้อปลา "
            "เพื่อคำนวณค่าคัดกรอง HQ และดัชนีความเป็นอันตราย HI",
        )
    )

    st.info(
        tr(
            "This tool is intended for preliminary screening and scenario "
            "exploration only. It does not certify food safety. Verify the "
            "reference doses (RfDs), exposure assumptions, units, and "
            "calculation methods against appropriate scientific sources "
            "before using the results for real-world decisions.",
            "เครื่องมือนี้ใช้สำหรับการคัดกรองเบื้องต้นและการสำรวจสถานการณ์เท่านั้น "
            "ไม่ใช่การรับรองความปลอดภัยของอาหาร ควรตรวจสอบค่าอ้างอิงความเป็นพิษ "
            "(RfD) สมมติฐานการรับสัมผัส หน่วย และวิธีคำนวณกับแหล่งข้อมูลทางวิชาการ "
            "ที่เหมาะสมก่อนนำผลไปใช้ประกอบการตัดสินใจจริง",
        )
    )

    # --------------------------------------------------------
    # Section 1: Fish muscle heavy metal concentrations
    # --------------------------------------------------------
    st.header(
        tr(
            "1. Heavy Metal Concentrations in Fish Muscle",
            "1. ความเข้มข้นโลหะหนักในกล้ามเนื้อปลา",
        )
    )

    st.caption(
        tr(
            "Unit: mg/kg wet weight. Leave a field blank if no measurement "
            "is available. Missing measurements are not treated as zero.",
            "หน่วย: mg/kg น้ำหนักเปียก เว้นช่องว่างหากไม่มีผลตรวจวัด "
            "ข้อมูลที่ไม่มีจะไม่ถูกนับเป็นศูนย์",
        )
    )

    left_col, right_col = st.columns(2)

    with left_col:
        cr = st.number_input(
            tr("Total Chromium, Cr (mg/kg)", "โครเมียมรวม Cr (mg/kg)"),
            min_value=0.0,
            value=None,
            step=0.001,
            format="%.4f",
            key="am_cr",
            help=tr(
                "Enter the measured concentration in fish muscle.",
                "กรอกค่าความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
            ),
        )

        ni = st.number_input(
            tr("Nickel, Ni (mg/kg)", "นิกเกิล Ni (mg/kg)"),
            min_value=0.0,
            value=None,
            step=0.001,
            format="%.4f",
            key="am_ni",
            help=tr(
                "Enter the measured concentration in fish muscle.",
                "กรอกค่าความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
            ),
        )

    with right_col:
        pb = st.number_input(
            tr("Lead, Pb (mg/kg)", "ตะกั่ว Pb (mg/kg)"),
            min_value=0.0,
            value=None,
            step=0.001,
            format="%.4f",
            key="am_pb",
            help=tr(
                "Enter the measured concentration in fish muscle.",
                "กรอกค่าความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
            ),
        )

        cd = st.number_input(
            tr("Cadmium, Cd (mg/kg)", "แคดเมียม Cd (mg/kg)"),
            min_value=0.0,
            value=None,
            step=0.001,
            format="%.4f",
            key="am_cd",
            help=tr(
                "Enter the measured concentration in fish muscle.",
                "กรอกค่าความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
            ),
        )

    st.subheader(
        tr("Exposure assumptions", "สมมติฐานการรับสัมผัส")
    )

    body_weight = st.number_input(
        tr("Consumer body weight (kg)", "น้ำหนักตัวผู้บริโภค (kg)"),
        min_value=1.0,
        value=50.0,
        step=1.0,
        key="am_weight",
        help=tr(
            "Body weight is used in the screening calculation.",
            "น้ำหนักตัวใช้ในการคำนวณเพื่อการคัดกรอง",
        ),
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
    # Section 2: Optional sediment scenario
    # --------------------------------------------------------
    st.header(
        tr(
            "2. Optional Sediment Chromium Scenario",
            "2. สถานการณ์โครเมียมในตะกอน (ไม่บังคับ)",
        )
    )

    st.write(
        tr(
            "Optionally enter an initial sediment chromium concentration "
            "to explore hypothetical future scenarios.",
            "หากมีข้อมูล สามารถกรอกความเข้มข้นโครเมียมเริ่มต้นในตะกอน "
            "เพื่อสำรวจสถานการณ์ในอนาคตที่สมมติขึ้นได้",
        )
    )

    sediment_cr = st.number_input(
        tr(
            "Initial sediment chromium concentration (mg/kg)",
            "ความเข้มข้นโครเมียมเริ่มต้นในตะกอน (mg/kg)",
        ),
        min_value=0.0,
        value=None,
        step=0.01,
        format="%.4f",
        key="am_sediment",
    )

    horizon = st.selectbox(
        tr("Simulation period", "ระยะเวลาจำลอง"),
        options=[1, 5, 10],
        index=1,
        format_func=lambda x: tr(f"{x} years", f"{x} ปี"),
        key="am_horizon",
    )

    # --------------------------------------------------------
    # Analysis button
    # --------------------------------------------------------
    analyze = st.button(
        tr("Analyze Results", "วิเคราะห์ผล"),
        type="primary",
        key="am_analyze",
    )

    if not analyze:
        st.caption(
            tr(
                "Enter available measurements and select Analyze Results "
                "to calculate screening indicators.",
                "กรอกข้อมูลที่มี แล้วกดปุ่มวิเคราะห์ผลเพื่อคำนวณตัวชี้วัดการคัดกรอง",
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
        metal: value
        for metal, value in measured.items()
        if value is not None
    }

    has_sediment = sediment_cr is not None

    if not measured and not has_sediment:
        st.error(
            tr(
                "No data entered. Enter at least one measured metal "
                "concentration or a sediment chromium concentration.",
                "ยังไม่มีข้อมูล โปรดกรอกความเข้มข้นโลหะหนักอย่างน้อยหนึ่งรายการ "
                "หรือกรอกความเข้มข้นโครเมียมในตะกอน",
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
    # Section 3: Screening summary
    # --------------------------------------------------------
    st.header(
        tr("3. Screening Summary", "3. สรุปผลการคัดกรอง")
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        tr("Metals with measurements", "จำนวนโลหะที่มีผลตรวจวัด"),
        f"{len(measured)}",
    )

    c2.metric(
        tr("Hazard Index (HI)", "ดัชนีความเป็นอันตราย (HI)"),
        f"{hi:.4f}" if hi is not None else "N/A",
    )

    above_one = sum(value > 1 for value in hq.values())

    c3.metric(
        tr("HQ values above 1", "จำนวนค่า HQ ที่มากกว่า 1"),
        f"{above_one}",
    )

    if hi is not None and hi > 1:
        st.warning(
            tr(
                "The calculated HI exceeds 1 under the selected assumptions. "
                "This is a screening signal, not proof of harm. Seek a "
                "qualified exposure and toxicological risk assessment.",
                "ค่า HI ที่คำนวณได้มากกว่า 1 ภายใต้สมมติฐานที่เลือก "
                "เป็นสัญญาณสำหรับการคัดกรอง ไม่ใช่หลักฐานยืนยันว่าจะเกิดอันตราย "
                "ควรให้ผู้เชี่ยวชาญประเมินการรับสัมผัสและความเสี่ยงทางพิษวิทยา",
            )
        )
    elif hi is not None:
        st.info(
            tr(
                "The calculated HI is at or below 1 under the selected "
                "assumptions. This does not establish that the fish is safe. "
                "The result depends on the assumed exposure rate, reference "
                "doses, and the metals measured.",
                "ค่า HI ที่คำนวณได้ไม่เกิน 1 ภายใต้สมมติฐานที่เลือก "
                "แต่ไม่ได้ยืนยันว่าปลอดภัย ผลขึ้นอยู่กับอัตราการรับสัมผัส "
                "ค่าอ้างอิงความเป็นพิษ และชนิดโลหะที่ตรวจวัด",
            )
        )

    if not measured:
        st.info(
            tr(
                "No fish-muscle metal concentrations were provided. "
                "HQ and HI were not calculated.",
                "ไม่มีข้อมูลความเข้มข้นโลหะหนักในกล้ามเนื้อปลา "
                "จึงไม่ได้คำนวณ HQ และ HI",
            )
        )

    # --------------------------------------------------------
    # Section 4: Concentration chart
    # --------------------------------------------------------
    if measured:
        st.header(
            tr(
                "4. Heavy Metal Concentrations",
                "4. ความเข้มข้นโลหะหนัก",
            )
        )

        concentration_df = pd.DataFrame(
            [
                {
                    "Metal": metal_label(metal),
                    "Concentration (mg/kg)": float(value),
                }
                for metal, value in measured.items()
            ]
        )

        fig_conc = px.bar(
            concentration_df,
            x="Metal",
            y="Concentration (mg/kg)",
            title=tr(
                "Measured concentrations in fish muscle",
                "ความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
            ),
            text_auto=".4f",
        )

        fig_conc.update_layout(
            xaxis_title=tr("Metal", "โลหะ"),
            yaxis_title=tr("Concentration (mg/kg)", "ความเข้มข้น (mg/kg)"),
        )

        st.plotly_chart(
            fig_conc,
            use_container_width=True,
        )

        # ----------------------------------------------------
        # Section 5: HQ chart and results table
        # ----------------------------------------------------
        st.header(
            tr(
                "5. Hazard Quotient (HQ)",
                "5. ค่าดัชนีอันตรายรายสาร (HQ)",
            )
        )

        hq_df = pd.DataFrame(
            [
                {
                    "Metal": metal_label(metal),
                    "HQ": float(value),
                }
                for metal, value in hq.items()
            ]
        )

        fig_hq = px.bar(
            hq_df,
            x="Metal",
            y="HQ",
            title=tr(
                "Screening Hazard Quotient by metal",
                "ค่า HQ สำหรับการคัดกรองแยกตามโลหะ",
            ),
            text_auto=".4f",
        )

        fig_hq.add_hline(
            y=1,
            line_dash="dash",
            annotation_text="HQ = 1",
        )

        fig_hq.update_layout(
            xaxis_title=tr("Metal", "โลหะ"),
            yaxis_title="HQ",
        )

        st.plotly_chart(
            fig_hq,
            use_container_width=True,
        )

        results_df = pd.DataFrame(
            [
                {
                    "Metal": metal,
                    "Concentration (mg/kg)": float(measured[metal]),
                    "Assumed RfD": float(RFD[metal]),
                    "HQ": float(hq[metal]),
                }
                for metal in measured
            ]
        )

        st.subheader(
            tr("Screening results table", "ตารางผลการคัดกรอง")
        )

        display_df = results_df.copy()

        display_df["Metal"] = display_df["Metal"].map(metal_label)

        st.dataframe(
            display_df.style.format(
                {
                    "Concentration (mg/kg)": "{:.4f}",
                    "Assumed RfD": "{:.4f}",
                    "HQ": "{:.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------------
    # Section 6: Sediment scenario analysis
    # --------------------------------------------------------
    sediment_scenarios_df = None

    if has_sediment:
        st.header(
            tr(
                "6. Sediment Chromium Scenario Analysis",
                "6. การวิเคราะห์สถานการณ์โครเมียมในตะกอน",
            )
        )

        st.write(
            tr(
                "The following scenarios are hypothetical illustrations. "
                "Their input and decay parameters are assumptions and should "
                "not be interpreted as site-calibrated forecasts.",
                "สถานการณ์ต่อไปนี้เป็นตัวอย่างสมมติ พารามิเตอร์อัตราการเพิ่ม "
                "และการสลายตัวเป็นสมมติฐาน ไม่ใช่การพยากรณ์ที่ปรับเทียบ "
                "กับพื้นที่จริง",
            )
        )

        scenarios = [
            (
                "A - No Intervention",
                tr("A - No Intervention", "A - ไม่ดำเนินมาตรการ"),
                float(sediment_cr),
                0.05,
            ),
            (
                "B - Source Reduction",
                tr("B - Source Reduction", "B - ลดแหล่งกำเนิด"),
                float(sediment_cr) * 0.85,
                0.07,
            ),
            (
                "C - Intensive Control",
                tr("C - Intensive Control", "C - ควบคุมเข้มข้น"),
                0.0,
                0.10,
            ),
        ]

        scenario_records = []

        for scenario_id, scenario_name, input_rate, decay in scenarios:
            values = sediment_model(
                initial=float(sediment_cr),
                years=int(horizon),
                input_rate=input_rate,
                decay=decay,
            )

            for year, concentration in enumerate(values):
                scenario_records.append(
                    {
                        "Scenario": scenario_name,
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
                "สถานการณ์โครเมียมในตะกอนโดยประมาณ",
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

        st.dataframe(
            final_year_df.style.format(
                {
                    "Sediment chromium (mg/kg)": "{:.4f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------------
    # Section 7: CSV export
    # --------------------------------------------------------
    st.header(
        tr("7. Export Results", "7. ส่งออกผลลัพธ์")
    )

    export_rows = []

    for metal in measured:
        export_rows.append(
            {
                "Record type": "Fish muscle concentration",
                "Metal": metal,
                "Concentration (mg/kg)": float(measured[metal]),
                "Assumed RfD": float(RFD[metal]),
                "HQ": float(hq[metal]),
                "HI": float(hi) if hi is not None else np.nan,
                "Body weight (kg)": float(body_weight),
                "Assumed fish consumption (kg/day)": float(
                    FISH_CONSUMPTION_RATE
                ),
                "Sediment scenario": "",
                "Year": np.nan,
                "Sediment chromium (mg/kg)": np.nan,
            }
        )

    if has_sediment and sediment_scenarios_df is not None:
        for _, row in sediment_scenarios_df.iterrows():
            export_rows.append(
                {
                    "Record type": "Sediment scenario",
                    "Metal": "Cr",
                    "Concentration (mg/kg)": np.nan,
                    "Assumed RfD": np.nan,
                    "HQ": np.nan,
                    "HI": np.nan,
                    "Body weight (kg)": float(body_weight),
                    "Assumed fish consumption (kg/day)": float(
                        FISH_CONSUMPTION_RATE
                    ),
                    "Sediment scenario": row["Scenario"],
                    "Year": int(row["Year"]),
                    "Sediment chromium (mg/kg)": float(
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
                "HI": float(hi) if hi is not None else np.nan,
                "Body weight (kg)": float(body_weight),
                "Assumed fish consumption (kg/day)": float(
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
    )

    # --------------------------------------------------------
    # Important limitations
    # --------------------------------------------------------
    st.divider()

    st.subheader(
        tr("Important limitations", "ข้อจำกัดสำคัญ")
    )

    st.warning(
        tr(
            "HQ and HI depend on the assumed exposure rate, body weight, "
            "reference doses, units, and calculation method. These "
            "assumptions require independent toxicological review. Total "
            "chromium measurements do not distinguish Cr(VI) from other "
            "chromium species. The sediment model is hypothetical and "
            "has not been validated for a specific site. This prototype "
            "does not replace applicable government standards, laboratory "
            "quality assurance, or professional risk assessment.",
            "ค่า HQ และ HI ขึ้นอยู่กับอัตราการรับสัมผัส น้ำหนักตัว "
            "ค่าอ้างอิงความเป็นพิษ หน่วย และวิธีคำนวณ ซึ่งควรได้รับการทบทวน "
            "โดยผู้เชี่ยวชาญด้านพิษวิทยา การตรวจวัดโครเมียมรวมไม่สามารถแยก "
            "Cr(VI) ออกจากรูปแบบอื่นของโครเมียมได้ แบบจำลองตะกอนเป็นสถานการณ์สมมติ "
            "และยังไม่ได้รับการตรวจสอบสำหรับพื้นที่เฉพาะ เครื่องมือต้นแบบนี้ "
            "ไม่สามารถใช้แทนมาตรฐานภาครัฐ การประกันคุณภาพห้องปฏิบัติการ "
            "หรือการประเมินความเสี่ยงโดยผู้เชี่ยวชาญได้",
        )
    )

    st.caption(
        tr(
            "AquaMonitor | Preliminary screening and scenario exploration only.",
            "AquaMonitor | ใช้สำหรับการคัดกรองเบื้องต้นและสำรวจสถานการณ์เท่านั้น",
        )
    )

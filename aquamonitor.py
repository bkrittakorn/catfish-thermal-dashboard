
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
    "Cr": "Total Chromium (Cr)",
    "Pb": "Lead (Pb)",
    "Ni": "Nickel (Ni)",
    "Cd": "Cadmium (Cd)",
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
    st.title("AquaMonitor")

    st.subheader(
        "Water Quality & Heavy Metal Risk Assessment in Fish"
    )

    st.write(
        "Enter measured heavy metal concentrations in fish muscle "
        "to calculate screening-level Hazard Quotients (HQ) and the "
        "Hazard Index (HI). You can also explore illustrative "
        "sediment chromium (Cr) scenarios."
    )

    st.info(
        "This tool is intended for preliminary screening and scenario "
        "exploration only. It does not certify food safety. Verify the "
        "reference doses (RfDs), exposure assumptions, units, and "
        "calculation methods against appropriate scientific sources "
        "before using the results for real-world decisions."
    )

    # 1. Fish muscle concentrations
    st.markdown("### 1. Heavy Metal Concentrations in Fish Muscle")

    st.caption(
        "Unit: mg/kg wet weight. Leave a field blank if no measurement "
        "is available. Missing measurements are not treated as zero."
    )

    c1, c2 = st.columns(2)
    concentrations = {}

    with c1:
        concentrations["Cr"] = st.number_input(
            "Total Chromium, Cr (mg/kg)",
            min_value=0.0,
            value=None,
            step=0.01,
            format="%.4f",
            key="am_cr"
        )

        concentrations["Ni"] = st.number_input(
            "Nickel, Ni (mg/kg)",
            min_value=0.0,
            value=None,
            step=0.01,
            format="%.4f",
            key="am_ni"
        )

    with c2:
        concentrations["Pb"] = st.number_input(
            "Lead, Pb (mg/kg)",
            min_value=0.0,
            value=None,
            step=0.01,
            format="%.4f",
            key="am_pb"
        )

        concentrations["Cd"] = st.number_input(
            "Cadmium, Cd (mg/kg)",
            min_value=0.0,
            value=None,
            step=0.01,
            format="%.4f",
            key="am_cd"
        )

    body_weight = st.number_input(
        "Consumer Body Weight (kg)",
        min_value=1.0,
        value=50.0,
        step=1.0,
        key="am_weight"
    )

    # 2. Optional sediment data
    st.markdown("### 2. Sediment Chromium (Optional)")

    sediment_cr = st.number_input(
        "Sediment Chromium, Cr (mg/kg)",
        min_value=0.0,
        value=None,
        step=0.1,
        format="%.4f",
        key="am_sediment"
    )

    horizon = st.selectbox(
        "Simulation Period",
        [1, 5, 10],
        index=1,
        format_func=lambda x: f"{x} years",
        key="am_horizon"
    )

    if not st.button(
        "Analyze Results",
        type="primary",
        key="am_analyze"
    ):
        st.caption("Enter measurements and click Analyze Results.")
        return

    measured = {
        k: v
        for k, v in concentrations.items()
        if v is not None
    }

    if not measured and sediment_cr is None:
        st.error(
            "Enter at least one measured metal concentration "
            "or provide a sediment chromium value."
        )
        return

    # Screening calculation retained from the original implementation.
    # Assumed fish consumption rate = 0.0215 kg/day.
    hq = {
        metal: concentration * 0.0215
        / body_weight / RFD[metal]
        for metal, concentration in measured.items()
    }

    hi = sum(hq.values()) if hq else None

    # 3. Screening summary
    st.divider()
    st.markdown("### 3. Screening Summary")

    m1, m2, m3 = st.columns(3)

    m1.metric(
        "Metals with Measurements",
        f"{len(measured)}/4"
    )

    m2.metric(
        "Hazard Index (HI)",
        f"{hi:.4f}" if hi is not None else "No data"
    )

    m3.metric(
        "Number of HQ Values Above 1",
        str(sum(value > 1 for value in hq.values()))
        if hq else "No data"
    )

    if hi is not None:
        if hi > 1:
            st.warning(
                "The calculated HI exceeds 1 under the assumptions "
                "used. Further assessment by a qualified risk "
                "assessment professional is recommended."
            )
        else:
            st.info(
                "The calculated HI is at or below 1 for the metals "
                "measured. This does not establish that the fish is "
                "safe to consume and does not account for metals "
                "with missing measurements."
            )

    # 4. Concentration chart
    if measured:
        st.markdown("### 4. Heavy Metal Concentrations")

        concentration_df = pd.DataFrame({
            "Metal": [
                METALS[metal] for metal in measured.keys()
            ],
            "Concentration (mg/kg)": list(measured.values())
        })

        fig1 = px.bar(
            concentration_df,
            x="Metal",
            y="Concentration (mg/kg)",
            color="Metal",
            title="Heavy Metal Concentrations in Fish Muscle"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

        # 5. HQ chart
        st.markdown("### 5. Hazard Quotient (HQ)")

        hq_df = pd.DataFrame({
            "Metal": [
                METALS[metal] for metal in hq.keys()
            ],
            "HQ": list(hq.values())
        })

        fig2 = px.bar(
            hq_df,
            x="Metal",
            y="HQ",
            color="Metal",
            title="Hazard Quotient by Metal"
        )

        fig2.add_hline(
            y=1,
            line_dash="dash",
            line_color="red",
            annotation_text="HQ = 1"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

        results_df = pd.DataFrame([
            {
                "Metal": METALS[metal],
                "Concentration (mg/kg)": measured[metal],
                "Assumed RfD": RFD[metal],
                "HQ": hq[metal],
            }
            for metal in measured
        ])

        st.markdown("#### Screening Results by Metal")

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True
        )

    # 6. Sediment scenario
    scenario_df = None

    if sediment_cr is not None:
        st.markdown("### 6. Sediment Chromium Scenario Analysis")

        st.caption(
            "These curves represent hypothetical scenarios, not "
            "forecasts. The parameters have not been calibrated "
            "against site-specific monitoring data."
        )

        scenarios = [
            ("A - No Intervention", 1.715, 0.05),
            ("B - Source Reduction", 1.715 * 0.85, 0.07),
            ("C - Intensive Control", 0.0, 0.10),
        ]

        rows = []

        for name, input_rate, decay in scenarios:
            values = sediment_model(
                sediment_cr,
                horizon,
                input_rate,
                decay
            )

            for year, value in enumerate(values):
                rows.append({
                    "Year": year,
                    "Scenario": name,
                    "Sediment Cr (mg/kg)": value
                })

        scenario_df = pd.DataFrame(rows)

        fig3 = px.line(
            scenario_df,
            x="Year",
            y="Sediment Cr (mg/kg)",
            color="Scenario",
            markers=True,
            title="Projected Sediment Chromium Under Illustrative Scenarios"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )

        final_df = (
            scenario_df[
                scenario_df["Year"] == horizon
            ]
            .sort_values("Scenario")
        )

        st.markdown(
            f"**Simulated Values at the End of Year {horizon}**"
        )

        st.dataframe(
            final_df,
            use_container_width=True,
            hide_index=True
        )

    # 7. Export results
    st.markdown("### 7. Export Results")

    export_rows = [
        {
            "Item": f"Concentration_{metal}",
            "Value": value,
            "Unit": "mg/kg wet weight"
        }
        for metal, value in measured.items()
    ]

    export_rows += [
        {
            "Item": f"HQ_{metal}",
            "Value": value,
            "Unit": "dimensionless"
        }
        for metal, value in hq.items()
    ]

    export_rows.append({
        "Item": "HI",
        "Value": hi if hi is not None else "",
        "Unit": "dimensionless"
    })

    if scenario_df is not None:
        for _, row in scenario_df.iterrows():
            export_rows.append({
                "Item": (
                    f"Sediment_Cr_Year_{row['Year']}_"
                    f"{row['Scenario']}"
                ),
                "Value": row["Sediment Cr (mg/kg)"],
                "Unit": "mg/kg"
            })

    export_df = pd.DataFrame(export_rows)

    st.download_button(
        "Download Results (CSV)",
        data=export_df.to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="AquaMonitor_results.csv",
        mime="text/csv",
        key="am_download"
    )

    # Limitations
    st.warning(
        "Limitations: HQ and HI depend on the assumed exposure rate, "
        "body weight, reference doses, and calculation method. The "
        "current calculation should be independently reviewed for "
        "dimensional consistency and toxicological validity before "
        "interpretation. Total chromium measurements cannot distinguish "
        "Cr(VI) from other chromium species. This prototype is not a "
        "validated risk assessment and does not replace applicable "
        "government standards or expert advice."
    )

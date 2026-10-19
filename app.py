
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Catfish Thermal Risk Dashboard",
    page_icon="🐟",
    layout="wide"
)

st.title("🐟 Catfish Thermal Risk Dashboard")
st.caption("Thermal effects, hatchery economics and climate scenarios")

# Reference data from Supplementary File S1
REFERENCE = pd.DataFrame({
    "Temperature (°C)": [29.0, 32.0],
    "Fertilization rate": [0.677, 0.590],
    "Hatching rate": [0.434, 0.266],
    "Survival rate to 72 h": [0.449, 0.000],
})

def biological_rates(temp):
    """Illustrative interpolation between the two supplied observations."""
    fert = np.interp(
        temp, REFERENCE["Temperature (°C)"],
        REFERENCE["Fertilization rate"]
    )
    hatch = np.interp(
        temp, REFERENCE["Temperature (°C)"],
        REFERENCE["Hatching rate"]
    )
    survival = np.interp(
        temp, REFERENCE["Temperature (°C)"],
        REFERENCE["Survival rate to 72 h"]
    )
    return float(fert), float(hatch), float(survival)

st.sidebar.header("Dashboard navigation")
page = st.sidebar.radio(
    "Choose a page",
    [
        "Overview",
        "Hatchery Calculator",
        "Climate Simulation",
        "Sensitivity Analysis",
        "Methods"
    ]
)

st.sidebar.divider()
st.sidebar.header("Hatchery assumptions")

eggs = st.sidebar.number_input(
    "Initial eggs", min_value=1, value=5_000_000, step=100_000
)
fry_price = st.sidebar.number_input(
    "Price per fry (THB)", min_value=0.0, value=1.50, step=0.10
)
base_cost = st.sidebar.number_input(
    "Base operating cost (THB)", min_value=0.0,
    value=100_000.0, step=5_000.0
)
cooling_cost = st.sidebar.number_input(
    "Cooling cost (THB)", min_value=0.0,
    value=80_000.0, step=5_000.0
)

if page == "Overview":
    st.subheader("Overview")
    temp = st.slider("Water temperature (°C)", 25.0, 36.0, 29.0, 0.5)
    fert, hatch, survival = biological_rates(temp)

    survivors = eggs * fert * hatch * survival
    revenue = survivors * fry_price
    cost = base_cost + cooling_cost

    a, b, c, d = st.columns(4)
    a.metric("Fertilization", f"{fert:.1%}")
    b.metric("Hatching", f"{hatch:.1%}")
    c.metric("Estimated survivors", f"{survivors:,.0f}")
    d.metric("Illustrative net result", f"฿{revenue - cost:,.0f}")

    st.info(
        "Rates at temperatures outside the two observations are illustrative "
        "and should not be interpreted as validated biological predictions."
    )

elif page == "Hatchery Calculator":
    st.subheader("Hatchery Calculator")
    temp = st.slider("Water temperature (°C)", 25.0, 36.0, 29.0, 0.5)
    fert, hatch, survival = biological_rates(temp)

    fertilized = eggs * fert
    hatched = fertilized * hatch
    survivors = hatched * survival
    revenue = survivors * fry_price
    total_cost = base_cost + cooling_cost

    results = pd.DataFrame({
        "Stage": ["Initial eggs", "Estimated fertilized", "Estimated hatched",
                  "Estimated survivors"],
        "Count": [eggs, fertilized, hatched, survivors]
    })
    st.plotly_chart(
        px.bar(results, x="Stage", y="Count", text_auto=".3s"),
        use_container_width=True
    )

    x, y, z = st.columns(3)
    x.metric("Estimated revenue", f"฿{revenue:,.0f}")
    y.metric("Total costs", f"฿{total_cost:,.0f}")
    z.metric("Illustrative net result", f"฿{revenue - total_cost:,.0f}")

elif page == "Climate Simulation":
    st.subheader("Climate Simulation")
    st.write(
        "Explore how hypothetical temperature changes may affect biological "
        "rates and hatchery outcomes. This is a scenario tool, not a climate forecast."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        start_temp = st.slider(
            "Starting temperature (°C)", 25.0, 34.0, 29.0, 0.5
        )
    with c2:
        warming = st.slider(
            "Hypothetical warming (°C/year)", 0.0, 0.20, 0.03, 0.01
        )
    with c3:
        years = st.slider("Projection period (years)", 1, 20, 10)

    st.markdown("### Annual scenario")
    annual = pd.DataFrame({"Year": np.arange(0, years + 1)})
    annual["Temperature (°C)"] = start_temp + annual["Year"] * warming

    rates = annual["Temperature (°C)"].apply(biological_rates)
    annual["Fertilization"] = [r[0] for r in rates]
    annual["Hatching"] = [r[1] for r in rates]
    annual["Survival to 72 h"] = [r[2] for r in rates]
    annual["Estimated survivors"] = (
        eggs * annual["Fertilization"] * annual["Hatching"]
        * annual["Survival to 72 h"]
    )

    st.plotly_chart(
        px.line(
            annual, x="Year", y="Temperature (°C)",
            markers=True, title="Hypothetical temperature trajectory"
        ),
        use_container_width=True
    )

    rate_data = annual.melt(
        id_vars="Year",
        value_vars=["Fertilization", "Hatching", "Survival to 72 h"],
        var_name="Biological indicator",
        value_name="Rate"
    )
    st.plotly_chart(
        px.line(
            rate_data, x="Year", y="Rate",
            color="Biological indicator", markers=True,
            title="Illustrative biological rates over time"
        ).update_yaxes(tickformat=".0%", range=[0, 1]),
        use_container_width=True
    )

    st.plotly_chart(
        px.line(
            annual, x="Year", y="Estimated survivors",
            markers=True, title="Estimated survivors by scenario year"
        ),
        use_container_width=True
    )

    st.markdown("### Monte Carlo temperature uncertainty")
    st.write(
        "Random temperature anomalies are simulated around the final scenario "
        "temperature. The anomaly spread is user-selected for exploration."
    )

    mc1, mc2 = st.columns(2)
    with mc1:
        sd = st.slider(
            "Temperature anomaly standard deviation (°C)",
            0.0, 2.0, 0.5, 0.1
        )
    with mc2:
        simulations = st.selectbox(
            "Number of simulations", [1000, 5000, 10000], index=1
        )

    seed = st.number_input(
        "Random seed (for reproducibility)",
        min_value=0, max_value=999999, value=42, step=1
    )

    rng = np.random.default_rng(int(seed))
    final_temp = float(annual["Temperature (°C)"].iloc[-1])
    simulated_temps = rng.normal(final_temp, sd, int(simulations))
    simulated_temps = np.clip(simulated_temps, 25.0, 36.0)

    sim_rates = [biological_rates(t) for t in simulated_temps]
    sim_survivors = np.array([
        eggs * f * h * s for f, h, s in sim_rates
    ])

    mc_df = pd.DataFrame({
        "Simulated temperature (°C)": simulated_temps,
        "Estimated survivors": sim_survivors
    })

    q05, q50, q95 = np.percentile(sim_survivors, [5, 50, 95])
    m1, m2, m3 = st.columns(3)
    m1.metric("5th percentile survivors", f"{q05:,.0f}")
    m2.metric("Median survivors", f"{q50:,.0f}")
    m3.metric("95th percentile survivors", f"{q95:,.0f}")

    st.plotly_chart(
        px.histogram(
            mc_df, x="Estimated survivors", nbins=40,
            title="Monte Carlo distribution of estimated survivors"
        ),
        use_container_width=True
    )

    st.download_button(
        "Download annual scenario CSV",
        data=annual.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_climate_scenario.csv",
        mime="text/csv"
    )
    st.download_button(
        "Download Monte Carlo CSV",
        data=mc_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_monte_carlo.csv",
        mime="text/csv"
    )

    st.warning(
        "Important limitation: the supplied observations are only at 29°C and "
        "32°C. This demo uses interpolation between those values and holds the "
        "rates constant outside that interval. The warming rate and random "
        "anomaly distribution are user-defined assumptions, not local climate "
        "projections. Monte Carlo results represent uncertainty under these "
        "assumptions, not validated probabilities of farm outcomes."
    )


elif page == "Sensitivity Analysis":
    st.subheader("Sensitivity Analysis")
    st.write(
        "Explore how changes in key assumptions affect estimated survivors "
        "and the illustrative net financial result."
    )

    st.markdown("### Set baseline assumptions")
    s1, s2 = st.columns(2)

    with s1:
        base_temp = st.slider(
            "Baseline temperature (°C)", 25.0, 36.0, 29.0, 0.5
        )
        temp_range = st.slider(
            "Temperature change range (°C)",
            -3.0, 3.0, (-2.0, 2.0), 0.5
        )
        base_eggs = st.number_input(
            "Eggs for analysis", min_value=1,
            value=5_000_000, step=100_000, key="sens_eggs"
        )

    with s2:
        price = st.number_input(
            "Price per fry (THB)", min_value=0.0,
            value=1.50, step=0.10, key="sens_price"
        )
        operating = st.number_input(
            "Operating cost (THB)", min_value=0.0,
            value=100_000.0, step=5_000.0, key="sens_cost"
        )
        cooling = st.number_input(
            "Cooling cost (THB)", min_value=0.0,
            value=80_000.0, step=5_000.0, key="sens_cooling"
        )

    def calculate_scenario(temp):
        f, h, s = biological_rates(temp)
        survivors = base_eggs * f * h * s
        revenue = survivors * price
        net = revenue - operating - cooling
        return survivors, revenue, net

    baseline_survivors, baseline_revenue, baseline_net = (
        calculate_scenario(base_temp)
    )

    delta_temps = np.linspace(
        temp_range[0], temp_range[1], 31
    )

    sens_rows = []
    for delta in delta_temps:
        t = base_temp + delta
        survivors, revenue, net = calculate_scenario(t)
        sens_rows.append({
            "Temperature change (°C)": delta,
            "Scenario temperature (°C)": t,
            "Estimated survivors": survivors,
            "Revenue (THB)": revenue,
            "Net result (THB)": net
        })

    sens_df = pd.DataFrame(sens_rows)

    st.markdown("### Effect of temperature change")
    st.plotly_chart(
        px.line(
            sens_df,
            x="Temperature change (°C)",
            y="Estimated survivors",
            markers=True,
            title="Estimated survivors across temperature scenarios"
        ),
        use_container_width=True
    )

    st.plotly_chart(
        px.line(
            sens_df,
            x="Temperature change (°C)",
            y="Net result (THB)",
            markers=True,
            title="Illustrative net financial result across scenarios"
        ),
        use_container_width=True
    )

    st.markdown("### Scenario results")
    st.dataframe(
        sens_df.style.format({
            "Temperature change (°C)": "{:+.1f}",
            "Scenario temperature (°C)": "{:.1f}",
            "Estimated survivors": "{:,.0f}",
            "Revenue (THB)": "฿{:,.0f}",
            "Net result (THB)": "฿{:,.0f}"
        }),
        use_container_width=True
    )

    st.download_button(
        "Download sensitivity results (CSV)",
        data=sens_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_sensitivity_analysis.csv",
        mime="text/csv"
    )

    st.info(
        "This sensitivity analysis varies temperature while holding the other "
        "inputs fixed. It does not establish causal effects or biological "
        "uncertainty. Results depend on the illustrative interpolation model."
    )


elif page == "Methods":
    st.subheader("Methods and limitations")
    st.markdown("""
    **Reference observations**

    - At 29°C: fertilization 67.7%, hatching 43.4%, survival to 72 h 44.9%.
    - At 32°C: fertilization 59.0%, hatching 26.6%, survival to 72 h 0%.

    **Current prototype**

    - Uses linear interpolation between the two observed temperatures.
    - Holds rates constant outside the observed temperature interval.
    - Uses hypothetical warming and normally distributed temperature anomalies
      in the Monte Carlo exploration.
    - Calculates survivors as initial eggs × fertilization rate × hatching rate
      × survival rate.

    **Not yet implemented**

    - The original seasonal temperature cycle and Q10 assumptions.
    - Calibrated local climate projections.
    - Confidence intervals fitted to experimental biological data.
    - Independent validation of the biological and economic model.
    """)

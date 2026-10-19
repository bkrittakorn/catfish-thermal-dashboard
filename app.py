
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

REFERENCE = {
    "Temperature (°C)": [29, 32],
    "Fertilization rate": [0.677, 0.590],
    "Hatching rate": [0.434, 0.266],
    "Survival rate to 72 h": [0.449, 0.0],
}

st.set_page_config(
    page_title="Catfish Thermal Risk Dashboard",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #F4F8FA;
    }

    [data-testid="stSidebar"] {
        background-color: #E8F1F4;
        border-right: 1px solid #D4E2E8;
    }

    h1 {
        color: #123B4A;
        font-weight: 750;
        letter-spacing: -0.5px;
    }

    h2, h3 {
        color: #205B68;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #DCE7EC;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(20, 60, 75, 0.05);
    }

    div[data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
        border: 1px solid #DCE7EC;
        border-radius: 12px;
        padding: 10px;
    }

    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)



st.title("🐟 Catfish Thermal Risk Dashboard")
st.caption(
    "THERMAL RISK • HATCHERY PERFORMANCE • CLIMATE SCENARIOS"
)

st.markdown(
    "Interactive decision-support prototype for hybrid catfish hatchery research."
)
st.divider()

# Supplementary File S1: reproducible scenario parameters
SEED = 20260929
N_MONTE_CARLO = 10000

TMEAN = 28.5
AMP0 = 3.5
DPEAK = 115
ALPHA = 0.08
BETA = 0.03
E_SD = 0.30

TOPT = 29.0
SIGMA = 1.0
SMAX = 44.9

TCRIT0 = 30.75
DELTA_G = 0.15

def seasonal_temperature(day, year_index):
    """Seasonal temperature scenario from Supplementary File S1."""
    return (
        TMEAN
        + ALPHA * year_index
        + (AMP0 + BETA * year_index)
        * np.cos(2 * np.pi * (day - DPEAK) / 365.0)
    )

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
        "Reproducible seasonal and multiyear temperature scenarios "
        "based on Supplementary File S1. These are illustrative scenarios, "
        "not calibrated local climate forecasts."
    )

    # Parameters from Supplementary File S1
    TMEAN = 28.5
    AMP0 = 3.5
    DPEAK = 115
    ALPHA = 0.08
    BETA = 0.03
    E_SD = 0.30
    TOPT = 29.0
    SIGMA = 1.0
    SMAX = 44.9
    TCRIT0 = 30.75
    DELTA_G = 0.15
    SEED = 20260929
    N_MONTE_CARLO = 10000

    # Scenario controls
    c1, c2 = st.columns(2)
    with c1:
        anomaly_sd = st.slider(
            "Annual temperature anomaly SD (°C)",
            min_value=0.0,
            max_value=1.0,
            value=float(E_SD),
            step=0.05,
            help="S1 default: 0.30°C. One anomaly is shared by all days in each year."
        )
    with c2:
        delta_g = st.slider(
            "Hypothetical threshold change Δg (°C/year)",
            min_value=0.10,
            max_value=0.20,
            value=float(DELTA_G),
            step=0.01,
            help="Sensitivity assumption, not a measured evolutionary rate."
        )

    seed = st.number_input(
        "Random seed",
        min_value=0,
        max_value=99999999,
        value=int(SEED),
        step=1
    )

    # Panel A: seasonal cycle for a representative year
    day = np.arange(1, 366)
    temp_day = (
        TMEAN
        + AMP0 * np.cos(2 * np.pi * (day - DPEAK) / 365.0)
    )
    survival_pct = SMAX * np.exp(
        -0.5 * ((temp_day - TOPT) / SIGMA) ** 2
    )

    seasonal_df = pd.DataFrame({
        "Day of year": day,
        "Water temperature (°C)": temp_day,
        "72-h larval survival (%)": survival_pct
    })

    st.markdown("### A. Annual seasonal vulnerability cycle")
    st.caption(
        "The survival curve is the illustrative Gaussian response specified "
        "in S1; it is not the same as the observed fertilization or hatching rates."
    )

    st.plotly_chart(
        px.line(
            seasonal_df,
            x="Day of year",
            y="Water temperature (°C)",
            title="Seasonal water temperature scenario"
        ),
        use_container_width=True
    )

    st.plotly_chart(
        px.line(
            seasonal_df,
            x="Day of year",
            y="72-h larval survival (%)",
            title="Illustrative temperature-dependent 72-h survival"
        ).update_yaxes(range=[0, 50]),
        use_container_width=True
    )

    # Panel B: multiyear climate scenario
    years = np.arange(2026, 2037)
    year_index = np.arange(len(years))
    n_days = len(years) * 365

    time_year = 2026 + np.arange(n_days) / 365.0
    yindex = np.minimum(np.arange(n_days) // 365, len(years) - 1)
    doy = (np.arange(n_days) % 365) + 1

    base_temp = (
        TMEAN
        + ALPHA * yindex
        + (AMP0 + BETA * yindex)
        * np.cos(2 * np.pi * (doy - DPEAK) / 365.0)
    )

    # One random anomaly per year and simulation, shared across that year's days
    rng = np.random.default_rng(int(seed))
    anomalies = rng.normal(
        0.0, anomaly_sd, size=(N_MONTE_CARLO, len(years))
    )

    q025 = np.quantile(anomalies, 0.025, axis=0)
    q975 = np.quantile(anomalies, 0.975, axis=0)

    mean_temp = base_temp
    lower_temp = base_temp + q025[yindex]
    upper_temp = base_temp + q975[yindex]

    tcrit_static = np.full(n_days, TCRIT0)
    tcrit_scenario = TCRIT0 + delta_g * (time_year - 2026)

    climate_df = pd.DataFrame({
        "Year": time_year,
        "Mean scenario temperature (°C)": mean_temp,
        "Lower 95% simulation interval (°C)": lower_temp,
        "Upper 95% simulation interval (°C)": upper_temp,
        "Static threshold (°C)": tcrit_static,
        "Hypothetical changing threshold (°C)": tcrit_scenario
    })

    st.markdown("### B. Multiyear stochastic climate scenario")
    st.caption(
        "The shaded band is the 2.5th–97.5th percentile of annual anomalies "
        "from 10,000 simulations. It represents uncertainty under the chosen "
        "model assumptions, not a validated climate projection."
    )

    fig = px.line(
        climate_df,
        x="Year",
        y="Mean scenario temperature (°C)",
        title="Illustrative 2026–2036 temperature scenario"
    )
    fig.add_scatter(
        x=climate_df["Year"],
        y=climate_df["Upper 95% simulation interval (°C)"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip"
    )
    fig.add_scatter(
        x=climate_df["Year"],
        y=climate_df["Lower 95% simulation interval (°C)"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        name="95% simulation interval",
        hoverinfo="skip"
    )
    fig.add_scatter(
        x=climate_df["Year"],
        y=climate_df["Static threshold (°C)"],
        mode="lines",
        name="Static threshold"
    )
    fig.add_scatter(
        x=climate_df["Year"],
        y=climate_df["Hypothetical changing threshold (°C)"],
        mode="lines",
        name="Hypothetical changing threshold"
    )
    fig.update_layout(
        xaxis_title="Projection year",
        yaxis_title="Water temperature (°C)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Annual summary of the seasonal model and Monte Carlo interval
    annual_df = pd.DataFrame({
        "Year": years,
        "Mean annual temperature baseline (°C)": [
            TMEAN + ALPHA * i for i in year_index
        ],
        "Seasonal amplitude (°C)": [
            AMP0 + BETA * i for i in year_index
        ],
        "Annual anomaly lower 95% (°C)": q025,
        "Annual anomaly upper 95% (°C)": q975,
        "Static threshold (°C)": TCRIT0,
        "Hypothetical changing threshold (°C)": (
            TCRIT0 + delta_g * year_index
        )
    })

    st.markdown("### Annual scenario data")
    st.dataframe(annual_df, use_container_width=True)

    st.download_button(
        "Download annual climate scenario CSV",
        data=annual_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_climate_scenario_s1.csv",
        mime="text/csv"
    )

    st.download_button(
        "Download daily seasonal scenario CSV",
        data=seasonal_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_seasonal_scenario_s1.csv",
        mime="text/csv"
    )

    st.download_button(
        "Download multiyear daily simulation CSV",
        data=climate_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_multiyear_climate_s1.csv",
        mime="text/csv"
    )

    st.warning(
        "Limitations: the seasonal temperatures, annual warming trend, "
        "anomaly distribution, and changing threshold are scenario assumptions "
        "from Supplementary File S1. They are not locally calibrated forecasts. "
        "The survival curve is an illustrative equation and must not be "
        "interpreted as a validated prediction of farm-level survival."
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


import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Catfish Thermal Risk Dashboard",
    page_icon="🐟",
    layout="wide"
)

st.title("🐟 Catfish Thermal Risk Dashboard")
st.caption("Interactive hatchery and thermal-risk assessment")

st.sidebar.header("Model settings")

temperature = st.sidebar.slider(
    "Water temperature (°C)", 25.0, 36.0, 29.0, 0.5
)
eggs = st.sidebar.number_input(
    "Initial number of eggs", min_value=1, value=5_000_000, step=100_000
)
egg_price = st.sidebar.number_input(
    "Price per fry (THB)", min_value=0.0, value=1.50, step=0.10
)
base_cost = st.sidebar.number_input(
    "Base operating cost (THB)", min_value=0.0, value=100_000.0, step=5_000.0
)
cooling_cost = st.sidebar.number_input(
    "Cooling cost (THB)", min_value=0.0, value=80_000.0, step=5_000.0
)

# Reference observations from the supplied Supplementary File S1
reference = pd.DataFrame({
    "Temperature (°C)": [29, 32],
    "Fertilization rate": [0.677, 0.590],
    "Hatching rate": [0.434, 0.266],
    "Survival rate to 72 h": [0.449, 0.000]
})

st.info(
    "Reference observations are available at 29°C and 32°C. "
    "Intermediate and other temperatures below are linearly interpolated "
    "for an illustrative scenario, not validated biological predictions."
)

fertilization = float(
    reference["Fertilization rate"].iloc[0]
    + (temperature - 29) / 3
    * (reference["Fertilization rate"].iloc[1]
       - reference["Fertilization rate"].iloc[0])
)
hatching = float(
    reference["Hatching rate"].iloc[0]
    + (temperature - 29) / 3
    * (reference["Hatching rate"].iloc[1]
       - reference["Hatching rate"].iloc[0])
)
survival = float(
    reference["Survival rate to 72 h"].iloc[0]
    + (temperature - 29) / 3
    * (reference["Survival rate to 72 h"].iloc[1]
       - reference["Survival rate to 72 h"].iloc[0])
)

fertilization = max(0.0, min(1.0, fertilization))
hatching = max(0.0, min(1.0, hatching))
survival = max(0.0, min(1.0, survival))

hatched = eggs * fertilization * hatching
survivors = hatched * survival
revenue = survivors * egg_price
total_cost = base_cost + cooling_cost
profit = revenue - total_cost

a, b, c, d = st.columns(4)
a.metric("Fertilization rate", f"{fertilization:.1%}")
b.metric("Hatching rate", f"{hatching:.1%}")
c.metric("Estimated survivors", f"{survivors:,.0f}")
d.metric("Illustrative net result", f"฿{profit:,.0f}")

st.subheader("Hatchery outcome")
outcomes = pd.DataFrame({
    "Stage": ["Initial eggs", "Estimated hatched", "Estimated survivors"],
    "Number": [eggs, hatched, survivors]
})
fig = px.bar(
    outcomes, x="Stage", y="Number", text_auto=".3s",
    title="Estimated numbers at each stage"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Reference temperature comparison")
long_data = reference.melt(
    id_vars="Temperature (°C)",
    var_name="Biological indicator",
    value_name="Rate"
)
fig2 = px.line(
    long_data, x="Temperature (°C)", y="Rate",
    color="Biological indicator", markers=True,
    title="Observed reference rates at 29°C and 32°C"
)
fig2.update_yaxes(tickformat=".0%", range=[0, 1])
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Cost and revenue")
x, y, z = st.columns(3)
x.metric("Estimated revenue", f"฿{revenue:,.0f}")
y.metric("Base + cooling costs", f"฿{total_cost:,.0f}")
z.metric("Cooling cost", f"฿{cooling_cost:,.0f}")

st.caption(
    "Model note: Biological values are based on the two reference "
    "temperatures supplied. Linear interpolation is illustrative only. "
    "The survival-rate definition and model assumptions should be verified "
    "against the original study before operational or financial decisions."
)

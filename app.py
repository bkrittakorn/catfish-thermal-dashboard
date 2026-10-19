
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Catfish Thermal Risk Dashboard",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 2. LANGUAGE MANAGEMENT
# ============================================================

# Initialize only once. Never reset the language on every rerun.
if "language" not in st.session_state:
    st.session_state["language"] = "English"


def tr(en, th):
    """Return text in the currently selected language."""
    return th if st.session_state.get("language", "English") == "ไทย" else en


# ============================================================
# 3. GLOBAL STYLE
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1400px;
    }

    [data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.07);
        padding: 14px;
        border-radius: 12px;
    }

    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    h1, h2, h3 {
        letter-spacing: -0.3px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 4. FIXED INTERNAL PAGE IDENTIFIERS
# ============================================================

# Internal IDs never change when the display language changes.
PAGES = {
    "overview": {
        "en": "Overview",
        "th": "ภาพรวม",
    },
    "calculator": {
        "en": "Hatchery Calculator",
        "th": "เครื่องคำนวณโรงเพาะฟัก",
    },
    "climate": {
        "en": "Climate Simulation",
        "th": "จำลองสภาพภูมิอากาศ",
    },
    "sensitivity": {
        "en": "Sensitivity Analysis",
        "th": "วิเคราะห์ความอ่อนไหว",
    },
    "aquamonitor": {
        "en": "AquaMonitor",
        "th": "AquaMonitor",
    },
    "methods": {
        "en": "Methods",
        "th": "วิธีการศึกษา",
    },
}


def page_label(page_id):
    """Translate the display label without changing the page ID."""
    language = st.session_state.get("language", "English")
    return PAGES[page_id]["th"] if language == "ไทย" else PAGES[page_id]["en"]


# ============================================================
# 5. SIDEBAR: LANGUAGE AND NAVIGATION
# ============================================================

st.sidebar.title("🐟 Catfish Thermal Risk")

st.sidebar.radio(
    "Language / เลือกภาษา",
    options=["English", "ไทย"],
    key="language",
    label_visibility="collapsed",
)

st.sidebar.divider()

st.sidebar.caption(tr("MAIN MENU", "เมนูหลัก"))

selected_page = st.sidebar.radio(
    tr("Navigation", "เลือกหน้า"),
    options=list(PAGES.keys()),
    format_func=page_label,
    key="page_navigation",
    label_visibility="collapsed",
)

st.sidebar.divider()

st.sidebar.caption(
    tr(
        "Research prototype for exploring temperature-related hatchery risks.",
        "ระบบต้นแบบสำหรับศึกษาความเสี่ยงของโรงเพาะฟักที่เกี่ยวข้องกับอุณหภูมิ",
    )
)

# ============================================================
# 6. MODEL PARAMETERS
# ============================================================

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

REFERENCE = {
    "Temperature (°C)": [29, 32],
    "Fertilization rate": [0.677, 0.590],
    "Hatching rate": [0.434, 0.266],
    "Survival rate to 72 h": [0.449, 0.000],
}

# ============================================================
# 7. BIOLOGICAL MODEL FUNCTIONS
# ============================================================


def biological_rates(temp, threshold_shift=0.0):
    """
    Illustrative temperature-response model.

    Outputs are model estimates, not validated biological predictions.
    """
    temp = np.asarray(temp, dtype=float)

    # Illustrative fertilization response.
    fertilization = np.clip(
        0.677 - ALPHA * (temp - 29.0),
        0.0,
        1.0,
    )

    # Illustrative hatching response.
    hatching = np.clip(
        0.434 - BETA * (temp - 29.0),
        0.0,
        1.0,
    )

    # Illustrative survival response.
    critical_temp = TCRIT0 + threshold_shift

    survival = SMAX * np.exp(
        -0.5 * ((temp - TOPT) / SIGMA) ** 2
    )

    heat_penalty = np.exp(
        -(np.maximum(temp - critical_temp, 0.0) ** 2)
        / (2 * SIGMA ** 2)
    )

    survival = np.clip(survival * heat_penalty, 0.0, 100.0)

    return fertilization, hatching, survival


def seasonal_temperature(
    days,
    mean_temp=TMEAN,
    amplitude=AMP0,
    peak_day=DPEAK,
    anomaly=0.0,
):
    """Generate an illustrative seasonal temperature curve."""
    days = np.asarray(days, dtype=float)

    return (
        mean_temp
        + anomaly
        + amplitude
        * np.cos(2 * np.pi * (days - peak_day) / 365.0)
    )


def gaussian_survival(temp, threshold_shift=0.0):
    """Return illustrative survival percentage."""
    temp = np.asarray(temp, dtype=float)

    critical_temp = TCRIT0 + threshold_shift

    base_survival = SMAX * np.exp(
        -0.5 * ((temp - TOPT) / SIGMA) ** 2
    )

    heat_penalty = np.exp(
        -(np.maximum(temp - critical_temp, 0.0) ** 2)
        / (2 * SIGMA ** 2)
    )

    return np.clip(base_survival * heat_penalty, 0.0, 100.0)


def calculate_hatchery(
    temperature,
    eggs,
    fry_price,
    base_cost,
    cooling_cost,
    threshold_shift=0.0,
):
    """Calculate illustrative hatchery production and financial outputs."""

    fertilization, hatching, survival_percent = biological_rates(
        np.array([temperature]),
        threshold_shift=threshold_shift,
    )

    fertilization_rate = float(fertilization[0])
    hatching_rate = float(hatching[0])
    survival_rate = float(survival_percent[0]) / 100.0

    fertilized_eggs = eggs * fertilization_rate
    hatched_fry = fertilized_eggs * hatching_rate
    surviving_fry = hatched_fry * survival_rate

    revenue = surviving_fry * fry_price
    total_cost = base_cost + cooling_cost
    profit = revenue - total_cost

    return {
        "fertilization_rate": fertilization_rate,
        "hatching_rate": hatching_rate,
        "survival_rate": survival_rate,
        "fertilized_eggs": fertilized_eggs,
        "hatched_fry": hatched_fry,
        "surviving_fry": surviving_fry,
        "revenue": revenue,
        "total_cost": total_cost,
        "profit": profit,
    }


def format_number(value, decimals=0):
    """Format numeric values for display."""
    if value is None or not np.isfinite(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_currency(value):
    return f"฿{value:,.2f}"


# ============================================================
# 8. COMMON INPUTS
# ============================================================

def hatchery_inputs(prefix):
    """Display reusable hatchery input controls."""

    col1, col2 = st.columns(2)

    with col1:
        eggs = st.number_input(
            tr("Initial eggs", "จำนวนไข่เริ่มต้น"),
            min_value=1,
            value=5_000_000,
            step=100_000,
            key=f"{prefix}_eggs",
        )

        fry_price = st.number_input(
            tr("Price per surviving fry (THB)", "ราคาลูกปลาที่รอดต่อตัว (บาท)"),
            min_value=0.0,
            value=1.50,
            step=0.10,
            key=f"{prefix}_price",
        )

    with col2:
        base_cost = st.number_input(
            tr("Base operating cost (THB)", "ต้นทุนดำเนินงานพื้นฐาน (บาท)"),
            min_value=0.0,
            value=100_000.0,
            step=10_000.0,
            key=f"{prefix}_base_cost",
        )

        cooling_cost = st.number_input(
            tr("Cooling cost (THB)", "ต้นทุนการทำความเย็น (บาท)"),
            min_value=0.0,
            value=80_000.0,
            step=10_000.0,
            key=f"{prefix}_cooling_cost",
        )

    return eggs, fry_price, base_cost, cooling_cost


def display_hatchery_results(result):
    """Display production and financial metrics."""

    c1, c2, c3 = st.columns(3)

    c1.metric(
        tr("Fertilized eggs", "ไข่ที่ได้รับการปฏิสนธิ"),
        format_number(result["fertilized_eggs"]),
    )

    c2.metric(
        tr("Hatched fry", "ลูกปลาที่ฟักออก"),
        format_number(result["hatched_fry"]),
    )

    c3.metric(
        tr("Surviving fry", "ลูกปลาที่รอด"),
        format_number(result["surviving_fry"]),
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        tr("Estimated revenue", "รายรับโดยประมาณ"),
        format_currency(result["revenue"]),
    )

    c5.metric(
        tr("Total cost", "ต้นทุนรวม"),
        format_currency(result["total_cost"]),
    )

    c6.metric(
        tr("Estimated profit / loss", "กำไร / ขาดทุนโดยประมาณ"),
        format_currency(result["profit"]),
    )


# ============================================================
# 9. PAGE: OVERVIEW
# ============================================================

def render_overview():

    st.title(tr("🐟 Catfish Thermal Risk Dashboard", "🐟 แดชบอร์ดความเสี่ยงอุณหภูมิในปลาดุก"))

    st.write(
        tr(
            "Explore how temperature may affect catfish hatchery performance, "
            "survival, and potential production outcomes.",
            "สำรวจว่าอุณหภูมิอาจส่งผลต่อประสิทธิภาพโรงเพาะฟัก "
            "การรอดชีวิต และผลผลิตที่คาดการณ์ได้อย่างไร",
        )
    )

    st.info(
        tr(
            "The biological relationships in this prototype are illustrative. "
            "Validate them against species-specific and site-specific data "
            "before using them for operational decisions.",
            "ความสัมพันธ์ทางชีววิทยาในระบบต้นแบบนี้เป็นแบบจำลองเพื่อการศึกษา "
            "ควรตรวจสอบกับข้อมูลเฉพาะชนิดปลาและพื้นที่ก่อนนำไปใช้ตัดสินใจจริง",
        )
    )

    temperature = st.slider(
        tr("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
        min_value=20.0,
        max_value=38.0,
        value=29.0,
        step=0.5,
        key="overview_temperature",
    )

    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs("overview")

    result = calculate_hatchery(
        temperature,
        eggs,
        fry_price,
        base_cost,
        cooling_cost,
    )

    st.divider()

    st.subheader(tr("Current scenario", "สถานการณ์ปัจจุบัน"))

    m1, m2, m3 = st.columns(3)

    m1.metric(
        tr("Temperature", "อุณหภูมิ"),
        f"{temperature:.1f} °C",
    )

    m2.metric(
        tr("Hatching rate", "อัตราการฟัก"),
        f"{result['hatching_rate'] * 100:.1f}%",
    )

    m3.metric(
        tr("Survival rate", "อัตราการรอด"),
        f"{result['survival_rate'] * 100:.1f}%",
    )

    display_hatchery_results(result)

    st.subheader(tr("Reference observations", "ข้อมูลอ้างอิง"))

    reference_rows = []

    for metric, values in REFERENCE.items():
        reference_rows.append(
            {
                tr("Indicator", "ตัวชี้วัด"): tr(
                    metric,
                    {
                        "Temperature (°C)": "อุณหภูมิ (°C)",
                        "Fertilization rate": "อัตราการปฏิสนธิ",
                        "Hatching rate": "อัตราการฟัก",
                        "Survival rate to 72 h": "อัตราการรอดถึง 72 ชั่วโมง",
                    }.get(metric, metric),
                ),
                "29°C": f"{values[0]:.3f}",
                "32°C": f"{values[1]:.3f}",
            }
        )

    st.dataframe(
        pd.DataFrame(reference_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        tr(
            "Reference values are presented as supplied model inputs and "
            "should be checked against the original study before publication.",
            "ค่าข้อมูลอ้างอิงแสดงตามข้อมูลที่กำหนดไว้ในระบบต้นแบบ "
            "ควรตรวจสอบกับงานวิจัยต้นฉบับก่อนนำไปเผยแพร่",
        )
    )


# ============================================================
# 10. PAGE: HATCHERY CALCULATOR
# ============================================================

def render_calculator():

    st.title(tr("Hatchery Calculator", "เครื่องคำนวณโรงเพาะฟัก"))

    st.write(
        tr(
            "Estimate fertilization, hatching, survival, production, "
            "revenue, and costs under a selected temperature scenario.",
            "ประมาณอัตราการปฏิสนธิ การฟัก การรอด ผลผลิต รายรับ "
            "และต้นทุนภายใต้สถานการณ์อุณหภูมิที่เลือก",
        )
    )

    temperature = st.slider(
        tr("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
        min_value=20.0,
        max_value=38.0,
        value=29.0,
        step=0.5,
        key="calculator_temperature",
    )

    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs("calculator")

    result = calculate_hatchery(
        temperature,
        eggs,
        fry_price,
        base_cost,
        cooling_cost,
    )

    st.divider()

    st.subheader(tr("Estimated results", "ผลการประมาณ"))

    display_hatchery_results(result)

    rate_df = pd.DataFrame(
        {
            "Indicator": [
                tr("Fertilization rate", "อัตราการปฏิสนธิ"),
                tr("Hatching rate", "อัตราการฟัก"),
                tr("Survival rate", "อัตราการรอด"),
            ],
            "Rate (%)": [
                result["fertilization_rate"] * 100,
                result["hatching_rate"] * 100,
                result["survival_rate"] * 100,
            ],
        }
    )

    fig = px.bar(
        rate_df,
        x="Indicator",
        y="Rate (%)",
        title=tr(
            "Estimated biological rates",
            "อัตราทางชีววิทยาที่ประมาณได้",
        ),
        text_auto=".2f",
    )

    fig.update_layout(
        xaxis_title=tr("Indicator", "ตัวชี้วัด"),
        yaxis_title=tr("Rate (%)", "อัตรา (%)"),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        tr(
            "Financial outputs exclude any costs not entered by the user. "
            "Biological rates are illustrative model estimates.",
            "ผลทางการเงินไม่รวมต้นทุนที่ผู้ใช้ไม่ได้กรอก "
            "อัตราทางชีววิทยาเป็นค่าประมาณจากแบบจำลองเพื่อการศึกษา",
        )
    )


# ============================================================
# 11. PAGE: CLIMATE SIMULATION
# ============================================================

def render_climate():

    st.title(tr("Climate Simulation", "จำลองสภาพภูมิอากาศ"))

    st.write(
        tr(
            "Explore illustrative seasonal temperature patterns and "
            "possible effects of temperature anomalies on survival.",
            "สำรวจรูปแบบอุณหภูมิตามฤดูกาลและผลที่อาจเกิดจาก "
            "ความผิดปกติของอุณหภูมิต่อการรอดชีวิต",
        )
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        mean_temp = st.slider(
            tr("Mean temperature (°C)", "อุณหภูมิเฉลี่ย (°C)"),
            min_value=24.0,
            max_value=34.0,
            value=float(TMEAN),
            step=0.5,
            key="climate_mean",
        )

    with col2:
        amplitude = st.slider(
            tr("Seasonal amplitude (°C)", "ช่วงแกว่งตามฤดูกาล (°C)"),
            min_value=0.0,
            max_value=8.0,
            value=float(AMP0),
            step=0.5,
            key="climate_amplitude",
        )

    with col3:
        anomaly_sd = st.slider(
            tr("Annual anomaly SD (°C)", "SD ของความผิดปกติรายปี (°C)"),
            min_value=0.0,
            max_value=3.0,
            value=1.0,
            step=0.1,
            key="climate_anomaly_sd",
        )

    threshold_shift = st.slider(
        tr(
            "Critical temperature shift (°C)",
            "การเปลี่ยนแปลงอุณหภูมิวิกฤต (°C)",
        ),
        min_value=-2.0,
        max_value=3.0,
        value=0.0,
        step=0.25,
        key="climate_threshold_shift",
    )

    seed = st.number_input(
        tr("Random seed", "ค่าเริ่มต้นสุ่ม"),
        min_value=0,
        max_value=999999,
        value=int(SEED),
        step=1,
        key="climate_seed",
    )

    days = np.arange(1, 366)

    temp_curve = seasonal_temperature(
        days,
        mean_temp=mean_temp,
        amplitude=amplitude,
    )

    temp_df = pd.DataFrame(
        {
            "Day": days,
            "Temperature (°C)": temp_curve,
        }
    )

    fig_temp = px.line(
        temp_df,
        x="Day",
        y="Temperature (°C)",
        title=tr(
            "Illustrative seasonal temperature",
            "อุณหภูมิตามฤดูกาลจากแบบจำลอง",
        ),
    )

    fig_temp.update_layout(
        xaxis_title=tr("Day of year", "วันในรอบปี"),
        yaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
    )

    st.plotly_chart(fig_temp, use_container_width=True)

    survival_curve = gaussian_survival(
        temp_curve,
        threshold_shift=threshold_shift,
    )

    survival_df = pd.DataFrame(
        {
            "Day": days,
            "Survival (%)": survival_curve,
        }
    )

    fig_survival = px.line(
        survival_df,
        x="Day",
        y="Survival (%)",
        title=tr(
            "Illustrative daily survival response",
            "การตอบสนองของอัตราการรอดรายวันจากแบบจำลอง",
        ),
    )

    fig_survival.update_layout(
        xaxis_title=tr("Day of year", "วันในรอบปี"),
        yaxis_title=tr("Survival (%)", "อัตราการรอด (%)"),
    )

    st.plotly_chart(fig_survival, use_container_width=True)

    st.divider()

    st.subheader(
        tr("Multi-year Monte Carlo simulation", "การจำลองมอนติคาร์โลหลายปี")
    )

    st.write(
        tr(
            "Each simulated year receives a random annual temperature "
            "anomaly. The same anomaly is applied to all days in that year.",
            "แต่ละปีจำลองจะได้รับค่าความผิดปกติของอุณหภูมิแบบสุ่ม "
            "โดยใช้ค่าความผิดปกติเดียวกันกับทุกวันภายในปีนั้น",
        )
    )

    rng = np.random.default_rng(int(seed))

    years = np.arange(2026, 2037)

    annual_anomalies = rng.normal(
        loc=0.0,
        scale=anomaly_sd,
        size=(N_MONTE_CARLO, len(years)),
    )

    daily_temps = (
        temp_curve[None, None, :]
        + annual_anomalies[:, :, None]
    )

    daily_survival = gaussian_survival(
        daily_temps,
        threshold_shift=threshold_shift,
    )

    annual_survival = daily_survival.mean(axis=2)

    mc_median = np.median(annual_survival, axis=0)
    mc_lower = np.percentile(annual_survival, 5, axis=0)
    mc_upper = np.percentile(annual_survival, 95, axis=0)

    mc_df = pd.DataFrame(
        {
            "Year": years,
            "Median survival (%)": mc_median,
            "5th percentile (%)": mc_lower,
            "95th percentile (%)": mc_upper,
        }
    )

    fig_mc = px.line(
        mc_df,
        x="Year",
        y="Median survival (%)",
        markers=True,
        title=tr(
            "Annual survival estimates with uncertainty",
            "ค่าประมาณการรอดรายปีพร้อมช่วงความไม่แน่นอน",
        ),
    )

    fig_mc.add_trace(
        px.line(
            mc_df,
            x="Year",
            y="5th percentile (%)",
        ).data[0]
    )

    fig_mc.add_trace(
        px.line(
            mc_df,
            x="Year",
            y="95th percentile (%)",
        ).data[0]
    )

    fig_mc.update_layout(
        xaxis_title=tr("Year", "ปี"),
        yaxis_title=tr("Mean daily survival (%)", "อัตราการรอดเฉลี่ยรายวัน (%)"),
        legend_title_text=tr("Statistic", "สถิติ"),
    )

    fig_mc.data[0].name = tr("Median", "มัธยฐาน")
    fig_mc.data[1].name = tr("5th percentile", "เปอร์เซ็นไทล์ที่ 5")
    fig_mc.data[2].name = tr("95th percentile", "เปอร์เซ็นไทล์ที่ 95")

    st.plotly_chart(fig_mc, use_container_width=True)

    st.dataframe(
        mc_df.style.format(
            {
                "Median survival (%)": "{:.2f}",
                "5th percentile (%)": "{:.2f}",
                "95th percentile (%)": "{:.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        tr("Download annual simulation CSV", "ดาวน์โหลดผลจำลองรายปี CSV"),
        data=mc_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_climate_annual_simulation.csv",
        mime="text/csv",
        key="climate_download_annual",
    )

    daily_df = pd.DataFrame(
        {
            "Day": days,
            "Temperature (°C)": temp_curve,
            "Estimated survival (%)": survival_curve,
        }
    )

    st.download_button(
        tr("Download daily simulation CSV", "ดาวน์โหลดผลจำลองรายวัน CSV"),
        data=daily_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_climate_daily_simulation.csv",
        mime="text/csv",
        key="climate_download_daily",
    )

    st.warning(
        tr(
            "The simulation uses simplified assumptions and does not "
            "represent an official climate projection. Validate model "
            "parameters against observed data before drawing conclusions.",
            "การจำลองนี้ใช้สมมติฐานอย่างง่ายและไม่ใช่การคาดการณ์ภูมิอากาศ "
            "อย่างเป็นทางการ ควรตรวจสอบพารามิเตอร์กับข้อมูลสังเกตจริงก่อนสรุปผล",
        )
    )


# ============================================================
# 12. PAGE: SENSITIVITY ANALYSIS
# ============================================================

def render_sensitivity():

    st.title(tr("Sensitivity Analysis", "วิเคราะห์ความอ่อนไหว"))

    st.write(
        tr(
            "Compare model outputs across a range of water temperatures.",
            "เปรียบเทียบผลลัพธ์ของแบบจำลองในช่วงอุณหภูมิน้ำต่าง ๆ",
        )
    )

    baseline_temp = st.slider(
        tr("Baseline temperature (°C)", "อุณหภูมิฐาน (°C)"),
        min_value=20.0,
        max_value=38.0,
        value=29.0,
        step=0.5,
        key="sensitivity_baseline",
    )

    temp_range = st.slider(
        tr(
            "Temperature range around baseline (°C)",
            "ช่วงอุณหภูมิรอบค่าอุณหภูมิฐาน (°C)",
        ),
        min_value=0.5,
        max_value=8.0,
        value=2.0,
        step=0.5,
        key="sensitivity_range",
    )

    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs("sensitivity")

    temps = np.arange(
        max(20.0, baseline_temp - temp_range),
        min(38.0, baseline_temp + temp_range) + 0.001,
        0.25,
    )

    if not np.any(np.isclose(temps, baseline_temp)):
        temps = np.append(temps, baseline_temp)

    temps = np.unique(np.round(temps, 2))
    temps.sort()

    records = []

    for temperature in temps:
        result = calculate_hatchery(
            temperature,
            eggs,
            fry_price,
            base_cost,
            cooling_cost,
        )

        records.append(
            {
                "Temperature (°C)": temperature,
                "Fertilization (%)": result["fertilization_rate"] * 100,
                "Hatching (%)": result["hatching_rate"] * 100,
                "Survival (%)": result["survival_rate"] * 100,
                "Surviving fry": result["surviving_fry"],
                "Revenue (THB)": result["revenue"],
                "Profit (THB)": result["profit"],
            }
        )

    sensitivity_df = pd.DataFrame(records)

    baseline_result = calculate_hatchery(
        baseline_temp,
        eggs,
        fry_price,
        base_cost,
        cooling_cost,
    )

    st.subheader(tr("Baseline scenario", "สถานการณ์ฐาน"))

    c1, c2, c3 = st.columns(3)

    c1.metric(
        tr("Baseline temperature", "อุณหภูมิฐาน"),
        f"{baseline_temp:.1f} °C",
    )

    c2.metric(
        tr("Surviving fry", "ลูกปลาที่รอด"),
        format_number(baseline_result["surviving_fry"]),
    )

    c3.metric(
        tr("Estimated profit / loss", "กำไร / ขาดทุนโดยประมาณ"),
        format_currency(baseline_result["profit"]),
    )

    fig_rates = px.line(
        sensitivity_df,
        x="Temperature (°C)",
        y=["Fertilization (%)", "Hatching (%)", "Survival (%)"],
        markers=True,
        title=tr(
            "Biological response to temperature",
            "การตอบสนองทางชีววิทยาต่ออุณหภูมิ",
        ),
    )

    fig_rates.add_vline(
        x=baseline_temp,
        line_dash="dash",
        annotation_text=tr("Baseline", "ค่าอุณหภูมิฐาน"),
    )

    fig_rates.update_layout(
        xaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
        yaxis_title=tr("Rate (%)", "อัตรา (%)"),
        legend_title_text=tr("Indicator", "ตัวชี้วัด"),
    )

    st.plotly_chart(fig_rates, use_container_width=True)

    fig_production = px.line(
        sensitivity_df,
        x="Temperature (°C)",
        y="Surviving fry",
        markers=True,
        title=tr(
            "Estimated surviving fry by temperature",
            "จำนวนลูกปลาที่คาดว่าจะรอดในแต่ละอุณหภูมิ",
        ),
    )

    fig_production.add_vline(
        x=baseline_temp,
        line_dash="dash",
    )

    fig_production.update_layout(
        xaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
        yaxis_title=tr("Surviving fry", "จำนวนลูกปลาที่รอด"),
    )

    st.plotly_chart(fig_production, use_container_width=True)

    fig_profit = px.line(
        sensitivity_df,
        x="Temperature (°C)",
        y="Profit (THB)",
        markers=True,
        title=tr(
            "Estimated profit / loss by temperature",
            "กำไร / ขาดทุนโดยประมาณตามอุณหภูมิ",
        ),
    )

    fig_profit.add_hline(y=0, line_dash="dash")

    fig_profit.add_vline(
        x=baseline_temp,
        line_dash="dash",
    )

    fig_profit.update_layout(
        xaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
        yaxis_title=tr("Profit / loss (THB)", "กำไร / ขาดทุน (บาท)"),
    )

    st.plotly_chart(fig_profit, use_container_width=True)

    st.subheader(tr("Scenario data", "ข้อมูลแต่ละสถานการณ์"))

    display_df = sensitivity_df.copy()

    for column in [
        "Fertilization (%)",
        "Hatching (%)",
        "Survival (%)",
    ]:
        display_df[column] = display_df[column].map(
            lambda value: f"{value:.2f}"
        )

    display_df["Temperature (°C)"] = display_df["Temperature (°C)"].map(
        lambda value: f"{value:.2f}"
    )

    display_df["Surviving fry"] = display_df["Surviving fry"].map(
        lambda value: f"{value:,.0f}"
    )

    display_df["Revenue (THB)"] = display_df["Revenue (THB)"].map(
        lambda value: f"{value:,.2f}"
    )

    display_df["Profit (THB)"] = display_df["Profit (THB)"].map(
        lambda value: f"{value:,.2f}"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        tr("Download sensitivity CSV", "ดาวน์โหลดข้อมูลความอ่อนไหว CSV"),
        data=sensitivity_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="catfish_sensitivity_analysis.csv",
        mime="text/csv",
        key="sensitivity_download",
    )

    st.caption(
        tr(
            "All biological and financial outputs are conditional on the "
            "model assumptions and user-entered inputs.",
            "ผลทางชีววิทยาและการเงินขึ้นอยู่กับสมมติฐานของแบบจำลอง "
            "และข้อมูลที่ผู้ใช้กรอก",
        )
    )


# ============================================================
# 13. PAGE: AQUAMONITOR
# ============================================================

def render_aquamonitor():

    try:
        from aquamonitor import run_aquamonitor

        run_aquamonitor()

    except ImportError as error:
        st.error(
            tr(
                "Could not import aquamonitor.py. Ensure that the file "
                "exists in the same directory as app.py.",
                "ไม่สามารถนำเข้า aquamonitor.py ได้ โปรดตรวจสอบว่าไฟล์ "
                "อยู่ในโฟลเดอร์เดียวกับ app.py",
            )
        )
        st.code(str(error))

    except Exception as error:
        st.error(
            tr(
                "An error occurred while loading AquaMonitor.",
                "เกิดข้อผิดพลาดระหว่างเปิด AquaMonitor",
            )
        )
        st.exception(error)


# ============================================================
# 14. PAGE: METHODS
# ============================================================

def render_methods():

    st.title(tr("Methods & Assumptions", "วิธีการศึกษาและสมมติฐาน"))

    st.write(
        tr(
            "This page summarizes the calculations and assumptions used "
            "in the Catfish Thermal Risk Dashboard.",
            "หน้านี้สรุปวิธีคำนวณและสมมติฐานที่ใช้ในแดชบอร์ด "
            "ความเสี่ยงอุณหภูมิในปลาดุก",
        )
    )

    st.header(tr("1. Hatchery production", "1. ผลผลิตโรงเพาะฟัก"))

    st.latex(
        r"\text{Fertilized eggs} = "
        r"\text{Initial eggs} \times "
        r"\text{Fertilization rate}"
    )

    st.latex(
        r"\text{Hatched fry} = "
        r"\text{Fertilized eggs} \times "
        r"\text{Hatching rate}"
    )

    st.latex(
        r"\text{Surviving fry} = "
        r"\text{Hatched fry} \times "
        r"\text{Survival rate}"
    )

    st.header(tr("2. Financial estimates", "2. การประมาณการทางการเงิน"))

    st.latex(
        r"\text{Revenue} = "
        r"\text{Surviving fry} \times "
        r"\text{Price per fry}"
    )

    st.latex(
        r"\text{Estimated profit} = "
        r"\text{Revenue} - "
        r"\text{Base cost} - "
        r"\text{Cooling cost}"
    )

    st.header(tr("3. Seasonal temperature", "3. อุณหภูมิตามฤดูกาล"))

    st.latex(
        r"T_d = \overline{T} + "
        r"A\cos\left(\frac{2\pi(d-d_{\mathrm{peak}})}{365}\right)"
        r" + \epsilon"
    )

    st.write(
        tr(
            "Where the mean temperature, seasonal amplitude, peak day, "
            "and anomaly are user-configurable or model assumptions.",
            "โดยอุณหภูมิเฉลี่ย ช่วงแกว่งตามฤดูกาล วันที่อุณหภูมิสูงสุด "
            "และค่าความผิดปกติ เป็นค่าที่กำหนดในแบบจำลองหรือโดยผู้ใช้",
        )
    )

    st.header(tr("4. Monte Carlo simulation", "4. การจำลองมอนติคาร์โล"))

    st.write(
        tr(
            "The model samples an annual temperature anomaly from a normal "
            "distribution and applies it to the daily seasonal temperature "
            "curve. The annual result is summarized from the simulated "
            "daily survival estimates.",
            "แบบจำลองสุ่มค่าความผิดปกติของอุณหภูมิรายปีจากการแจกแจงปกติ "
            "แล้วนำไปบวกกับเส้นอุณหภูมิตามฤดูกาลรายวัน "
            "ผลรายปีสรุปจากค่าการรอดรายวันที่จำลองได้",
        )
    )

    st.header(tr("5. AquaMonitor", "5. AquaMonitor"))

    st.latex(
        r"\mathrm{HQ} = "
        r"\frac{C \times IR}{BW \times RfD}"
    )

    st.latex(
        r"\mathrm{HI} = \sum_i \mathrm{HQ}_i"
    )

    st.write(
        tr(
            "AquaMonitor uses a screening calculation based on measured "
            "concentrations, an assumed fish consumption rate, body weight, "
            "and reference doses. Confirm that the units and reference doses "
            "match the intended exposure pathway before interpreting results.",
            "AquaMonitor ใช้การคำนวณเพื่อการคัดกรองจากค่าความเข้มข้นที่ตรวจวัด "
            "ปริมาณการบริโภคปลาที่สมมติ น้ำหนักตัว และค่าอ้างอิงความเป็นพิษ "
            "ควรตรวจสอบหน่วยและค่าอ้างอิงให้ตรงกับช่องทางการรับสัมผัส "
            "ก่อนแปลผล",
        )
    )

    st.header(tr("6. Limitations", "6. ข้อจำกัด"))

    st.warning(
        tr(
            "This dashboard is a research prototype. The biological response "
            "functions are simplified and are not validated predictions for "
            "all catfish species or hatchery systems. The climate simulation "
            "is not an official climate projection. Financial estimates omit "
            "costs not entered by the user. AquaMonitor reference doses and "
            "exposure assumptions require independent verification. "
            "Do not use these outputs as a substitute for laboratory data, "
            "official standards, or professional advice.",
            "แดชบอร์ดนี้เป็นระบบต้นแบบเพื่อการศึกษา ฟังก์ชันตอบสนองทางชีววิทยา "
            "เป็นแบบจำลองอย่างง่ายและไม่ได้รับการยืนยันว่าใช้พยากรณ์ได้กับ "
            "ปลาดุกทุกชนิดหรือทุกระบบเพาะฟัก การจำลองภูมิอากาศไม่ใช่ "
            "การคาดการณ์อย่างเป็นทางการ การประมาณทางการเงินไม่รวมต้นทุน "
            "ที่ผู้ใช้ไม่ได้กรอก ส่วนค่าอ้างอิงความเป็นพิษและสมมติฐานการรับสัมผัส "
            "ของ AquaMonitor ต้องได้รับการตรวจสอบอย่างอิสระ "
            "ไม่ควรใช้ผลลัพธ์แทนข้อมูลห้องปฏิบัติการ มาตรฐานทางการ "
            "หรือคำแนะนำจากผู้เชี่ยวชาญ",
        )
    )


# ============================================================
# 15. ROUTE TO THE SELECTED PAGE
# ============================================================

# The selected_page is always an internal ID.
# Changing the language changes labels only, not page identity.

if selected_page == "overview":
    render_overview()

elif selected_page == "calculator":
    render_calculator()

elif selected_page == "climate":
    render_climate()

elif selected_page == "sensitivity":
    render_sensitivity()

elif selected_page == "aquamonitor":
    render_aquamonitor()

elif selected_page == "methods":
    render_methods()

else:
    st.error(
        tr(
            "Unknown page. Please select a page from the navigation menu.",
            "ไม่พบหน้าที่เลือก โปรดเลือกหน้าจากเมนูหลัก",
        )
    )

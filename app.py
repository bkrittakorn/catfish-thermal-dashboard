
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
# 2. BILINGUAL LANGUAGE SYSTEM
# ============================================================
if "language" not in st.session_state:
    st.session_state["language"] = "English"


def tr(en, th):
    """Return the selected language."""
    return th if st.session_state.get("language", "English") == "ไทย" else en


# ============================================================
# 3. STYLING
# ============================================================
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F4F8FA;
    }

    [data-testid="stSidebar"] {
        background-color: #E8F1F4;
    }

    h1, h2, h3 {
        color: #163A4A;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #D9E5EA;
        border-radius: 12px;
        padding: 14px;
    }

    div[data-testid="stAlert"] {
        border-radius: 10px;
    }

    .dashboard-caption {
        color: #607782;
        font-size: 0.92rem;
    }

    hr {
        border-color: #D9E5EA;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 4. REFERENCE DATA
# ============================================================
REFERENCE = {
    "Temperature (°C)": [29, 32],
    "Fertilization rate": [0.677, 0.590],
    "Hatching rate": [0.434, 0.266],
    "Survival rate to 72 h": [0.449, 0.0],
}


# ============================================================
# 5. MODEL PARAMETERS
# ============================================================
SEED = 20260929
N_MONTE_CARLO = 10000

TMEAN = 28.5
AMP0 = 3.5
DPEAK = 115
ALPHA = 0.08
BETA = 0.03
E_SD = 0.30

TOPT = 29
SIGMA = 1
SMAX = 44.9

TCRIT0 = 30.75
DELTA_G = 0.15


# ============================================================
# 6. BIOLOGICAL AND CLIMATE FUNCTIONS
# ============================================================
def biological_rates(temp):
    """
    Estimate biological rates using linear interpolation
    between the two available reference temperatures.
    Values outside the reference interval use endpoint rates.
    """
    temperatures = np.array(REFERENCE["Temperature (°C)"])

    rates = {}

    for name in [
        "Fertilization rate",
        "Hatching rate",
        "Survival rate to 72 h",
    ]:
        observed = np.array(REFERENCE[name])

        rates[name] = float(
            np.interp(temp, temperatures, observed)
        )

    return rates


def seasonal_temperature(day, year_index=0):
    """
    Illustrative seasonal temperature model.

    day: day of year, 1-365
    year_index: number of years after the baseline year
    """
    day = np.asarray(day)

    mean_temp = TMEAN + ALPHA * year_index

    amplitude = AMP0 * np.exp(-BETA * year_index)

    temperature = (
        mean_temp
        + amplitude
        * np.sin(2 * np.pi * (day - DPEAK) / 365)
    )

    return temperature


def gaussian_survival(temp, threshold_shift=0.0):
    """
    Illustrative temperature-dependent survival curve.

    This curve is a scenario assumption, not a calibrated
    biological prediction.
    """
    threshold = TCRIT0 + threshold_shift

    survival = SMAX * np.exp(
        -0.5 * ((np.asarray(temp) - TOPT) / SIGMA) ** 2
    )

    # Illustrative high-temperature stress penalty
    penalty = np.exp(
        -np.maximum(np.asarray(temp) - threshold, 0) ** 2
        / (2 * SIGMA ** 2)
    )

    return survival * penalty


def calculate_hatchery(temp, eggs, fry_price, base_cost, cooling_cost):
    """Calculate hatchery production and illustrative economics."""
    rates = biological_rates(temp)

    fertilized = eggs * rates["Fertilization rate"]

    hatched = fertilized * rates["Hatching rate"]

    survivors = hatched * rates["Survival rate to 72 h"]

    revenue = survivors * fry_price

    total_cost = base_cost + cooling_cost

    net_result = revenue - total_cost

    return {
        "temperature": float(temp),
        "fertilization_rate": rates["Fertilization rate"],
        "hatching_rate": rates["Hatching rate"],
        "survival_rate": rates["Survival rate to 72 h"],
        "fertilized_eggs": fertilized,
        "hatched_larvae": hatched,
        "survivors": survivors,
        "revenue": revenue,
        "base_cost": base_cost,
        "cooling_cost": cooling_cost,
        "total_cost": total_cost,
        "net_result": net_result,
    }


# ============================================================
# 7. SIDEBAR: LANGUAGE, NAVIGATION AND ASSUMPTIONS
# ============================================================
st.sidebar.markdown("### 🌐 Language / ภาษา")

st.sidebar.radio(
    "Select language / เลือกภาษา",
    options=["English", "ไทย"],
    horizontal=True,
    key="language",
    label_visibility="collapsed",
)

language = st.session_state["language"]
is_thai = language == "ไทย"

PAGE_LABELS = {
    "Overview": ("Overview", "ภาพรวม"),
    "Hatchery Calculator": (
        "Hatchery Calculator",
        "เครื่องคำนวณโรงเพาะฟัก",
    ),
    "Climate Simulation": (
        "Climate Simulation",
        "จำลองสภาพภูมิอากาศ",
    ),
    "Sensitivity Analysis": (
        "Sensitivity Analysis",
        "วิเคราะห์ความอ่อนไหว",
    ),
    "AquaMonitor": (
        "AquaMonitor",
        "วิเคราะห์คุณภาพน้ำ",
    ),
    "Methods": (
        "Methods & Limitations",
        "วิธีการและข้อจำกัด",
    ),
}

st.sidebar.divider()
st.sidebar.header(tr("Dashboard navigation", "เมนูหลัก"))

page = st.sidebar.radio(
    tr("Choose a page", "เลือกหน้า"),
    options=list(PAGE_LABELS.keys()),
    format_func=lambda key: (
        PAGE_LABELS[key][1]
        if is_thai
        else PAGE_LABELS[key][0]
    ),
    key="page_navigation",
)

st.sidebar.divider()
st.sidebar.header(
    tr("Hatchery assumptions", "สมมติฐานโรงเพาะฟัก")
)

eggs = st.sidebar.number_input(
    tr("Initial eggs", "จำนวนไข่เริ่มต้น"),
    min_value=1,
    value=5_000_000,
    step=100_000,
    key="assumption_eggs",
)

fry_price = st.sidebar.number_input(
    tr("Price per fry (THB)", "ราคาต่อลูกปลา (บาท)"),
    min_value=0.0,
    value=1.50,
    step=0.10,
    key="assumption_fry_price",
)

base_cost = st.sidebar.number_input(
    tr("Base operating cost (THB)", "ต้นทุนดำเนินงานพื้นฐาน (บาท)"),
    min_value=0.0,
    value=100_000.0,
    step=5_000.0,
    key="assumption_base_cost",
)

cooling_cost = st.sidebar.number_input(
    tr("Cooling cost (THB)", "ต้นทุนระบบทำความเย็น (บาท)"),
    min_value=0.0,
    value=80_000.0,
    step=5_000.0,
    key="assumption_cooling_cost",
)

st.sidebar.caption(
    tr(
        "Economic estimates exclude costs not entered above.",
        "การประเมินทางเศรษฐศาสตร์ไม่รวมต้นทุนอื่นที่ไม่ได้ระบุไว้ข้างต้น",
    )
)


# ============================================================
# 8. HEADER
# ============================================================
st.title(
    tr(
        "🐟 Catfish Thermal Risk Dashboard",
        "🐟 แดชบอร์ดความเสี่ยงด้านอุณหภูมิของปลาดุก",
    )
)

st.markdown(
    f'<p class="dashboard-caption">'
    f'{tr("Biological performance, climate scenarios and hatchery economics",
          "ประสิทธิภาพทางชีววิทยา สถานการณ์ภูมิอากาศ และเศรษฐศาสตร์โรงเพาะฟัก")}'
    f'</p>',
    unsafe_allow_html=True,
)


# ============================================================
# 9. OVERVIEW
# ============================================================
if page == "Overview":

    st.header(tr("Overview", "ภาพรวม"))

    st.write(
        tr(
            "Explore how water temperature may affect estimated "
            "catfish hatchery performance and illustrative financial results.",
            "สำรวจว่าอุณหภูมิน้ำอาจส่งผลต่อประสิทธิภาพการเพาะฟักปลาดุก "
            "และผลลัพธ์ทางการเงินโดยประมาณอย่างไร",
        )
    )

    temp = st.slider(
        tr("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
        min_value=25.0,
        max_value=36.0,
        value=29.0,
        step=0.5,
        key="overview_temperature",
    )

    result = calculate_hatchery(
        temp,
        eggs,
        fry_price,
        base_cost,
        cooling_cost,
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        tr("Fertilization rate", "อัตราการปฏิสนธิ"),
        f'{result["fertilization_rate"]:.1%}',
    )

    col2.metric(
        tr("Hatching rate", "อัตราการฟัก"),
        f'{result["hatching_rate"]:.1%}',
    )

    col3.metric(
        tr("Survival rate to 72 h", "อัตรารอดที่ 72 ชั่วโมง"),
        f'{result["survival_rate"]:.1%}',
    )

    col4, col5, col6 = st.columns(3)

    col4.metric(
        tr("Estimated survivors", "จำนวนที่คาดว่าจะรอด"),
        f'{result["survivors"]:,.0f}',
    )

    col5.metric(
        tr("Estimated revenue", "รายได้โดยประมาณ"),
        f'฿{result["revenue"]:,.2f}',
    )

    col6.metric(
        tr("Illustrative net result", "ผลสุทธิโดยประมาณ"),
        f'฿{result["net_result"]:,.2f}',
    )

    st.subheader(
        tr("Production stages", "ขั้นตอนการผลิต")
    )

    production_df = pd.DataFrame(
        {
            "Stage": [
                tr("Initial eggs", "ไข่เริ่มต้น"),
                tr("Fertilized eggs", "ไข่ที่ปฏิสนธิ"),
                tr("Hatched larvae", "ลูกปลาที่ฟัก"),
                tr("Survivors at 72 h", "ลูกปลารอดที่ 72 ชั่วโมง"),
            ],
            "Number of fish": [
                eggs,
                result["fertilized_eggs"],
                result["hatched_larvae"],
                result["survivors"],
            ],
        }
    )

    fig = px.bar(
        production_df,
        x="Stage",
        y="Number of fish",
        title=tr(
            "Estimated production by stage",
            "จำนวนปลาโดยประมาณในแต่ละขั้นตอน",
        ),
        text_auto=",.0f",
    )

    fig.update_layout(
        xaxis_title=tr("Production stage", "ขั้นตอนการผลิต"),
        yaxis_title=tr("Number of fish", "จำนวนปลา"),
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander(
        tr("View assumptions and formulas", "ดูสมมติฐานและสูตรคำนวณ")
    ):
        st.markdown(
            tr(
                """
                - Fertilized eggs = Initial eggs × Fertilization rate
                - Hatched larvae = Fertilized eggs × Hatching rate
                - Survivors = Hatched larvae × Survival rate to 72 h
                - Revenue = Survivors × Price per fry
                - Total specified costs = Base operating cost + Cooling cost
                - Net result = Revenue − Total specified costs
                """,
                """
                - ไข่ที่ปฏิสนธิ = จำนวนไข่เริ่มต้น × อัตราการปฏิสนธิ
                - ลูกปลาที่ฟัก = ไข่ที่ปฏิสนธิ × อัตราการฟัก
                - ลูกปลารอด = ลูกปลาที่ฟัก × อัตรารอดที่ 72 ชั่วโมง
                - รายได้ = จำนวนลูกปลารอด × ราคาต่อลูกปลา
                - ต้นทุนรวมที่ระบุ = ต้นทุนดำเนินงานพื้นฐาน + ต้นทุนทำความเย็น
                - ผลสุทธิ = รายได้ − ต้นทุนรวมที่ระบุ
                """,
            )
        )

    st.warning(
        tr(
            "Only two reference temperatures (29°C and 32°C) are available. "
            "Linear interpolation is used between these values and endpoint "
            "rates are used outside this interval. Results are estimates, "
            "not validated predictions. The economic model excludes costs "
            "not entered in the sidebar.",
            "มีข้อมูลอ้างอิงเพียงสองอุณหภูมิ คือ 29°C และ 32°C "
            "จึงใช้การประมาณค่าเชิงเส้นระหว่างสองจุด และใช้ค่าอัตราที่ปลายช่วง "
            "เมื่ออุณหภูมิอยู่นอกช่วงดังกล่าว ผลลัพธ์เป็นค่าประมาณ "
            "ไม่ใช่การพยากรณ์ที่ผ่านการตรวจสอบ และไม่รวมต้นทุนที่ไม่ได้กรอกในแถบด้านข้าง",
        )
    )


# ============================================================
# 10. HATCHERY CALCULATOR
# ============================================================
elif page == "Hatchery Calculator":

    st.header(
        tr("Hatchery Calculator", "เครื่องคำนวณโรงเพาะฟัก")
    )

    st.write(
        tr(
            "Estimate production stages and illustrative financial results "
            "using the selected temperature and sidebar assumptions.",
            "ประมาณจำนวนปลาในแต่ละขั้นตอนและผลทางการเงินโดยใช้ "
            "อุณหภูมิที่เลือกและสมมติฐานจากแถบด้านข้าง",
        )
    )

    temp = st.slider(
        tr("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
        25.0,
        36.0,
        29.0,
        0.5,
        key="hatchery_temperature",
    )

    result = calculate_hatchery(
        temp,
        eggs,
        fry_price,
        base_cost,
        cooling_cost,
    )

    st.subheader(
        tr("Estimated production", "ผลผลิตโดยประมาณ")
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        tr("Fertilized eggs", "ไข่ที่ปฏิสนธิ"),
        f'{result["fertilized_eggs"]:,.0f}',
    )

    c2.metric(
        tr("Hatched larvae", "ลูกปลาที่ฟัก"),
        f'{result["hatched_larvae"]:,.0f}',
    )

    c3.metric(
        tr("Survivors at 72 h", "ลูกปลารอดที่ 72 ชั่วโมง"),
        f'{result["survivors"]:,.0f}',
    )

    st.subheader(
        tr("Illustrative economics", "ผลทางเศรษฐศาสตร์โดยประมาณ")
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        tr("Revenue", "รายได้"),
        f'฿{result["revenue"]:,.2f}',
    )

    c2.metric(
        tr("Specified costs", "ต้นทุนที่ระบุ"),
        f'฿{result["total_cost"]:,.2f}',
    )

    c3.metric(
        tr("Net result", "ผลสุทธิ"),
        f'฿{result["net_result"]:,.2f}',
    )

    stage_labels = [
        tr("Initial eggs", "ไข่เริ่มต้น"),
        tr("Fertilized eggs", "ไข่ที่ปฏิสนธิ"),
        tr("Hatched larvae", "ลูกปลาที่ฟัก"),
        tr("Survivors at 72 h", "ลูกปลารอดที่ 72 ชั่วโมง"),
    ]

    stage_values = [
        eggs,
        result["fertilized_eggs"],
        result["hatched_larvae"],
        result["survivors"],
    ]

    stage_df = pd.DataFrame(
        {
            "Production stage": stage_labels,
            "Number of fish": stage_values,
        }
    )

    fig = px.bar(
        stage_df,
        x="Production stage",
        y="Number of fish",
        title=tr(
            "Production by stage",
            "ผลผลิตแยกตามขั้นตอน",
        ),
        text_auto=",.0f",
    )

    fig.update_layout(
        xaxis_title=tr("Production stage", "ขั้นตอนการผลิต"),
        yaxis_title=tr("Number of fish", "จำนวนปลา"),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        stage_df,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander(
        tr("Calculation assumptions", "สมมติฐานการคำนวณ")
    ):
        st.write(
            tr(
                "Biological rates are estimated by linear interpolation "
                "between reference temperatures of 29°C and 32°C. "
                "Survival is calculated through sequential multiplication "
                "of the fertilization, hatching and 72-hour survival rates.",
                "อัตราทางชีววิทยาประมาณด้วยการประมาณค่าเชิงเส้นระหว่าง "
                "29°C และ 32°C โดยคำนวณจำนวนลูกปลารอดจากการคูณอัตราการปฏิสนธิ "
                "อัตราการฟัก และอัตรารอดที่ 72 ชั่วโมงตามลำดับ",
            )
        )

    st.warning(
        tr(
            "This calculator is an illustrative screening tool. "
            "The limited reference data may not represent all production "
            "conditions. Economic results exclude any unentered costs.",
            "เครื่องคำนวณนี้ใช้สำหรับการประเมินเบื้องต้นเท่านั้น "
            "ข้อมูลอ้างอิงที่มีจำกัดอาจไม่ครอบคลุมทุกสภาวะการผลิต "
            "และผลทางเศรษฐศาสตร์ไม่รวมต้นทุนที่ไม่ได้ระบุ",
        )
    )


# ============================================================
# 11. CLIMATE SIMULATION
# ============================================================
elif page == "Climate Simulation":

    st.header(
        tr("Climate Simulation", "จำลองสภาพภูมิอากาศ")
    )

    st.write(
        tr(
            "Explore illustrative seasonal temperature patterns, "
            "temperature-dependent survival, and multi-year uncertainty.",
            "สำรวจรูปแบบอุณหภูมิตามฤดูกาล การรอดตามอุณหภูมิ "
            "และความไม่แน่นอนในหลายปีด้วยสถานการณ์จำลอง",
        )
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        anomaly_sd = st.slider(
            tr("Annual anomaly SD (°C)", "ส่วนเบี่ยงเบนมาตรฐานของความแปรปรวนรายปี (°C)"),
            min_value=0.0,
            max_value=1.0,
            value=E_SD,
            step=0.05,
            key="climate_anomaly_sd",
        )

    with col2:
        delta_g = st.slider(
            tr("Threshold shift Δg (°C)", "การเลื่อนเกณฑ์ Δg (°C)"),
            min_value=0.10,
            max_value=0.20,
            value=DELTA_G,
            step=0.01,
            key="climate_delta_g",
        )

    with col3:
        seed = st.number_input(
            tr("Random seed", "ค่าเริ่มต้นสุ่ม"),
            min_value=0,
            value=SEED,
            step=1,
            key="climate_seed",
        )

    days = np.arange(1, 366)

    base_temps = seasonal_temperature(days, year_index=0)

    future_temps = seasonal_temperature(days, year_index=10)

    st.subheader(
        tr("Seasonal temperature scenario", "สถานการณ์อุณหภูมิตามฤดูกาล")
    )

    seasonal_df = pd.DataFrame(
        {
            "Day of year": np.concatenate([days, days]),
            "Temperature (°C)": np.concatenate(
                [base_temps, future_temps]
            ),
            "Scenario": (
                [tr("Baseline year", "ปีฐาน")] * len(days)
                + [tr("Year +10", "ปีที่ +10")] * len(days)
            ),
        }
    )

    fig_temp = px.line(
        seasonal_df,
        x="Day of year",
        y="Temperature (°C)",
        color="Scenario",
        title=tr(
            "Illustrative seasonal temperature",
            "อุณหภูมิตามฤดูกาลโดยประมาณ",
        ),
    )

    fig_temp.update_layout(
        xaxis_title=tr("Day of year", "วันในรอบปี"),
        yaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
    )

    st.plotly_chart(fig_temp, use_container_width=True)

    st.subheader(
        tr(
            "Illustrative temperature-dependent survival",
            "การรอดตามอุณหภูมิโดยประมาณ",
        )
    )

    temp_grid = np.linspace(22, 38, 200)

    survival_baseline = gaussian_survival(
        temp_grid,
        threshold_shift=0.0,
    )

    survival_shifted = gaussian_survival(
        temp_grid,
        threshold_shift=delta_g,
    )

    survival_df = pd.DataFrame(
        {
            "Temperature (°C)": np.concatenate(
                [temp_grid, temp_grid]
            ),
            "Illustrative survival (%)": np.concatenate(
                [survival_baseline, survival_shifted]
            ),
            "Scenario": (
                [tr("Baseline threshold", "เกณฑ์ฐาน")] * len(temp_grid)
                + [
                    tr("Shifted threshold", "เกณฑ์ที่เลื่อน")
                ] * len(temp_grid)
            ),
        }
    )

    fig_survival = px.line(
        survival_df,
        x="Temperature (°C)",
        y="Illustrative survival (%)",
        color="Scenario",
        title=tr(
            "Illustrative survival response",
            "การตอบสนองด้านการรอดโดยประมาณ",
        ),
    )

    fig_survival.update_layout(
        xaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
        yaxis_title=tr("Illustrative survival (%)", "อัตรารอดโดยประมาณ (%)"),
    )

    st.plotly_chart(fig_survival, use_container_width=True)

    st.subheader(
        tr("Multi-year Monte Carlo simulation", "การจำลอง Monte Carlo หลายปี")
    )

    st.write(
        tr(
            "Each simulated year receives one random temperature anomaly. "
            "The same anomaly is applied across all days within that year. "
            "The resulting interval represents scenario uncertainty under "
            "the assumptions below, not a validated climate forecast.",
            "แต่ละปีจำลองได้รับค่าความแปรปรวนของอุณหภูมิแบบสุ่มหนึ่งค่า "
            "และใช้ค่าเดียวกันตลอดทุกวันในปีนั้น ช่วงค่าที่ได้สะท้อนความไม่แน่นอน "
            "ภายใต้สมมติฐานของแบบจำลอง ไม่ใช่การพยากรณ์ภูมิอากาศที่ผ่านการตรวจสอบ",
        )
    )

    rng = np.random.default_rng(int(seed))

    years = np.arange(2026, 2037)

    annual_records = []
    daily_records = []

    for year in years:
        year_index = int(year - 2026)

        deterministic_temps = seasonal_temperature(
            days,
            year_index=year_index,
        )

        anomalies = rng.normal(
            loc=0.0,
            scale=anomaly_sd,
            size=N_MONTE_CARLO,
        )

        # One anomaly per simulated year; shared across all days.
        simulated_temps = (
            deterministic_temps[np.newaxis, :]
            + anomalies[:, np.newaxis]
        )

        simulated_survival = gaussian_survival(
            simulated_temps,
            threshold_shift=delta_g,
        )

        annual_mean_survival = simulated_survival.mean(axis=1)

        q025, q50, q975 = np.quantile(
            annual_mean_survival,
            [0.025, 0.50, 0.975],
        )

        annual_records.append(
            {
                "Year": int(year),
                "Mean temperature (°C)": float(
                    deterministic_temps.mean()
                ),
                "Median survival (%)": float(q50),
                "Survival 2.5th percentile (%)": float(q025),
                "Survival 97.5th percentile (%)": float(q975),
                "Anomaly SD (°C)": float(anomaly_sd),
                "Threshold shift (°C)": float(delta_g),
                "Monte Carlo simulations": int(N_MONTE_CARLO),
                "Random seed": int(seed),
            }
        )

        daily_mean = simulated_temps.mean(axis=0)

        daily_low = np.quantile(
            simulated_temps,
            0.025,
            axis=0,
        )

        daily_high = np.quantile(
            simulated_temps,
            0.975,
            axis=0,
        )

        for i, day in enumerate(days):
            daily_records.append(
                {
                    "Year": int(year),
                    "Day of year": int(day),
                    "Mean temperature (°C)": float(daily_mean[i]),
                    "Temperature 2.5th percentile (°C)": float(
                        daily_low[i]
                    ),
                    "Temperature 97.5th percentile (°C)": float(
                        daily_high[i]
                    ),
                }
            )

    annual_df = pd.DataFrame(annual_records)
    multiyear_daily_df = pd.DataFrame(daily_records)

    fig_mc = px.line(
        annual_df,
        x="Year",
        y="Median survival (%)",
        title=tr(
            "Multi-year median illustrative survival",
            "ค่ามัธยฐานการรอดโดยประมาณในหลายปี",
        ),
    )

    fig_mc.add_scatter(
        x=annual_df["Year"],
        y=annual_df["Survival 2.5th percentile (%)"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        name="Lower interval",
    )

    fig_mc.add_scatter(
        x=annual_df["Year"],
        y=annual_df["Survival 97.5th percentile (%)"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(31, 119, 180, 0.18)",
        name=tr("95% scenario interval", "ช่วงสถานการณ์ 95%"),
    )

    fig_mc.update_layout(
        xaxis_title=tr("Year", "ปี"),
        yaxis_title=tr("Illustrative survival (%)", "อัตรารอดโดยประมาณ (%)"),
    )

    st.plotly_chart(fig_mc, use_container_width=True)

    st.subheader(
        tr("Annual scenario summary", "สรุปสถานการณ์รายปี")
    )

    st.dataframe(
        annual_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        tr("Download annual scenario CSV", "ดาวน์โหลดข้อมูลสถานการณ์รายปี CSV"),
        data=annual_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="climate_annual_scenario.csv",
        mime="text/csv",
        key="climate_download_annual",
    )

    st.download_button(
        tr("Download seasonal temperature CSV", "ดาวน์โหลดข้อมูลอุณหภูมิตามฤดูกาล CSV"),
        data=seasonal_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="climate_seasonal_temperature.csv",
        mime="text/csv",
        key="climate_download_seasonal",
    )

    st.download_button(
        tr("Download multi-year daily CSV", "ดาวน์โหลดข้อมูลรายวันหลายปี CSV"),
        data=multiyear_daily_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="climate_multiyear_daily.csv",
        mime="text/csv",
        key="climate_download_daily",
    )

    st.warning(
        tr(
            "All climate and survival curves are illustrative scenarios. "
            "Parameters have not been calibrated as local climate forecasts "
            "or validated survival predictions. The uncertainty interval "
            "reflects only the specified Monte Carlo anomaly.",
            "เส้นกราฟภูมิอากาศและการรอดเป็นสถานการณ์สมมติ "
            "พารามิเตอร์ยังไม่ได้ปรับเทียบเพื่อใช้เป็นการพยากรณ์ภูมิอากาศเฉพาะพื้นที่ "
            "หรือการทำนายการรอดที่ผ่านการตรวจสอบ ช่วงความไม่แน่นอนสะท้อนเฉพาะ "
            "ความแปรปรวนที่กำหนดในการจำลอง Monte Carlo",
        )
    )


# ============================================================
# 12. SENSITIVITY ANALYSIS
# ============================================================
elif page == "Sensitivity Analysis":

    st.header(
        tr("Sensitivity Analysis", "วิเคราะห์ความอ่อนไหว")
    )

    st.write(
        tr(
            "Compare how changes in water temperature affect estimated "
            "survivors and illustrative financial results.",
            "เปรียบเทียบผลของการเปลี่ยนแปลงอุณหภูมิน้ำต่อจำนวนลูกปลารอด "
            "และผลทางการเงินโดยประมาณ",
        )
    )

    baseline_temp = st.slider(
        tr("Baseline temperature (°C)", "อุณหภูมิฐาน (°C)"),
        min_value=25.0,
        max_value=36.0,
        value=29.0,
        step=0.5,
        key="sensitivity_baseline_temp",
    )

    temp_range = st.slider(
        tr("Temperature range around baseline (°C)", "ช่วงอุณหภูมิรอบค่าอุณหภูมิฐาน (°C)"),
        min_value=-3.0,
        max_value=3.0,
        value=(-2.0, 2.0),
        step=0.5,
        key="sensitivity_temp_range",
    )

    sensitivity_eggs = st.number_input(
        tr("Initial eggs for sensitivity analysis", "จำนวนไข่สำหรับการวิเคราะห์"),
        min_value=1,
        value=int(eggs),
        step=100_000,
        key="sensitivity_eggs",
    )

    sensitivity_price = st.number_input(
        tr("Price per fry (THB)", "ราคาต่อลูกปลา (บาท)"),
        min_value=0.0,
        value=float(fry_price),
        step=0.10,
        key="sensitivity_price",
    )

    sensitivity_base_cost = st.number_input(
        tr("Base operating cost (THB)", "ต้นทุนดำเนินงานพื้นฐาน (บาท)"),
        min_value=0.0,
        value=float(base_cost),
        step=5_000.0,
        key="sensitivity_base_cost",
    )

    sensitivity_cooling_cost = st.number_input(
        tr("Cooling cost (THB)", "ต้นทุนระบบทำความเย็น (บาท)"),
        min_value=0.0,
        value=float(cooling_cost),
        step=5_000.0,
        key="sensitivity_cooling_cost",
    )

    include_cooling = st.checkbox(
        tr(
            "Include cooling cost in all scenarios",
            "รวมต้นทุนระบบทำความเย็นในทุกสถานการณ์",
        ),
        value=False,
        key="sensitivity_include_cooling",
    )

    temp_min = max(
        25.0,
        baseline_temp + float(temp_range[0]),
    )

    temp_max = min(
        36.0,
        baseline_temp + float(temp_range[1]),
    )

    if temp_min > temp_max:
        temp_min = temp_max = float(
            np.clip(baseline_temp, 25.0, 36.0)
        )

    scenario_temps = np.arange(
        temp_min,
        temp_max + 0.001,
        0.25,
    )

    if len(scenario_temps) == 0:
        scenario_temps = np.array([baseline_temp])

    if not np.any(np.isclose(scenario_temps, baseline_temp)):
        scenario_temps = np.append(
            scenario_temps,
            np.clip(baseline_temp, temp_min, temp_max),
        )

    scenario_temps = np.unique(np.round(scenario_temps, 2))

    def calculate_scenario(temp):
        rates = biological_rates(temp)

        fertilized = sensitivity_eggs * rates["Fertilization rate"]

        hatched = fertilized * rates["Hatching rate"]

        survivors = hatched * rates["Survival rate to 72 h"]

        revenue = survivors * sensitivity_price

        cost = sensitivity_base_cost

        if include_cooling:
            cost += sensitivity_cooling_cost

        net = revenue - cost

        return {
            "Temperature (°C)": float(temp),
            "Fertilization rate": rates["Fertilization rate"],
            "Hatching rate": rates["Hatching rate"],
            "Survival rate to 72 h": rates["Survival rate to 72 h"],
            "Estimated survivors": survivors,
            "Revenue (THB)": revenue,
            "Costs included (THB)": cost,
            "Net result (THB)": net,
        }

    scenario_df = pd.DataFrame(
        [calculate_scenario(t) for t in scenario_temps]
    )

    baseline_row = calculate_scenario(
        float(np.clip(baseline_temp, 25.0, 36.0))
    )

    scenario_df["Change in survivors"] = (
        scenario_df["Estimated survivors"]
        - baseline_row["Estimated survivors"]
    )

    scenario_df["Change in survivors (%)"] = np.where(
        baseline_row["Estimated survivors"] != 0,
        scenario_df["Change in survivors"]
        / baseline_row["Estimated survivors"]
        * 100,
        np.nan,
    )

    st.subheader(
        tr("Estimated survivors", "จำนวนลูกปลารอดโดยประมาณ")
    )

    fig_survivors = px.line(
        scenario_df,
        x="Temperature (°C)",
        y="Estimated survivors",
        markers=True,
        title=tr(
            "Estimated survivors by temperature",
            "จำนวนลูกปลารอดโดยประมาณตามอุณหภูมิ",
        ),
    )

    fig_survivors.add_vline(
        x=baseline_temp,
        line_dash="dash",
        annotation_text=tr("Baseline", "ค่าอุณหภูมิฐาน"),
    )

    fig_survivors.update_layout(
        xaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
        yaxis_title=tr("Estimated survivors", "จำนวนลูกปลารอดโดยประมาณ"),
    )

    st.plotly_chart(fig_survivors, use_container_width=True)

    st.subheader(
        tr("Illustrative net result", "ผลสุทธิโดยประมาณ")
    )

    fig_net = px.line(
        scenario_df,
        x="Temperature (°C)",
        y="Net result (THB)",
        markers=True,
        title=tr(
            "Net result by temperature",
            "ผลสุทธิตามอุณหภูมิ",
        ),
    )

    fig_net.add_hline(y=0, line_dash="dash")

    fig_net.add_vline(
        x=baseline_temp,
        line_dash="dash",
        annotation_text=tr("Baseline", "ค่าอุณหภูมิฐาน"),
    )

    fig_net.update_layout(
        xaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
        yaxis_title=tr("Net result (THB)", "ผลสุทธิ (บาท)"),
    )

    st.plotly_chart(fig_net, use_container_width=True)

    st.subheader(
        tr("Change in survivors vs. baseline", "การเปลี่ยนแปลงจำนวนลูกปลารอดเทียบกับค่าอุณหภูมิฐาน")
    )

    fig_change = px.bar(
        scenario_df,
        x="Temperature (°C)",
        y="Change in survivors",
        title=tr(
            "Change in estimated survivors",
            "การเปลี่ยนแปลงจำนวนลูกปลารอดโดยประมาณ",
        ),
    )

    fig_change.add_hline(y=0, line_dash="dash")

    fig_change.update_layout(
        xaxis_title=tr("Temperature (°C)", "อุณหภูมิ (°C)"),
        yaxis_title=tr("Change in survivors", "การเปลี่ยนแปลงจำนวนลูกปลารอด"),
    )

    st.plotly_chart(fig_change, use_container_width=True)

    st.subheader(
        tr("Scenario results table", "ตารางผลลัพธ์ของแต่ละสถานการณ์")
    )

    st.dataframe(
        scenario_df.style.format(
            {
                "Temperature (°C)": "{:.2f}",
                "Fertilization rate": "{:.1%}",
                "Hatching rate": "{:.1%}",
                "Survival rate to 72 h": "{:.1%}",
                "Estimated survivors": "{:,.0f}",
                "Revenue (THB)": "฿{:,.2f}",
                "Costs included (THB)": "฿{:,.2f}",
                "Net result (THB)": "฿{:,.2f}",
                "Change in survivors": "{:,.0f}",
                "Change in survivors (%)": "{:+.2f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        tr("Download sensitivity results CSV", "ดาวน์โหลดผลการวิเคราะห์ความอ่อนไหว CSV"),
        data=scenario_df.to_csv(index=False).encode("utf-8-sig"),
        file_name="sensitivity_analysis.csv",
        mime="text/csv",
        key="sensitivity_download",
    )

    st.info(
        tr(
            "Sensitivity results use the same two-temperature reference "
            "dataset and interpolation method. They are not independent "
            "experimental observations. Costs are included according to "
            "the checkbox above.",
            "ผลการวิเคราะห์ใช้ข้อมูลอ้างอิงสองอุณหภูมิและวิธีประมาณค่าเดียวกัน "
            "จึงไม่ใช่ผลการทดลองอิสระ ต้นทุนที่นำมาคำนวณขึ้นอยู่กับตัวเลือกด้านบน",
        )
    )


# ============================================================
# 13. AQUAMONITOR
# ============================================================
elif page == "AquaMonitor":

    st.header(
        tr("AquaMonitor", "AquaMonitor")
    )

    st.write(
        tr(
            "Open the water quality and heavy metal risk assessment module.",
            "เปิดโมดูลประเมินคุณภาพน้ำและความเสี่ยงจากโลหะหนัก",
        )
    )

    try:
        from aquamonitor import run_aquamonitor

        run_aquamonitor()

    except ImportError:
        st.error(
            tr(
                "The file aquamonitor.py could not be imported. "
                "Please confirm that it exists in the same folder as app.py.",
                "ไม่สามารถนำเข้าไฟล์ aquamonitor.py ได้ "
                "โปรดตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกับ app.py",
            )
        )


# ============================================================
# 14. METHODS AND LIMITATIONS
# ============================================================
elif page == "Methods":

    st.header(
        tr("Methods & Limitations", "วิธีการและข้อจำกัด")
    )

    st.write(
        tr(
            "This dashboard combines a small reference dataset with "
            "illustrative hatchery calculations, seasonal temperature "
            "scenarios, Monte Carlo uncertainty analysis, and sensitivity "
            "analysis. Outputs should be interpreted in the context of "
            "the assumptions listed below.",
            "แดชบอร์ดนี้รวมข้อมูลอ้างอิงที่มีจำกัดเข้ากับการคำนวณโรงเพาะฟัก "
            "สถานการณ์อุณหภูมิตามฤดูกาล การวิเคราะห์ความไม่แน่นอนด้วย "
            "Monte Carlo และการวิเคราะห์ความอ่อนไหว ควรแปลผลโดยพิจารณา "
            "สมมติฐานและข้อจำกัดต่อไปนี้",
        )
    )

    with st.expander(
        tr("1. Reference data", "1. ข้อมูลอ้างอิง"),
        expanded=True,
    ):
        reference_df = pd.DataFrame(REFERENCE)

        st.dataframe(
            reference_df,
            use_container_width=True,
            hide_index=True,
        )

        st.write(
            tr(
                "The current model uses observations at 29°C and 32°C. "
                "These two points are insufficient to characterize all "
                "temperature-dependent biological responses.",
                "แบบจำลองปัจจุบันใช้ข้อมูลที่ 29°C และ 32°C "
                "ข้อมูลเพียงสองจุดยังไม่เพียงพอที่จะอธิบายการตอบสนองทางชีววิทยา "
                "ต่ออุณหภูมิได้ครบทุกช่วง",
            )
        )

    with st.expander(
        tr("2. Hatchery calculations", "2. การคำนวณโรงเพาะฟัก")
    ):
        st.markdown(
            r"""
            \[
            N_{\mathrm{fertilized}}
            =
            N_{\mathrm{eggs}}\times r_{\mathrm{fertilization}}
            \]

            \[
            N_{\mathrm{hatched}}
            =
            N_{\mathrm{fertilized}}\times r_{\mathrm{hatching}}
            \]

            \[
            N_{\mathrm{survivors}}
            =
            N_{\mathrm{hatched}}\times r_{\mathrm{survival,72h}}
            \]
            """
        )

        st.write(
            tr(
                "The number of survivors is calculated by multiplying "
                "the successive biological rates.",
                "จำนวนลูกปลารอดคำนวณจากการคูณอัตราทางชีววิทยาในแต่ละขั้นตอน",
            )
        )

    with st.expander(
        tr("3. Interpolation", "3. การประมาณค่า")
    ):
        st.markdown(
            r"""
            \[
            r(T)
            =
            r_1+
            \frac{T-T_1}{T_2-T_1}(r_2-r_1)
            \]
            """
        )

        st.write(
            tr(
                "Linear interpolation is applied between 29°C and 32°C. "
                "Outside that range, the endpoint value is used. "
                "This is a simplifying assumption, not evidence that "
                "biological rates remain constant beyond the observed range.",
                "ใช้การประมาณค่าเชิงเส้นระหว่าง 29°C และ 32°C "
                "และใช้ค่าที่ปลายช่วงเมื่ออยู่นอกช่วงดังกล่าว "
                "นี่เป็นสมมติฐานเพื่อให้คำนวณได้ ไม่ใช่หลักฐานว่าอัตราทางชีววิทยา "
                "คงที่เมื่ออยู่นอกช่วงอุณหภูมิที่มีข้อมูล",
            )
        )

    with st.expander(
        tr("4. Seasonal temperature model", "4. แบบจำลองอุณหภูมิตามฤดูกาล")
    ):
        st.markdown(
            r"""
            \[
            T(d,y)
            =
            \left(T_{\mathrm{mean}}+\alpha y\right)
            +
            \left(A_0e^{-\beta y}\right)
            \sin\left(\frac{2\pi(d-D_{\mathrm{peak}})}{365}\right)
            \]
            """
        )

        st.write(
            tr(
                "The model describes an illustrative seasonal cycle. "
                "It is not calibrated to a specific station or a validated "
                "climate projection.",
                "แบบจำลองแสดงวงจรอุณหภูมิตามฤดูกาลเพื่อประกอบการศึกษา "
                "ไม่ได้ปรับเทียบกับสถานีตรวจวัดเฉพาะแห่ง "
                "และไม่ใช่การคาดการณ์ภูมิอากาศที่ผ่านการตรวจสอบ",
            )
        )

    with st.expander(
        tr("5. Temperature-dependent survival scenario", "5. สถานการณ์การรอดตามอุณหภูมิ")
    ):
        st.markdown(
            r"""
            \[
            S(T)
            =
            S_{\max}
            \exp\left(
            -\frac{1}{2}
            \left(\frac{T-T_{\mathrm{opt}}}{\sigma}\right)^2
            \right)
            \]
            """
        )

        st.write(
            tr(
                "The displayed survival curve is illustrative. Its "
                "parameters have not been validated against a complete "
                "experimental dataset. The threshold-related penalty is "
                "an additional scenario assumption.",
                "เส้นโค้งการรอดเป็นเพียงตัวอย่างประกอบการศึกษา "
                "พารามิเตอร์ยังไม่ได้รับการตรวจสอบกับชุดข้อมูลการทดลองที่ครบถ้วน "
                "ส่วนการลดค่าตามเกณฑ์อุณหภูมิเป็นสมมติฐานเพิ่มเติมของสถานการณ์",
            )
        )

    with st.expander(
        tr("6. Monte Carlo analysis", "6. การวิเคราะห์ Monte Carlo")
    ):
        st.markdown(
            r"""
            \[
            T_{\mathrm{sim}}(d,y,i)
            =
            T(d,y)+\varepsilon_{y,i}
            \]

            \[
            \varepsilon_{y,i}
            \sim
            \mathcal{N}(0,\sigma_{\varepsilon}^{2})
            \]
            """
        )

        st.write(
            tr(
                "Each simulation samples one annual temperature anomaly "
                "and applies it across the days in that year. The 2.5th "
                "and 97.5th percentiles describe a scenario interval under "
                "the assumed distribution, not a guarantee of real-world coverage.",
                "แต่ละการจำลองสุ่มค่าความแปรปรวนของอุณหภูมิหนึ่งค่าต่อปี "
                "และใช้ค่านั้นกับทุกวันในปีเดียวกัน เปอร์เซ็นไทล์ที่ 2.5 และ 97.5 "
                "แสดงช่วงสถานการณ์ภายใต้การแจกแจงที่สมมติไว้ "
                "ไม่ใช่การรับประกันความครอบคลุมของผลในโลกจริง",
            )
        )

    with st.expander(
        tr("7. Threshold scenario", "7. สถานการณ์การเลื่อนเกณฑ์")
    ):
        st.write(
            tr(
                "The threshold shift is a user-selected hypothetical "
                "parameter. It should not be interpreted as an experimentally "
                "confirmed adaptation or climate response.",
                "ค่าการเลื่อนเกณฑ์เป็นพารามิเตอร์สมมติที่ผู้ใช้เลือก "
                "ไม่ควรตีความว่าเป็นการปรับตัวหรือการตอบสนองต่อภูมิอากาศ "
                "ที่ได้รับการยืนยันจากการทดลอง",
            )
        )

    with st.expander(
        tr("8. Sensitivity analysis", "8. การวิเคราะห์ความอ่อนไหว")
    ):
        st.write(
            tr(
                "Sensitivity analysis changes the input temperature while "
                "holding other selected inputs constant. It illustrates "
                "model behavior under the stated assumptions and does not "
                "establish causal effects.",
                "การวิเคราะห์ความอ่อนไหวเปลี่ยนอุณหภูมิขณะที่คงค่าปัจจัยอื่น "
                "ตามที่กำหนดไว้ เพื่อแสดงพฤติกรรมของแบบจำลองภายใต้สมมติฐาน "
                "แต่ไม่สามารถยืนยันความสัมพันธ์เชิงเหตุและผลได้",
            )
        )

    with st.expander(
        tr("9. Economic assumptions", "9. สมมติฐานทางเศรษฐศาสตร์")
    ):
        st.write(
            tr(
                "Revenue is estimated from surviving fish multiplied by "
                "the assumed selling price. Costs include only the base "
                "operating cost and, where specified, the cooling cost. "
                "Labor, feed, energy, mortality outside the modeled stage, "
                "capital, transport, and other expenses are not included "
                "unless entered explicitly.",
                "รายได้ประมาณจากจำนวนลูกปลารอดคูณราคาขายที่กำหนด "
                "ต้นทุนรวมเฉพาะต้นทุนดำเนินงานพื้นฐานและต้นทุนทำความเย็น "
                "ตามที่ระบุ ยังไม่รวมค่าแรง อาหาร พลังงาน การตายที่อยู่นอกช่วง "
                "ที่จำลอง เงินลงทุน การขนส่ง และค่าใช้จ่ายอื่น "
                "เว้นแต่จะนำมาระบุในการคำนวณอย่างชัดเจน",
            )
        )

    with st.expander(
        tr("10. Limitations and reproducibility", "10. ข้อจำกัดและการทำซ้ำ")
    ):
        st.markdown(
            tr(
                """
                - The biological reference dataset contains only two temperatures.
                - The climate model is illustrative and not locally calibrated.
                - The survival curve and threshold penalty are scenario assumptions.
                - Monte Carlo uncertainty reflects only the specified random anomaly.
                - Economic estimates exclude costs that are not entered.
                - Use the random seed to reproduce the same simulation.
                - Validate assumptions with experimental data before using results
                  for operational or policy decisions.
                """,
                """
                - ข้อมูลอ้างอิงทางชีววิทยามีเพียงสองอุณหภูมิ
                - แบบจำลองภูมิอากาศเป็นตัวอย่างและไม่ได้ปรับเทียบเฉพาะพื้นที่
                - เส้นโค้งการรอดและค่าปรับตามเกณฑ์เป็นสมมติฐานของสถานการณ์
                - ความไม่แน่นอนจาก Monte Carlo สะท้อนเฉพาะค่าความแปรปรวนที่กำหนด
                - ผลทางเศรษฐศาสตร์ไม่รวมต้นทุนที่ไม่ได้กรอก
                - สามารถใช้ค่าเริ่มต้นสุ่มเดิมเพื่อทำซ้ำการจำลอง
                - ควรตรวจสอบสมมติฐานกับข้อมูลทดลองก่อนใช้ตัดสินใจในการดำเนินงานหรือนโยบาย
                """,
            )
        )

    st.info(
        tr(
            "This dashboard is intended for exploratory analysis and "
            "education. It does not replace experimental validation, "
            "professional advice, or a locally validated model.",
            "แดชบอร์ดนี้จัดทำขึ้นเพื่อการสำรวจและการศึกษา "
            "ไม่สามารถทดแทนการตรวจสอบด้วยการทดลอง คำแนะนำจากผู้เชี่ยวชาญ "
            "หรือแบบจำลองที่ผ่านการตรวจสอบในพื้นที่ได้",
        )
    )


# ============================================================
# 15. FOOTER
# ============================================================
st.divider()

st.caption(
    tr(
        "Catfish Thermal Risk Dashboard | Exploratory model — "
        "interpret outputs with the stated assumptions and limitations.",
        "แดชบอร์ดความเสี่ยงด้านอุณหภูมิของปลาดุก | "
        "แบบจำลองเพื่อการศึกษา — โปรดแปลผลภายใต้สมมติฐานและข้อจำกัดที่ระบุ",
    )
)

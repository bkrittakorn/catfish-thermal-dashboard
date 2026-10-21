"""
Catfish Thermal Risk Dashboard
==============================
Single-file Streamlit application (English / Thai).

File layout (search for the "# ====" banners):
    0. Imports
    1. Scientific parameters and models   (values unchanged from the original app.py / aquamonitor.py)
    2. Translation dictionary             (single source of all interface text)
    3. Language, state and formatting helpers
    4. Styling (CSS, Plotly theme)
    5. UI components
    6. Pages: overview, calculator, climate, sensitivity, aquamonitor, methods
    7. Sidebar and main entry point

All model formulas, parameters and reference values are reproduced exactly from
the original app.py and aquamonitor.py. Only presentation, language handling
and code organisation were changed.
"""

# ============================================================
# 0. IMPORTS
# ============================================================
import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# 1. SCIENTIFIC PARAMETERS AND MODELS
# ============================================================

# --- 1.1 Source-study observations (reproduced in Supplementary File S1) ---
REFERENCE = {
    "Temperature (°C)": [29, 32],
    "Fertilization rate": [0.677, 0.590],
    "Hatching rate": [0.434, 0.266],
    "Survival rate to 72 h": [0.449, 0.0],
}

# --- 1.2 Supplementary File S1: reproducible scenario parameters ---
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

# Dashboard temperature domain (unchanged)
T_MIN_DOMAIN = 25.0
T_MAX_DOMAIN = 36.0

# --- 1.3 AquaMonitor: reference doses and exposure assumption ---
RFD = {
    "Cr": 0.003,
    "Pb": 0.0035,
    "Ni": 0.020,
    "Cd": 0.001,
}
METAL_ORDER = ["Cr", "Pb", "Ni", "Cd"]

# Assumed daily fish consumption in kg/day.
# This is a model assumption and should be verified before real use.
FISH_CONSUMPTION_RATE = 0.0215


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
# 2. TRANSLATION DICTIONARY  (key -> (English, Thai))
# ============================================================
# Scientific names, variable symbols, formulas, units and numbers are kept
# identical in both languages. Use {name} placeholders for dynamic values.
TEXT = {
    # ---------- App shell ----------
    "app.page_title": (
        "Catfish Thermal Risk Dashboard",
        "แดชบอร์ดความเสี่ยงด้านอุณหภูมิต่อการเพาะเลี้ยงปลาดุก",
    ),
    "app.name": (
        "Catfish Thermal Risk Dashboard",
        "แดชบอร์ดความเสี่ยงด้านอุณหภูมิต่อการเพาะเลี้ยงปลาดุก",
    ),
    "app.tagline": (
        "Interactive decision-support prototype for hybrid catfish hatchery research.",
        "ต้นแบบเครื่องมือสนับสนุนการตัดสินใจเชิงโต้ตอบสำหรับงานวิจัยการเพาะฟักปลาดุกลูกผสม",
    ),
    "app.disclaimer": (
        "Exploratory research prototype. Outputs are scenario estimates, "
        "not experimental results.",
        "ต้นแบบเพื่อการวิจัยเชิงสำรวจ ผลลัพธ์เป็นค่าประมาณตามสถานการณ์ "
        "ไม่ใช่ผลการทดลองจริง",
    ),
    "lang.label": ("Language", "ภาษา"),
    "nav.title": ("Navigation", "เมนูนำทาง"),
    "nav.label": ("Choose a page", "เลือกหน้า"),
    "nav.overview": ("Overview", "ภาพรวม"),
    "nav.calculator": ("Hatchery Calculator", "เครื่องคำนวณการเพาะฟัก"),
    "nav.climate": ("Climate Simulation", "แบบจำลองสภาพภูมิอากาศ"),
    "nav.sensitivity": ("Sensitivity Analysis", "การวิเคราะห์ความไว"),
    "nav.aquamonitor": ("AquaMonitor", "AquaMonitor"),
    "nav.methods": ("Methods", "ระเบียบวิธี"),
    "side.assump": ("Hatchery assumptions", "สมมติฐานการเพาะฟัก"),
    "side.assump_note": (
        "Used by the Overview and Hatchery Calculator pages.",
        "ใช้กับหน้าภาพรวมและเครื่องคำนวณการเพาะฟัก",
    ),

    # ---------- Shared inputs ----------
    "in.eggs": ("Initial eggs", "จำนวนไข่เริ่มต้น"),
    "in.eggs.help": (
        "Number of eggs at the start of the hatchery cycle.",
        "จำนวนไข่เมื่อเริ่มรอบการเพาะฟัก",
    ),
    "in.price": ("Price per fry (THB)", "ราคาต่อลูกปลา (THB)"),
    "in.price.help": (
        "Assumed selling price of one fry.",
        "ราคาขายสมมติของลูกปลาหนึ่งตัว",
    ),
    "in.base_cost": ("Base operating cost (THB)", "ต้นทุนดำเนินงานพื้นฐาน (THB)"),
    "in.base_cost.help": (
        "Fixed operating cost deducted from revenue.",
        "ต้นทุนดำเนินงานคงที่ที่นำไปหักจากรายได้",
    ),
    "in.cooling": ("Cooling cost (THB)", "ต้นทุนระบบทำความเย็น (THB)"),
    "in.cooling.help": (
        "Fixed cooling cost. Cooling effectiveness is not modelled.",
        "ต้นทุนระบบทำความเย็นคงที่ ไม่ได้จำลองประสิทธิภาพการลดอุณหภูมิ",
    ),
    "in.temp": ("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
    "in.temp.help": (
        "Select a water temperature between 25 and 36 °C.",
        "เลือกอุณหภูมิน้ำระหว่าง 25 ถึง 36 °C",
    ),

    # ---------- Shared metrics / labels ----------
    "m.fert": ("Fertilization rate", "อัตราการปฏิสนธิ"),
    "m.hatch": ("Hatching rate", "อัตราการฟัก"),
    "m.surv72": ("Survival to 72 h", "อัตรารอดถึง 72 h"),
    "m.survivors": ("Estimated survivors", "จำนวนลูกปลารอดโดยประมาณ"),
    "m.revenue": ("Estimated revenue", "รายได้โดยประมาณ"),
    "m.revenue_ill": ("Illustrative revenue", "รายได้เชิงตัวอย่าง"),
    "m.cost": ("Total specified costs", "ต้นทุนรวมที่ระบุ"),
    "m.net": ("Illustrative net result", "ผลลัพธ์สุทธิเชิงตัวอย่าง"),
    "m.net.help": (
        "Illustrative revenue minus the specified operating and cooling costs.",
        "รายได้เชิงตัวอย่างหักด้วยต้นทุนดำเนินงานและต้นทุนระบบทำความเย็นที่ระบุ",
    ),
    "m.fert.help": (
        "Interpolated between the source observations at 29 and 32 °C.",
        "ประมาณค่าระหว่างค่าสังเกตจากงานต้นทางที่ 29 และ 32 °C",
    ),
    "m.survivors.help": (
        "Initial eggs × fertilization × hatching × 72-h survival.",
        "ไข่เริ่มต้น × อัตราปฏิสนธิ × อัตราการฟัก × อัตรารอด 72 h",
    ),
    "badge.scenario": ("Scenario estimate", "ค่าประมาณตามสถานการณ์"),
    "badge.observed": ("Source observation", "ค่าสังเกตจากงานต้นทาง"),

    # ---------- Overview ----------
    "ov.desc": (
        "Water-temperature effects on hatchery output, estimated from two "
        "source-study observations.",
        "ผลของอุณหภูมิน้ำต่อผลผลิตการเพาะฟัก ประมาณจากค่าสังเกตสองจุดของงานต้นทาง",
    ),
    "ov.status_title": (
        "Temperature position relative to source observations",
        "ตำแหน่งอุณหภูมิเทียบกับค่าสังเกตจากงานต้นทาง",
    ),
    "ov.status_low": (
        "At or below 29 °C: rates are held at the values observed at 29 °C.",
        "ที่หรือต่ำกว่า 29 °C: อัตราคงที่เท่ากับค่าที่สังเกตได้ที่ 29 °C",
    ),
    "ov.status_mid": (
        "Between 29 and 32 °C: rates are linearly interpolated and were not observed directly.",
        "ระหว่าง 29 ถึง 32 °C: อัตราได้จากการประมาณค่าเชิงเส้น ไม่ได้สังเกตโดยตรง",
    ),
    "ov.status_high": (
        "At or above 32 °C: rates are held at the values observed at 32 °C "
        "(72-h survival 0%).",
        "ที่หรือสูงกว่า 32 °C: อัตราคงที่เท่ากับค่าที่สังเกตได้ที่ 32 °C "
        "(อัตรารอด 72 h เท่ากับ 0%)",
    ),
    "ov.bio": ("Biological estimates", "ค่าประมาณทางชีววิทยา"),
    "ov.econ": ("Hatchery economic scenario", "สถานการณ์เศรษฐศาสตร์ของการเพาะฟัก"),
    "ov.curve": (
        "Survival rate analysis across temperature",
        "การวิเคราะห์อัตรารอดตามอุณหภูมิ",
    ),
    "ov.curve_title": (
        "Biological rates versus water temperature",
        "อัตราทางชีววิทยาเทียบกับอุณหภูมิน้ำ",
    ),
    "ov.curve_cap": (
        "Markers show the two source-study observations (29 and 32 °C). Lines "
        "show the linear interpolation used by the dashboard, held constant "
        "outside that range. The dashed vertical line marks the selected "
        "temperature. The lines are a model approximation, not measured data.",
        "เครื่องหมายแสดงค่าสังเกตสองจุดจากงานต้นทาง (29 และ 32 °C) "
        "เส้นแสดงการประมาณค่าเชิงเส้นที่แดชบอร์ดใช้ และคงค่าคงที่นอกช่วงดังกล่าว "
        "เส้นประแนวตั้งแสดงอุณหภูมิที่เลือก เส้นเหล่านี้เป็นการประมาณของแบบจำลอง "
        "ไม่ใช่ข้อมูลที่วัดได้",
    ),
    "ov.warn": (
        "Important limitation: biological rates are based on observations "
        "at 29°C and 32°C. The dashboard linearly interpolates between "
        "these temperatures and holds rates at the nearest endpoint "
        "outside this range. These are illustrative estimates, not "
        "validated predictions of hatchery performance. The economic "
        "result includes only the costs specified in the calculator.",
        "ข้อจำกัดสำคัญ: อัตราทางชีววิทยาอ้างอิงจากค่าสังเกตที่ 29°C และ 32°C "
        "แดชบอร์ดใช้การประมาณค่าเชิงเส้นระหว่างอุณหภูมิทั้งสอง "
        "และคงค่าไว้ที่จุดปลายที่ใกล้ที่สุดเมื่ออยู่นอกช่วงดังกล่าว "
        "ผลลัพธ์เป็นค่าประมาณเชิงตัวอย่าง ไม่ใช่การทำนายผลการเพาะฟักที่ผ่านการตรวจสอบความถูกต้องแล้ว "
        "ผลทางเศรษฐศาสตร์รวมเฉพาะต้นทุนที่ระบุในเครื่องคำนวณเท่านั้น",
    ),
    "axis.temp": ("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
    "axis.rate": ("Rate (proportion)", "อัตรา (สัดส่วน)"),
    "legend.selected": ("Selected temperature", "อุณหภูมิที่เลือก"),
    "legend.obs_suffix": ("(observed)", "(ค่าสังเกต)"),
    "legend.interp_suffix": ("(model)", "(แบบจำลอง)"),

    # ---------- Shared: assumptions expander ----------
    "assump.title": ("View calculation assumptions", "ดูสมมติฐานการคำนวณ"),
    "assump.temp": ("Water temperature: {v} °C", "อุณหภูมิน้ำ: {v} °C"),
    "assump.eggs": ("Initial egg count: {v}", "จำนวนไข่เริ่มต้น: {v}"),
    "assump.price": ("Price per fry: ฿{v}", "ราคาต่อลูกปลา: ฿{v}"),
    "assump.opcost": ("Operating cost: ฿{v}", "ต้นทุนดำเนินงาน: ฿{v}"),
    "assump.cooling": ("Cooling cost: ฿{v}", "ต้นทุนระบบทำความเย็น: ฿{v}"),

    # ---------- Calculator ----------
    "calc.desc": (
        "Estimate hatchery output and illustrative economics "
        "under a selected water-temperature scenario.",
        "ประมาณผลผลิตการเพาะฟักและเศรษฐศาสตร์เชิงตัวอย่าง "
        "ภายใต้สถานการณ์อุณหภูมิน้ำที่เลือก",
    ),
    "calc.s1": ("1. Biological estimates", "1. ค่าประมาณทางชีววิทยา"),
    "calc.s2": ("2. Estimated production", "2. ผลผลิตโดยประมาณ"),
    "calc.s3": ("3. Illustrative economic results", "3. ผลทางเศรษฐศาสตร์เชิงตัวอย่าง"),
    "stage.eggs": ("Initial eggs", "ไข่เริ่มต้น"),
    "stage.fert": ("Estimated fertilized eggs", "ไข่ที่ปฏิสนธิ (ประมาณ)"),
    "stage.hatched": ("Estimated hatched larvae", "ลูกปลาที่ฟักออก (ประมาณ)"),
    "stage.surv": ("Estimated survivors at 72 h", "ลูกปลารอดที่ 72 h (ประมาณ)"),
    "col.stage": ("Production stage", "ขั้นตอนการผลิต"),
    "col.count": ("Estimated count", "จำนวนโดยประมาณ"),
    "calc.chart_title": (
        "Estimated production at each stage",
        "ผลผลิตโดยประมาณในแต่ละขั้นตอน",
    ),
    "calc.chart_cap": (
        "Counts are scenario estimates computed from interpolated rates; "
        "they are not experimental counts.",
        "จำนวนเป็นค่าประมาณตามสถานการณ์ที่คำนวณจากอัตราที่ประมาณค่า "
        "ไม่ใช่จำนวนที่นับได้จากการทดลอง",
    ),
    "axis.stage": ("Production stage", "ขั้นตอนการผลิต"),
    "axis.count": ("Estimated count (n)", "จำนวนโดยประมาณ (n)"),
    "calc.warn": (
        "These are illustrative estimates. Biological rates are based on "
        "observations at 29°C and 32°C, with linear interpolation between "
        "them and endpoint values held outside that range. Actual production "
        "may differ. Total costs include only the operating and cooling costs "
        "entered in the dashboard.",
        "ผลลัพธ์เหล่านี้เป็นค่าประมาณเชิงตัวอย่าง อัตราทางชีววิทยาอ้างอิงจากค่าสังเกตที่ "
        "29°C และ 32°C โดยประมาณค่าเชิงเส้นระหว่างสองจุดและคงค่าที่จุดปลายเมื่ออยู่นอกช่วง "
        "ผลผลิตจริงอาจแตกต่างออกไป ต้นทุนรวมประกอบด้วยเฉพาะต้นทุนดำเนินงานและ"
        "ต้นทุนระบบทำความเย็นที่กรอกในแดชบอร์ด",
    ),

    # ---------- Climate ----------
    "clim.desc": (
        "Reproducible seasonal and multiyear temperature scenarios "
        "based on Supplementary File S1. These are illustrative scenarios, "
        "not calibrated local climate forecasts.",
        "สถานการณ์อุณหภูมิตามฤดูกาลและหลายปีที่ทำซ้ำได้ ตามเอกสารเสริม S1 "
        "เป็นสถานการณ์เชิงตัวอย่าง ไม่ใช่การพยากรณ์ภูมิอากาศท้องถิ่นที่ผ่านการปรับเทียบ",
    ),
    "clim.controls": ("Scenario controls", "ตัวควบคุมสถานการณ์"),
    "in.anomaly_sd": (
        "Annual temperature anomaly SD (°C)",
        "ส่วนเบี่ยงเบนมาตรฐานของความผิดปกติอุณหภูมิรายปี (°C)",
    ),
    "in.anomaly_sd.help": (
        "S1 default: 0.30°C. One anomaly is shared by all days in each year.",
        "ค่าเริ่มต้นใน S1: 0.30°C ความผิดปกติหนึ่งค่าใช้ร่วมกันทุกวันในแต่ละปี",
    ),
    "in.delta_g": (
        "Hypothetical threshold change Δg (°C/year)",
        "การเปลี่ยนแปลงค่าเกณฑ์เชิงสมมติ Δg (°C/year)",
    ),
    "in.delta_g.help": (
        "Sensitivity assumption, not a measured evolutionary rate.",
        "สมมติฐานเพื่อการวิเคราะห์ความไว ไม่ใช่อัตราวิวัฒนาการที่วัดได้",
    ),
    "in.seed": ("Random seed", "ค่าเริ่มต้นการสุ่ม (random seed)"),
    "in.seed.help": (
        "Fixes the Monte Carlo draws so results are reproducible. S1 default: 20260929.",
        "กำหนดการสุ่มแบบมอนติคาร์โลให้ทำซ้ำผลได้ ค่าเริ่มต้นใน S1: 20260929",
    ),
    "clim.a": (
        "A. Annual seasonal vulnerability cycle",
        "A. วัฏจักรความเปราะบางตามฤดูกาลในรอบปี",
    ),
    "clim.a_cap": (
        "The survival curve is the illustrative Gaussian response specified "
        "in S1; it is not the same as the observed fertilization or hatching rates.",
        "เส้นโค้งอัตรารอดเป็นการตอบสนองแบบเกาส์เซียนเชิงตัวอย่างตามที่ระบุใน S1 "
        "ซึ่งไม่เหมือนกับอัตราการปฏิสนธิหรืออัตราการฟักที่สังเกตได้จริง",
    ),
    "kpi.peak_temp": ("Peak baseline temperature", "อุณหภูมิฐานสูงสุด"),
    "kpi.peak_day": ("Day of peak temperature", "วันที่อุณหภูมิสูงสุด"),
    "kpi.days_above": (
        "Days above static threshold",
        "จำนวนวันที่สูงกว่าค่าเกณฑ์คงที่",
    ),
    "kpi.days_above.help": (
        "Number of days in the 2026 baseline curve (no anomaly) with "
        "temperature above 30.75 °C.",
        "จำนวนวันในเส้นฐานปี 2026 (ไม่รวมความผิดปกติ) ที่อุณหภูมิสูงกว่า 30.75 °C",
    ),
    "kpi.max_surv": (
        "Maximum illustrative 72-h survival",
        "อัตรารอด 72 h สูงสุด (เชิงตัวอย่าง)",
    ),
    "kpi.cap": (
        "Indicators are read directly from the 2026 baseline scenario curves below.",
        "ตัวชี้วัดอ่านจากเส้นสถานการณ์ฐานปี 2026 ด้านล่างโดยตรง",
    ),
    "clim.seasonal_title": (
        "Seasonal water temperature scenario",
        "สถานการณ์อุณหภูมิน้ำตามฤดูกาล",
    ),
    "clim.survival_title": (
        "Illustrative temperature-dependent 72-h survival",
        "อัตรารอด 72 h ที่ขึ้นกับอุณหภูมิ (เชิงตัวอย่าง)",
    ),
    "clim.seasonal_cap": (
        "Scenario baseline for a representative year (year index 0). "
        "Not an observed temperature record.",
        "เส้นฐานของสถานการณ์สำหรับปีตัวแทน (ดัชนีปี 0) ไม่ใช่บันทึกอุณหภูมิที่สังเกตได้",
    ),
    "clim.survival_cap": (
        "Gaussian response from S1 (Smax, Topt, sigma). It is an illustrative "
        "equation, not a validated prediction of farm-level survival.",
        "การตอบสนองแบบเกาส์เซียนจาก S1 (Smax, Topt, sigma) เป็นสมการเชิงตัวอย่าง "
        "ไม่ใช่การทำนายอัตรารอดระดับฟาร์มที่ผ่านการตรวจสอบแล้ว",
    ),
    "axis.doy": ("Day of year", "วันที่ในรอบปี"),
    "axis.surv_pct": ("72-h larval survival (%)", "อัตรารอดของลูกปลา 72 h (%)"),
    "legend.threshold_line": ("Static threshold", "ค่าเกณฑ์คงที่"),
    "clim.b": (
        "B. Multiyear stochastic climate scenario",
        "B. สถานการณ์ภูมิอากาศเชิงสุ่มหลายปี",
    ),
    "clim.b_cap": (
        "The main line shows the daily seasonal temperature baseline, "
        "including the assumed long-term warming trend and seasonal-amplitude "
        "change. The shaded band adds the 2.5th and 97.5th percentiles of "
        "annual temperature anomalies from 10,000 Monte Carlo simulations. "
        "The band represents uncertainty under the specified scenario "
        "assumptions, not a calibrated local climate forecast. "
        "The annual summary table reports values at each year's baseline.",
        "เส้นหลักแสดงเส้นฐานอุณหภูมิตามฤดูกาลรายวัน รวมแนวโน้มการอุ่นขึ้นระยะยาวและ"
        "การเปลี่ยนแปลงแอมพลิจูดตามฤดูกาลที่สมมติไว้ แถบสีเพิ่มเปอร์เซ็นไทล์ที่ 2.5 และ 97.5 "
        "ของความผิดปกติอุณหภูมิรายปีจากการจำลองมอนติคาร์โล 10,000 ครั้ง "
        "แถบนี้แสดงความไม่แน่นอนภายใต้สมมติฐานของสถานการณ์ที่กำหนด "
        "ไม่ใช่การพยากรณ์ภูมิอากาศท้องถิ่นที่ผ่านการปรับเทียบ "
        "ตารางสรุปรายปีรายงานค่าที่เส้นฐานของแต่ละปี",
    ),
    "clim.b_title": (
        "Daily Temperature Scenario and Annual Uncertainty (2026–2036)",
        "สถานการณ์อุณหภูมิรายวันและความไม่แน่นอนรายปี (2026–2036)",
    ),
    "axis.year_proj": ("Projection year", "ปีตามสถานการณ์จำลอง"),
    "legend.mean": ("Scenario baseline temperature", "อุณหภูมิฐานตามสถานการณ์"),
    "legend.interval": ("95% simulation interval", "ช่วงการจำลอง 95%"),
    "legend.static": ("Static threshold", "ค่าเกณฑ์คงที่"),
    "legend.changing": ("Hypothetical changing threshold", "ค่าเกณฑ์เปลี่ยนแปลงเชิงสมมติ"),
    "hover.interval": ("95% simulation interval", "ช่วงการจำลอง 95%"),
    "hover.temp": ("Temperature", "อุณหภูมิ"),
    "hover.day": ("Day", "วันที่"),
    "hover.year": ("Year", "ปี"),
    "hover.survival": ("Survival", "อัตรารอด"),
    "clim.annual": ("Annual scenario data", "ข้อมูลสถานการณ์รายปี"),
    "col.year": ("Year", "ปี"),
    "col.mean_annual": (
        "Mean annual temperature baseline (°C)",
        "เส้นฐานอุณหภูมิเฉลี่ยรายปี (°C)",
    ),
    "col.amplitude": ("Seasonal amplitude (°C)", "แอมพลิจูดตามฤดูกาล (°C)"),
    "col.anom_low": ("Annual anomaly lower 95% (°C)", "ความผิดปกติรายปี ขอบล่าง 95% (°C)"),
    "col.anom_high": ("Annual anomaly upper 95% (°C)", "ความผิดปกติรายปี ขอบบน 95% (°C)"),
    "col.static": ("Static threshold (°C)", "ค่าเกณฑ์คงที่ (°C)"),
    "col.changing": (
        "Hypothetical changing threshold (°C)",
        "ค่าเกณฑ์เปลี่ยนแปลงเชิงสมมติ (°C)",
    ),
    "col.doy": ("Day of year", "วันที่ในรอบปี"),
    "col.temp": ("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
    "col.surv_pct": ("72-h larval survival (%)", "อัตรารอดของลูกปลา 72 h (%)"),
    "col.mean_temp": ("Mean scenario temperature (°C)", "อุณหภูมิเฉลี่ยตามสถานการณ์ (°C)"),
    "col.low_temp": ("Lower 95% simulation interval (°C)", "ช่วงการจำลอง 95% ขอบล่าง (°C)"),
    "col.up_temp": ("Upper 95% simulation interval (°C)", "ช่วงการจำลอง 95% ขอบบน (°C)"),
    "dl.annual": (
        "Download annual climate scenario CSV",
        "ดาวน์โหลด CSV สถานการณ์ภูมิอากาศรายปี",
    ),
    "dl.seasonal": (
        "Download daily seasonal scenario CSV",
        "ดาวน์โหลด CSV สถานการณ์ตามฤดูกาลรายวัน",
    ),
    "dl.multiyear": (
        "Download multiyear daily simulation CSV",
        "ดาวน์โหลด CSV การจำลองรายวันหลายปี",
    ),
    "clim.warn": (
        "Limitations: the seasonal temperatures, annual warming trend, "
        "anomaly distribution, and changing threshold are scenario assumptions "
        "from Supplementary File S1. They are not locally calibrated forecasts. "
        "The survival curve is an illustrative equation and must not be "
        "interpreted as a validated prediction of farm-level survival.",
        "ข้อจำกัด: อุณหภูมิตามฤดูกาล แนวโน้มการอุ่นขึ้นรายปี การแจกแจงความผิดปกติ "
        "และค่าเกณฑ์ที่เปลี่ยนแปลง เป็นสมมติฐานของสถานการณ์จากเอกสารเสริม S1 "
        "ไม่ใช่การพยากรณ์ที่ปรับเทียบกับพื้นที่จริง เส้นโค้งอัตรารอดเป็นสมการเชิงตัวอย่าง "
        "และต้องไม่ตีความว่าเป็นการทำนายอัตรารอดระดับฟาร์มที่ผ่านการตรวจสอบแล้ว",
    ),

    # ---------- Sensitivity ----------
    "sens.desc": (
        "Explore how temperature assumptions affect estimated larval "
        "survival and illustrative financial outcomes. All results depend "
        "on the selected assumptions and the biological-rate model.",
        "สำรวจว่าสมมติฐานด้านอุณหภูมิส่งผลต่ออัตรารอดของลูกปลาโดยประมาณและ"
        "ผลทางการเงินเชิงตัวอย่างอย่างไร ผลลัพธ์ทั้งหมดขึ้นอยู่กับสมมติฐานที่เลือก"
        "และแบบจำลองอัตราทางชีววิทยา",
    ),
    "sens.baseline_set": ("Set baseline assumptions", "กำหนดสมมติฐานฐาน"),
    "in.base_temp": ("Baseline temperature (°C)", "อุณหภูมิฐาน (°C)"),
    "in.temp_range": (
        "Temperature change range (°C)",
        "ช่วงการเปลี่ยนแปลงอุณหภูมิ (°C)",
    ),
    "in.temp_range.help": (
        "Offsets added to the baseline temperature. The scenario range is "
        "limited to 25–36 °C.",
        "ค่าที่บวกเพิ่มจากอุณหภูมิฐาน ช่วงของสถานการณ์จำกัดอยู่ที่ 25–36 °C",
    ),
    "in.include_cooling": (
        "Include cooling cost in all scenarios",
        "รวมต้นทุนระบบทำความเย็นในทุกสถานการณ์",
    ),
    "in.include_cooling.help": (
        "If checked, the specified cooling cost is deducted from every "
        "scenario. This does not model cooling effectiveness or energy use.",
        "หากเลือก ต้นทุนระบบทำความเย็นที่ระบุจะถูกหักจากทุกสถานการณ์ "
        "ไม่ได้จำลองประสิทธิภาพการลดอุณหภูมิหรือการใช้พลังงาน",
    ),
    "sens.baseline_results": ("Baseline results", "ผลลัพธ์ที่อุณหภูมิฐาน"),
    "sens.baseline_cap": (
        "Baseline rates: fertilization {f}, hatching {h}, 72-h survival {s}. "
        "Costs deducted: ฿{c}.",
        "อัตราที่อุณหภูมิฐาน: การปฏิสนธิ {f} การฟัก {h} อัตรารอด 72 h {s} "
        "ต้นทุนที่หัก: ฿{c}",
    ),
    "sens.clipped": (
        "Some requested temperatures fall outside the supported "
        "25–36°C range. The sensitivity analysis uses only "
        "temperatures within this range.",
        "อุณหภูมิบางค่าที่ร้องขออยู่นอกช่วงที่รองรับ 25–36°C "
        "การวิเคราะห์ความไวจึงใช้เฉพาะอุณหภูมิภายในช่วงนี้",
    ),
    "sens.effect": ("Effect of temperature change", "ผลของการเปลี่ยนแปลงอุณหภูมิ"),
    "sens.chart1": (
        "Estimated survivors across temperature scenarios",
        "จำนวนลูกปลารอดโดยประมาณตามสถานการณ์อุณหภูมิ",
    ),
    "sens.chart2": (
        "Illustrative net financial result across scenarios",
        "ผลลัพธ์สุทธิทางการเงินเชิงตัวอย่างตามสถานการณ์",
    ),
    "sens.chart3": (
        "Change in estimated survivors relative to baseline",
        "การเปลี่ยนแปลงของจำนวนลูกปลารอดโดยประมาณเทียบกับอุณหภูมิฐาน",
    ),
    "sens.chart_cap": (
        "All curves are model scenarios under fixed egg number, price and cost "
        "assumptions; they are not experimental outcomes.",
        "ทุกเส้นเป็นสถานการณ์จากแบบจำลองภายใต้สมมติฐานจำนวนไข่ ราคา และต้นทุนคงที่ "
        "ไม่ใช่ผลลัพธ์จากการทดลอง",
    ),
    "sens.breakeven": ("Net result = 0", "ผลลัพธ์สุทธิ = 0"),
    "sens.baseline_line": ("No change", "ไม่เปลี่ยนแปลง"),
    "axis.temp_change": ("Temperature change (°C)", "การเปลี่ยนแปลงอุณหภูมิ (°C)"),
    "axis.survivors": ("Estimated survivors (n)", "จำนวนลูกปลารอดโดยประมาณ (n)"),
    "axis.net": ("Net result (THB)", "ผลลัพธ์สุทธิ (THB)"),
    "axis.dsurv": (
        "Change in estimated survivors (n)",
        "การเปลี่ยนแปลงจำนวนลูกปลารอด (n)",
    ),
    "sens.table": ("Scenario results", "ผลลัพธ์รายสถานการณ์"),
    "col.dT": ("Temperature change (°C)", "การเปลี่ยนแปลงอุณหภูมิ (°C)"),
    "col.scn_temp": ("Scenario temperature (°C)", "อุณหภูมิตามสถานการณ์ (°C)"),
    "col.fert": ("Fertilization rate", "อัตราการปฏิสนธิ"),
    "col.hatch": ("Hatching rate", "อัตราการฟัก"),
    "col.surv72": ("72-h survival rate", "อัตรารอด 72 h"),
    "col.survivors": ("Estimated survivors", "จำนวนลูกปลารอดโดยประมาณ"),
    "col.revenue": ("Revenue (THB)", "รายได้ (THB)"),
    "col.opcost": ("Operating cost (THB)", "ต้นทุนดำเนินงาน (THB)"),
    "col.coolcost": ("Cooling cost included (THB)", "ต้นทุนระบบทำความเย็นที่รวม (THB)"),
    "col.totcost": ("Total costs (THB)", "ต้นทุนรวม (THB)"),
    "col.net": ("Net result (THB)", "ผลลัพธ์สุทธิ (THB)"),
    "col.dsurv": (
        "Change in survivors vs baseline",
        "การเปลี่ยนแปลงจำนวนลูกปลารอดเทียบกับอุณหภูมิฐาน",
    ),
    "col.dnet": (
        "Change in net result vs baseline (THB)",
        "การเปลี่ยนแปลงผลลัพธ์สุทธิเทียบกับอุณหภูมิฐาน (THB)",
    ),
    "dl.sens": ("Download sensitivity results (CSV)", "ดาวน์โหลดผลการวิเคราะห์ความไว (CSV)"),
    "sens.info": (
        "Interpretation and limitations: this analysis changes temperature "
        "while holding egg number, price, and costs fixed. Cooling is treated "
        "only as a fixed cost when selected; its effect on water temperature "
        "is not modelled. Biological rates between the source observations "
        "are interpolated, and rates outside the observed range are held at "
        "the endpoints. These scenario outputs are not validated forecasts "
        "or proof of causal effects.",
        "การตีความและข้อจำกัด: การวิเคราะห์นี้เปลี่ยนเฉพาะอุณหภูมิ "
        "โดยคงจำนวนไข่ ราคา และต้นทุนไว้คงที่ ระบบทำความเย็นถูกนับเป็นต้นทุนคงที่เมื่อเลือกเท่านั้น "
        "ไม่ได้จำลองผลต่ออุณหภูมิน้ำ อัตราทางชีววิทยาระหว่างค่าสังเกตได้จากการประมาณค่า "
        "และอัตรานอกช่วงที่สังเกตคงค่าไว้ที่จุดปลาย ผลลัพธ์ตามสถานการณ์เหล่านี้ไม่ใช่"
        "การพยากรณ์ที่ผ่านการตรวจสอบหรือหลักฐานของความสัมพันธ์เชิงสาเหตุ",
    ),

    # ---------- AquaMonitor ----------
    "am.subtitle": (
        "Water Quality & Heavy Metal Risk Assessment in Fish",
        "การประเมินคุณภาพน้ำและความเสี่ยงจากโลหะหนักในปลา",
    ),
    "am.desc": (
        "Enter measured heavy metal concentrations in fish muscle "
        "to calculate screening-level Hazard Quotients (HQ) "
        "and the Hazard Index (HI).",
        "กรอกค่าความเข้มข้นโลหะหนักที่ตรวจวัดได้ในกล้ามเนื้อปลา "
        "เพื่อคำนวณค่าคัดกรอง HQ และดัชนีความเป็นอันตราย HI",
    ),
    "am.info": (
        "This tool is intended for preliminary screening and scenario "
        "exploration only. It does not certify food safety. Verify the "
        "reference doses (RfDs), exposure assumptions, units, and "
        "calculation methods against appropriate scientific sources "
        "before using the results for real-world decisions.",
        "เครื่องมือนี้ใช้สำหรับการคัดกรองเบื้องต้นและการสำรวจสถานการณ์เท่านั้น "
        "ไม่ใช่การรับรองความปลอดภัยของอาหาร ควรตรวจสอบค่าอ้างอิงความเป็นพิษ "
        "(RfD) สมมติฐานการรับสัมผัส หน่วย และวิธีคำนวณกับแหล่งข้อมูลทางวิชาการ "
        "ที่เหมาะสมก่อนนำผลไปใช้ประกอบการตัดสินใจจริง",
    ),
    "am.s1": (
        "1. Heavy Metal Concentrations in Fish Muscle",
        "1. ความเข้มข้นโลหะหนักในกล้ามเนื้อปลา",
    ),
    "am.s1_cap": (
        "Unit: mg/kg wet weight. Leave a field blank if no measurement "
        "is available. Missing measurements are not treated as zero.",
        "หน่วย: mg/kg น้ำหนักเปียก เว้นช่องว่างหากไม่มีผลตรวจวัด "
        "ข้อมูลที่ไม่มีจะไม่ถูกนับเป็นศูนย์",
    ),
    "metal.Cr": ("Total Chromium (Cr)", "โครเมียมรวม (Cr)"),
    "metal.Pb": ("Lead (Pb)", "ตะกั่ว (Pb)"),
    "metal.Ni": ("Nickel (Ni)", "นิกเกิล (Ni)"),
    "metal.Cd": ("Cadmium (Cd)", "แคดเมียม (Cd)"),
    "in.cr": ("Total Chromium, Cr (mg/kg)", "โครเมียมรวม Cr (mg/kg)"),
    "in.pb": ("Lead, Pb (mg/kg)", "ตะกั่ว Pb (mg/kg)"),
    "in.ni": ("Nickel, Ni (mg/kg)", "นิกเกิล Ni (mg/kg)"),
    "in.cd": ("Cadmium, Cd (mg/kg)", "แคดเมียม Cd (mg/kg)"),
    "in.metal.help": (
        "Enter the measured concentration in fish muscle.",
        "กรอกค่าความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
    ),
    "am.exposure": ("Exposure assumptions", "สมมติฐานการรับสัมผัส"),
    "in.bw": ("Consumer body weight (kg)", "น้ำหนักตัวผู้บริโภค (kg)"),
    "in.bw.help": (
        "Body weight is used in the screening calculation.",
        "น้ำหนักตัวใช้ในการคำนวณเพื่อการคัดกรอง",
    ),
    "am.ir_cap": (
        "Assumed daily fish consumption: {v} kg/day.",
        "ปริมาณการบริโภคปลาต่อวันที่สมมติ: {v} kg/day",
    ),
    "am.s2": (
        "2. Optional Sediment Chromium Scenario",
        "2. สถานการณ์โครเมียมในตะกอน (ไม่บังคับ)",
    ),
    "am.s2_desc": (
        "Optionally enter an initial sediment chromium concentration "
        "to explore hypothetical future scenarios.",
        "หากมีข้อมูล สามารถกรอกความเข้มข้นโครเมียมเริ่มต้นในตะกอน "
        "เพื่อสำรวจสถานการณ์ในอนาคตที่สมมติขึ้นได้",
    ),
    "in.sediment": (
        "Initial sediment chromium concentration (mg/kg)",
        "ความเข้มข้นโครเมียมเริ่มต้นในตะกอน (mg/kg)",
    ),
    "in.horizon": ("Simulation period", "ระยะเวลาจำลอง"),
    "in.horizon.fmt": ("{x} years", "{x} ปี"),
    "btn.analyze": ("Analyze Results", "วิเคราะห์ผล"),
    "btn.reset": ("Clear inputs", "ล้างข้อมูลที่กรอก"),
    "am.prompt": (
        "Enter available measurements and select Analyze Results "
        "to calculate screening indicators.",
        "กรอกข้อมูลที่มี แล้วกดปุ่มวิเคราะห์ผลเพื่อคำนวณตัวชี้วัดการคัดกรอง",
    ),
    "am.err_nodata": (
        "No data entered. Enter at least one measured metal "
        "concentration or a sediment chromium concentration.",
        "ยังไม่มีข้อมูล โปรดกรอกความเข้มข้นโลหะหนักอย่างน้อยหนึ่งรายการ "
        "หรือกรอกความเข้มข้นโครเมียมในตะกอน",
    ),
    "am.err_bw": (
        "Body weight must be greater than zero.",
        "น้ำหนักตัวต้องมากกว่าศูนย์",
    ),
    "am.s3": ("3. Screening Summary", "3. สรุปผลการคัดกรอง"),
    "am.k_metals": ("Metals with measurements", "จำนวนโลหะที่มีผลตรวจวัด"),
    "am.k_hi": ("Hazard Index (HI)", "ดัชนีความเป็นอันตราย (HI)"),
    "am.k_hi.help": (
        "Sum of the Hazard Quotients of the metals entered.",
        "ผลรวมของค่า HQ ของโลหะที่กรอก",
    ),
    "am.k_above": ("HQ values above 1", "จำนวนค่า HQ ที่มากกว่า 1"),
    "am.hi_high": (
        "The calculated HI exceeds 1 under the selected assumptions. "
        "This is a screening signal, not proof of harm. Seek a "
        "qualified exposure and toxicological risk assessment.",
        "ค่า HI ที่คำนวณได้มากกว่า 1 ภายใต้สมมติฐานที่เลือก "
        "เป็นสัญญาณสำหรับการคัดกรอง ไม่ใช่หลักฐานยืนยันว่าจะเกิดอันตราย "
        "ควรให้ผู้เชี่ยวชาญประเมินการรับสัมผัสและความเสี่ยงทางพิษวิทยา",
    ),
    "am.hi_low": (
        "The calculated HI is at or below 1 under the selected "
        "assumptions. This does not establish that the fish is safe. "
        "The result depends on the assumed exposure rate, reference "
        "doses, and the metals measured.",
        "ค่า HI ที่คำนวณได้ไม่เกิน 1 ภายใต้สมมติฐานที่เลือก "
        "แต่ไม่ได้ยืนยันว่าปลอดภัย ผลขึ้นอยู่กับอัตราการรับสัมผัส "
        "ค่าอ้างอิงความเป็นพิษ และชนิดโลหะที่ตรวจวัด",
    ),
    "am.no_fish": (
        "No fish-muscle metal concentrations were provided. "
        "HQ and HI were not calculated.",
        "ไม่มีข้อมูลความเข้มข้นโลหะหนักในกล้ามเนื้อปลา "
        "จึงไม่ได้คำนวณ HQ และ HI",
    ),
    "am.s4": ("4. Heavy Metal Concentrations", "4. ความเข้มข้นโลหะหนัก"),
    "am.conc_title": (
        "Measured concentrations in fish muscle",
        "ความเข้มข้นที่ตรวจวัดได้ในกล้ามเนื้อปลา",
    ),
    "am.conc_cap": (
        "Bars show the concentrations you entered (measured values supplied by the user).",
        "แท่งแสดงความเข้มข้นที่คุณกรอก (ค่าตรวจวัดที่ผู้ใช้ป้อน)",
    ),
    "axis.metal": ("Metal", "โลหะ"),
    "axis.conc": ("Concentration (mg/kg)", "ความเข้มข้น (mg/kg)"),
    "am.s5": ("5. Hazard Quotient (HQ)", "5. ค่าดัชนีอันตรายรายสาร (HQ)"),
    "am.hq_title": (
        "Screening Hazard Quotient by metal",
        "ค่า HQ สำหรับการคัดกรองแยกตามโลหะ",
    ),
    "am.hq_cap": (
        "Red bars exceed the HQ = 1 screening line. HQ is a screening ratio "
        "computed from your inputs and assumed exposure parameters, not a "
        "measured health outcome.",
        "แท่งสีแดงคือค่าที่เกินเส้นคัดกรอง HQ = 1 ค่า HQ เป็นอัตราส่วนเพื่อการคัดกรอง "
        "คำนวณจากข้อมูลที่กรองและพารามิเตอร์การรับสัมผัสที่สมมติ "
        "ไม่ใช่ผลลัพธ์ทางสุขภาพที่วัดได้",
    ),
    "am.table": ("Screening results table", "ตารางผลการคัดกรอง"),
    "col.metal": ("Metal", "โลหะ"),
    "col.conc": ("Concentration (mg/kg)", "ความเข้มข้น (mg/kg)"),
    "col.rfd": ("Assumed RfD (mg/kg/day)", "ค่า RfD ที่สมมติ (mg/kg/day)"),
    "col.hq": ("HQ", "HQ"),
    "col.hi": ("HI", "HI"),
    "col.bw": ("Body weight (kg)", "น้ำหนักตัว (kg)"),
    "col.ir": (
        "Assumed fish consumption (kg/day)",
        "ปริมาณบริโภคปลาที่สมมติ (kg/day)",
    ),
    "col.record": ("Record type", "ประเภทระเบียน"),
    "col.scenario": ("Sediment scenario", "สถานการณ์ตะกอน"),
    "col.sed_cr": ("Sediment chromium (mg/kg)", "โครเมียมในตะกอน (mg/kg)"),
    "rec.fish": ("Fish muscle concentration", "ความเข้มข้นในกล้ามเนื้อปลา"),
    "rec.sediment": ("Sediment scenario", "สถานการณ์ตะกอน"),
    "rec.summary": ("Summary", "สรุป"),
    "am.s6": (
        "6. Sediment Chromium Scenario Analysis",
        "6. การวิเคราะห์สถานการณ์โครเมียมในตะกอน",
    ),
    "am.s6_desc": (
        "The following scenarios are hypothetical illustrations. "
        "Their input and decay parameters are assumptions and should "
        "not be interpreted as site-calibrated forecasts.",
        "สถานการณ์ต่อไปนี้เป็นตัวอย่างสมมติ พารามิเตอร์อัตราการเพิ่ม "
        "และการสลายตัวเป็นสมมติฐาน ไม่ใช่การพยากรณ์ที่ปรับเทียบ "
        "กับพื้นที่จริง",
    ),
    "scn.A": ("A - No Intervention", "A - ไม่ดำเนินมาตรการ"),
    "scn.B": ("B - Source Reduction", "B - ลดแหล่งกำเนิด"),
    "scn.C": ("C - Intensive Control", "C - ควบคุมเข้มข้น"),
    "am.sed_title": (
        "Illustrative sediment chromium scenarios",
        "สถานการณ์โครเมียมในตะกอนโดยประมาณ",
    ),
    "am.sed_cap": (
        "Hypothetical scenarios with assumed parameters; not forecasts "
        "calibrated to a real site.",
        "สถานการณ์สมมติที่ใช้พารามิเตอร์ที่สมมติ ไม่ใช่การพยากรณ์ที่ปรับเทียบกับพื้นที่จริง",
    ),
    "axis.year": ("Year", "ปี"),
    "axis.sed": ("Sediment chromium (mg/kg)", "โครเมียมในตะกอน (mg/kg)"),
    "am.sed_summary": (
        "Scenario summary at year {h}",
        "สรุปสถานการณ์ในปีที่ {h}",
    ),
    "am.s7": ("7. Export Results", "7. ส่งออกผลลัพธ์"),
    "dl.am": ("Download Results (CSV)", "ดาวน์โหลดผลลัพธ์ (CSV)"),
    "am.limits": ("Important limitations", "ข้อจำกัดสำคัญ"),
    "am.limits_text": (
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
    ),
    "am.footer": (
        "AquaMonitor | Preliminary screening and scenario exploration only.",
        "AquaMonitor | ใช้สำหรับการคัดกรองเบื้องต้นและสำรวจสถานการณ์เท่านั้น",
    ),

    # ---------- Methods ----------
    "me.desc": (
        "Methods, data sources and limitations",
        "ระเบียบวิธี แหล่งข้อมูล และข้อจำกัด",
    ),
    "me.1": ("1. Reference biological observations", "1. ค่าสังเกตทางชีววิทยาที่ใช้อ้างอิง"),
    "me.1_t": (
        "The prototype uses the two temperature-specific observations "
        "provided in the source study.",
        "ต้นแบบนี้ใช้ค่าสังเกตเฉพาะอุณหภูมิสองจุดที่ได้จากงานศึกษาต้นทาง",
    ),
    "me.1_cap": (
        "Source-study values reproduced in Supplementary File S1. "
        "The two temperature observations do not establish a complete "
        "biological response curve.",
        "ค่าจากงานศึกษาต้นทางที่นำมาแสดงไว้ในเอกสารเสริม S1 "
        "ค่าสังเกตสองอุณหภูมิไม่เพียงพอที่จะกำหนดเส้นโค้งการตอบสนองทางชีววิทยาที่สมบูรณ์",
    ),
    "col.temp_ref": ("Temperature (°C)", "อุณหภูมิ (°C)"),
    "me.2": ("2. Hatchery calculation", "2. การคำนวณการเพาะฟัก"),
    "me.2_t": (
        "Estimated survivors are calculated by multiplying the initial "
        "egg count by fertilization, hatching and 72-hour survival rates. "
        "Illustrative revenue is estimated survivors multiplied by the "
        "user-entered price per fry. The net result subtracts the specified "
        "operating and cooling costs.",
        "จำนวนลูกปลารอดโดยประมาณคำนวณจากจำนวนไข่เริ่มต้นคูณด้วยอัตราการปฏิสนธิ "
        "อัตราการฟัก และอัตรารอด 72 ชั่วโมง รายได้เชิงตัวอย่างคือจำนวนลูกปลารอดโดยประมาณ"
        "คูณด้วยราคาต่อลูกปลาที่ผู้ใช้กรอก ผลลัพธ์สุทธิคือรายได้หักด้วยต้นทุนดำเนินงาน"
        "และต้นทุนระบบทำความเย็นที่ระบุ",
    ),
    "me.3": ("3. Biological-rate approximation", "3. การประมาณอัตราทางชีววิทยา"),
    "me.3_t": (
        "For the Overview, Hatchery Calculator and Sensitivity Analysis "
        "pages, the prototype linearly interpolates between the observed "
        "rates at 29°C and 32°C. Outside that interval, rates are held at "
        "the nearest endpoint. This is a simplifying approximation, not a "
        "validated biological response model.",
        "สำหรับหน้าภาพรวม เครื่องคำนวณการเพาะฟัก และการวิเคราะห์ความไว "
        "ต้นแบบนี้ประมาณค่าเชิงเส้นระหว่างอัตราที่สังเกตได้ที่ 29°C และ 32°C "
        "นอกช่วงดังกล่าวคงอัตราไว้ที่จุดปลายที่ใกล้ที่สุด "
        "เป็นการประมาณแบบง่าย ไม่ใช่แบบจำลองการตอบสนองทางชีววิทยาที่ผ่านการตรวจสอบแล้ว",
    ),
    "me.4": (
        "4. Seasonal and multiyear climate scenario",
        "4. สถานการณ์ภูมิอากาศตามฤดูกาลและหลายปี",
    ),
    "me.4_t": (
        "The Climate Simulation page uses the illustrative seasonal and "
        "multiyear scenario parameters from Supplementary File S1: mean "
        "temperature 28.5°C, initial seasonal amplitude 3.5°C, peak day 115, "
        "mean warming parameter 0.08°C/year, and amplitude-change parameter "
        "0.03°C/year.",
        "หน้าแบบจำลองสภาพภูมิอากาศใช้พารามิเตอร์สถานการณ์ตามฤดูกาลและหลายปีเชิงตัวอย่างจาก"
        "เอกสารเสริม S1: อุณหภูมิเฉลี่ย 28.5°C แอมพลิจูดตามฤดูกาลเริ่มต้น 3.5°C "
        "วันที่ร้อนสูงสุดคือวันที่ 115 พารามิเตอร์การอุ่นขึ้นเฉลี่ย 0.08°C/year "
        "และพารามิเตอร์การเปลี่ยนแปลงแอมพลิจูด 0.03°C/year",
    ),
    "me.5": ("5. Seasonal survival illustration", "5. ภาพประกอบอัตรารอดตามฤดูกาล"),
    "me.5_t": (
        "The seasonal survival curve uses the illustrative Gaussian equation "
        "in Supplementary File S1, with Smax = 44.9%, Topt = 29°C and "
        "sigma = 1°C. This curve is displayed separately from the observed "
        "fertilization and hatching rates; it is not a validated prediction "
        "of farm-level survival.",
        "เส้นโค้งอัตรารอดตามฤดูกาลใช้สมการเกาส์เซียนเชิงตัวอย่างในเอกสารเสริม S1 "
        "โดย Smax = 44.9%, Topt = 29°C และ sigma = 1°C เส้นโค้งนี้แสดงแยกจากอัตราการปฏิสนธิ"
        "และอัตราการฟักที่สังเกตได้ และไม่ใช่การทำนายอัตรารอดระดับฟาร์มที่ผ่านการตรวจสอบแล้ว",
    ),
    "me.6": ("6. Monte Carlo uncertainty", "6. ความไม่แน่นอนจากมอนติคาร์โล"),
    "me.6_t": (
        "The multiyear climate scenario uses 10,000 Monte Carlo simulations. "
        "Each simulated year receives one normally distributed temperature "
        "anomaly shared by all days in that year. The default anomaly "
        "standard deviation is 0.30°C. The displayed band is based on the "
        "2.5th and 97.5th percentiles of simulated annual anomalies and "
        "represents a simulation interval under the specified assumptions, "
        "not a confidence interval estimated from observed local climate data "
        "or a calibrated climate forecast.",
        "สถานการณ์ภูมิอากาศหลายปีใช้การจำลองมอนติคาร์โล 10,000 ครั้ง "
        "แต่ละปีที่จำลองได้รับความผิดปกติอุณหภูมิแบบแจกแจงปกติหนึ่งค่า "
        "ซึ่งใช้ร่วมกันทุกวันในปีนั้น ส่วนเบี่ยงเบนมาตรฐานของความผิดปกติค่าเริ่มต้นคือ 0.30°C "
        "แถบที่แสดงอิงเปอร์เซ็นไทล์ที่ 2.5 และ 97.5 ของความผิดปกติรายปีที่จำลอง "
        "และแทนช่วงการจำลองภายใต้สมมติฐานที่กำหนด ไม่ใช่ช่วงความเชื่อมั่นที่ประมาณจาก"
        "ข้อมูลภูมิอากาศท้องถิ่นที่สังเกตได้ และไม่ใช่การพยากรณ์ภูมิอากาศที่ปรับเทียบแล้ว",
    ),
    "me.7": ("7. Threshold scenario", "7. สถานการณ์ค่าเกณฑ์"),
    "me.7_t": (
        "The changing threshold is a hypothetical sensitivity line starting "
        "at 30.75°C in 2026. Its annual change is user-adjustable within "
        "the interface. It must not be interpreted as a measured genetic "
        "adaptation rate or a demonstrated evolutionary outcome.",
        "ค่าเกณฑ์ที่เปลี่ยนแปลงเป็นเส้นวิเคราะห์ความไวเชิงสมมติ เริ่มที่ 30.75°C ในปี 2026 "
        "การเปลี่ยนแปลงรายปีปรับได้ในหน้าจอ ต้องไม่ตีความว่าเป็นอัตราการปรับตัวทางพันธุกรรม"
        "ที่วัดได้หรือผลทางวิวัฒนาการที่พิสูจน์แล้ว",
    ),
    "me.8": ("8. Sensitivity Analysis", "8. การวิเคราะห์ความไว"),
    "me.8_t": (
        "Sensitivity Analysis varies temperature while holding egg number, "
        "price and selected costs fixed. Cooling cost can be included as a "
        "fixed expense, but the model does not simulate cooling-system "
        "performance, energy consumption or the resulting change in water "
        "temperature.",
        "การวิเคราะห์ความไวเปลี่ยนอุณหภูมิโดยคงจำนวนไข่ ราคา และต้นทุนที่เลือกไว้คงที่ "
        "สามารถรวมต้นทุนระบบทำความเย็นเป็นค่าใช้จ่ายคงที่ได้ แต่แบบจำลองไม่ได้จำลอง"
        "ประสิทธิภาพของระบบทำความเย็น การใช้พลังงาน หรือการเปลี่ยนแปลงของอุณหภูมิน้ำที่เกิดขึ้น",
    ),
    "me.9": ("9. Limitations", "9. ข้อจำกัด"),
    "me.9_t": (
        "This dashboard is an exploratory scenario tool. It is not a "
        "calibrated local climate forecast, a validated farm-production "
        "model, or an experimentally fitted biological response model. "
        "Only two source-study temperature observations are used for the "
        "fertilization, hatching and 72-hour survival calculations. "
        "Economic outputs depend on user-entered assumptions. Independent "
        "validation and additional experimental and local climate data are "
        "required before operational or policy decisions are based on these results.",
        "แดชบอร์ดนี้เป็นเครื่องมือสำรวจสถานการณ์ ไม่ใช่การพยากรณ์ภูมิอากาศท้องถิ่นที่ปรับเทียบแล้ว "
        "แบบจำลองผลผลิตฟาร์มที่ผ่านการตรวจสอบ หรือแบบจำลองการตอบสนองทางชีววิทยาที่ปรับค่า"
        "จากการทดลอง ใช้ค่าสังเกตจากงานต้นทางเพียงสองอุณหภูมิสำหรับการคำนวณการปฏิสนธิ "
        "การฟัก และอัตรารอด 72 ชั่วโมง ผลทางเศรษฐศาสตร์ขึ้นอยู่กับสมมติฐานที่ผู้ใช้กรอก "
        "ต้องมีการตรวจสอบอย่างอิสระ รวมถึงข้อมูลการทดลองและข้อมูลภูมิอากาศท้องถิ่นเพิ่มเติม "
        "ก่อนนำผลไปใช้ตัดสินใจเชิงปฏิบัติการหรือเชิงนโยบาย",
    ),
    "me.10": ("10. Reproducibility", "10. การทำซ้ำผลลัพธ์"),
    "me.10_t": (
        "The climate scenario uses a configurable random seed, with "
        "20260929 as the default, and 10,000 Monte Carlo simulations. "
        "Downloaded CSV files contain scenario outputs for further inspection.",
        "สถานการณ์ภูมิอากาศใช้ค่าเริ่มต้นการสุ่มที่ปรับได้ โดยค่าเริ่มต้นคือ 20260929 "
        "และการจำลองมอนติคาร์โล 10,000 ครั้ง ไฟล์ CSV ที่ดาวน์โหลดมีผลลัพธ์ของสถานการณ์"
        "สำหรับตรวจสอบเพิ่มเติม",
    ),
    "me.11": (
        "11. AquaMonitor: Hazard Quotient and sediment scenarios",
        "11. AquaMonitor: ค่าดัชนีอันตรายรายสารและสถานการณ์ตะกอน",
    ),
    "me.11_t1": (
        "AquaMonitor computes a screening Hazard Quotient for each metal "
        "entered, HQ = C × IR / (BW × RfD), where C is the fish-muscle "
        "concentration (mg/kg wet weight), IR is the assumed daily fish "
        "consumption ({ir} kg/day), BW is the consumer body weight (kg) and "
        "RfD is the assumed reference dose (mg/kg/day). The Hazard Index is "
        "the sum of the HQ values of the metals entered. Missing "
        "measurements are excluded, not treated as zero.",
        "AquaMonitor คำนวณค่า HQ เพื่อการคัดกรองสำหรับโลหะแต่ละชนิดที่กรอก "
        "HQ = C × IR / (BW × RfD) โดย C คือความเข้มข้นในกล้ามเนื้อปลา "
        "(mg/kg น้ำหนักเปียก) IR คือปริมาณการบริโภคปลาต่อวันที่สมมติ ({ir} kg/day) "
        "BW คือน้ำหนักตัวผู้บริโภค (kg) และ RfD คือค่าอ้างอิงความเป็นพิษที่สมมติ (mg/kg/day) "
        "ดัชนี HI คือผลรวมของค่า HQ ของโลหะที่กรอก ข้อมูลที่ไม่มีจะถูกตัดออก ไม่ถูกนับเป็นศูนย์",
    ),
    "me.11_rfd": ("Assumed reference doses", "ค่าอ้างอิงความเป็นพิษที่สมมติ"),
    "me.11_t2": (
        "The sediment chromium scenarios are hypothetical. Concentration "
        "follows C(t) = C0·exp(−k·t) + (I/k)·(1 − exp(−k·t)), or C0 + I·t when "
        "k = 0, and is never allowed to fall below zero. Scenario A uses "
        "I = C0 and k = 0.05; scenario B uses I = 0.85·C0 and k = 0.07; "
        "scenario C uses I = 0 and k = 0.10 (I in mg/kg per year, k per year). "
        "These parameters are illustrative assumptions and are not calibrated "
        "to any site.",
        "สถานการณ์โครเมียมในตะกอนเป็นสถานการณ์สมมติ ความเข้มข้นเป็นไปตาม "
        "C(t) = C0·exp(−k·t) + (I/k)·(1 − exp(−k·t)) หรือ C0 + I·t เมื่อ k = 0 "
        "และไม่ปล่อยให้ต่ำกว่าศูนย์ สถานการณ์ A ใช้ I = C0 และ k = 0.05 "
        "สถานการณ์ B ใช้ I = 0.85·C0 และ k = 0.07 สถานการณ์ C ใช้ I = 0 และ k = 0.10 "
        "(I หน่วย mg/kg ต่อปี, k ต่อปี) พารามิเตอร์เหล่านี้เป็นสมมติฐานเชิงตัวอย่าง "
        "และไม่ได้ปรับเทียบกับพื้นที่ใดๆ",
    ),
}


# ============================================================
# 3. LANGUAGE, STATE AND FORMATTING HELPERS
# ============================================================
LANG_OPTIONS = ["English", "ไทย"]
PAGE_IDS = ["overview", "calculator", "climate", "sensitivity", "aquamonitor", "methods"]

# Every persistent widget key and its default value. Values are seeded once and
# re-asserted on every run so that inputs survive page changes and language
# switches (Streamlit otherwise drops a widget's state when the widget is not
# rendered, or when its label changes).
WIDGET_DEFAULTS = {
    "language": "English",
    "page": "overview",
    # Sidebar hatchery assumptions
    "eggs": 5_000_000,
    "fry_price": 1.50,
    "base_cost": 100_000.0,
    "cooling_cost": 80_000.0,
    # Overview / calculator
    "ov_temp": 29.0,
    "calc_temp": 29.0,
    # Climate
    "clim_sd": float(E_SD),
    "clim_dg": float(DELTA_G),
    "clim_seed": int(SEED),
    # Sensitivity
    "sens_base_temp": 29.0,
    "sens_temp_range": (-2.0, 2.0),
    "sens_eggs": 5_000_000,
    "sens_price": 1.50,
    "sens_cost": 100_000.0,
    "sens_cooling": 80_000.0,
    "sens_include_cooling": False,
    # AquaMonitor (None = blank field)
    "am_cr": None,
    "am_pb": None,
    "am_ni": None,
    "am_cd": None,
    "am_weight": 50.0,
    "am_sediment": None,
    "am_horizon": 5,
    "am_analyzed": False,
}


def init_state():
    """Seed defaults and keep every widget value alive across reruns."""
    for key, default in WIDGET_DEFAULTS.items():
        st.session_state.setdefault(key, default)
        # Re-assigning moves the value into the persistent session store so it
        # is not discarded when its widget is hidden or relabelled.
        st.session_state[key] = st.session_state[key]


def is_thai():
    return st.session_state.get("language", "English") == "ไทย"


def t(key, **kwargs):
    """Central translation lookup: key -> text in the selected language."""
    english, thai = TEXT[key]
    text = thai if is_thai() else english
    return text.format(**kwargs) if kwargs else text


def metal_label(metal):
    return t(f"metal.{metal}")


def relabel(df):
    """Rename internal translation-key columns to the selected language."""
    return df.rename(columns={c: t(c) for c in df.columns if c in TEXT})


def csv_bytes(df):
    return relabel(df).to_csv(index=False).encode("utf-8-sig")


def _streamlit_version():
    parts = []
    for piece in st.__version__.split(".")[:2]:
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


# Newer Streamlit replaces use_container_width with width="stretch".
_STRETCH = (
    {"width": "stretch"}
    if _streamlit_version() >= (1, 50)
    else {"use_container_width": True}
)


def show_table(df, formats=None, index=False):
    """Display a DataFrame whose columns are translation keys."""
    shown = relabel(df)
    if formats:
        shown = shown.style.format(
            {t(col): fmt for col, fmt in formats.items() if t(col) in shown.columns}
        )
    st.dataframe(shown, hide_index=not index, **_STRETCH)


# ============================================================
# 4. STYLING
# ============================================================
NAVY = "#123B4A"
TEAL = "#1F7A8C"
BLUE = "#2F5D8A"
SLATE = "#5B7083"
AMBER = "#D9822B"
RED = "#C0392B"
GRID = "#E3EBEF"
BAND = "rgba(31, 122, 140, 0.18)"

# Consistent semantic colours across all charts
COLOR_TEMPERATURE = BLUE
COLOR_FERT = TEAL
COLOR_HATCH = BLUE
COLOR_SURVIVAL = NAVY
COLOR_THRESHOLD_STATIC = AMBER
COLOR_THRESHOLD_CHANGING = RED
COLOR_SCENARIO = {"A": AMBER, "B": BLUE, "C": TEAL}

FONT_STACK = "Sarabun, 'Noto Sans Thai', 'Segoe UI', Roboto, Arial, sans-serif"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');

html, body, .stApp, [data-testid="stSidebar"], .stMarkdown, p, li, label,
h1, h2, h3, h4, h5, button, input, textarea, select, .stCaption,
[data-testid="stMetricLabel"], [data-testid="stMetricValue"],
[data-testid="stDataFrame"] {
    font-family: 'Sarabun', 'Noto Sans Thai', 'Segoe UI', Roboto, Arial, sans-serif;
}
[data-testid="stIconMaterial"], .material-icons, .material-symbols-rounded {
    font-family: 'Material Symbols Rounded', 'Material Icons' !important;
}

.stApp { background-color: #F4F8FA; color: #1F2D3A; }
.block-container { padding-top: 3.5rem; padding-bottom: 3rem; max-width: 1180px; }

[data-testid="stSidebar"] {
    background-color: #E8F1F4;
    border-right: 1px solid #D4E2E8;
}
[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }

h1 { color: #123B4A; font-weight: 700; letter-spacing: -0.3px; }
h2, h3, h4 { color: #1B5565; font-weight: 600; }

/* Page header */
.pg-head {border-bottom: 2px solid #CFE0E6; padding-top: 0.3rem; padding-bottom: 0.9rem; margin-bottom: 1.4rem;}
.pg-head h1 { margin: 0 0 0.25rem 0; padding: 0; font-size: 2rem; line-height: 1.25; }
.pg-head p { margin: 0; color: #4A6270; font-size: 1.02rem; line-height: 1.55; max-width: 62rem; }

/* Sidebar brand */
.brand { margin-bottom: 0.8rem; }
.brand .name { font-weight: 700; color: #123B4A; font-size: 1.12rem; line-height: 1.3; }
.brand .tag { color: #4A6270; font-size: 0.86rem; line-height: 1.45; margin-top: 0.35rem; }
.side-note { color: #4A6270; font-size: 0.85rem; line-height: 1.45; margin: -0.3rem 0 0.6rem 0; }

/* Cards */
[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #DCE7EC;
    border-left: 4px solid #1F7A8C;
    padding: 16px 18px;
    border-radius: 10px;
    box-shadow: 0 1px 6px rgba(20, 60, 75, 0.05);
}
[data-testid="stMetricLabel"] { color: #4A6270; }
[data-testid="stMetricValue"] { color: #123B4A; font-weight: 600; }

div[data-testid="stPlotlyChart"] {
    background-color: #FFFFFF;
    border: 1px solid #DCE7EC;
    border-radius: 10px;
    padding: 8px;
}
div[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stExpander"] { background: #FFFFFF; border-radius: 10px; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 10px; }

/* Section headings */
.sec { margin: 2.4rem 0 0.4rem 0; }
.sec h3 { margin: 0; font-size: 1.28rem; color: #1B5565; }
.sec .rule { height: 3px; width: 44px; background: #1F7A8C; margin-top: 0.4rem; border-radius: 2px; }

/* Status chips (risk indicators) */
.chip { display: flex; align-items: flex-start; gap: 0.6rem; padding: 0.7rem 0.9rem;
        border-radius: 10px; border: 1px solid; font-size: 0.97rem; line-height: 1.5;
        margin: 0.4rem 0 1rem 0; }
.chip .dot { flex: 0 0 12px; height: 12px; margin-top: 0.4rem; border-radius: 50%; }
.chip-ok    { background: #E6F3F5; border-color: #BCDCE2; color: #14505D; }
.chip-ok .dot { background: #1F7A8C; }
.chip-caution { background: #FDF1E3; border-color: #F0D2AC; color: #7A4510; }
.chip-caution .dot { background: #D9822B; }
.chip-alert { background: #FBE9E7; border-color: #F0BDB6; color: #7C241A; }
.chip-alert .dot { background: #C0392B; }

.badge { display: inline-block; font-size: 0.8rem; padding: 0.12rem 0.55rem; border-radius: 999px;
         background: #E6EEF2; color: #35505E; border: 1px solid #CFDDE4; margin-bottom: 0.3rem; }

footer { visibility: hidden; }

@media (max-width: 768px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 2.0rem; }
    .pg-head h1 { font-size: 1.5rem; }
    [data-testid="stMetric"] { padding: 12px 14px; }
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def style_fig(fig, title, x_title, y_title, height=420, legend=True):
    """Apply the shared scientific chart theme."""
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=title, x=0.0, xanchor="left",
            font=dict(size=16, color=NAVY, family=FONT_STACK),
        ),
        font=dict(family=FONT_STACK, size=13, color="#1F2D3A"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=12, r=12, t=64, b=12),
        showlegend=legend,
        legend=dict(
            orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0.0,
            font=dict(size=12),
        ),
        hoverlabel=dict(font=dict(family=FONT_STACK, size=13), bgcolor="#FFFFFF"),
        xaxis=dict(title=dict(text=x_title), gridcolor=GRID, zeroline=False,
                   linecolor="#B9CAD2", automargin=True),
        yaxis=dict(title=dict(text=y_title), gridcolor=GRID, zeroline=False,
                   linecolor="#B9CAD2", automargin=True),
    )
    return fig


def show_fig(fig):
    st.plotly_chart(fig, config={"displaylogo": False}, **_STRETCH)


# ============================================================
# 5. UI COMPONENTS
# ============================================================
def page_header(title, description):
    st.markdown(
        f'<div class="pg-head"><h1>{html.escape(title)}</h1>'
        f"<p>{html.escape(description)}</p></div>",
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(
        f'<div class="sec"><h3>{html.escape(title)}</h3><div class="rule"></div></div>',
        unsafe_allow_html=True,
    )


def status_chip(level, text):
    """Risk/status indicator. level: ok | caution | alert."""
    st.markdown(
        f'<div class="chip chip-{level}"><span class="dot"></span>'
        f"<span>{html.escape(text)}</span></div>",
        unsafe_allow_html=True,
    )


def scenario_badge():
    st.markdown(
        f'<span class="badge">{html.escape(t("badge.scenario"))}</span>',
        unsafe_allow_html=True,
    )


def assumptions_expander(temp, eggs, price, base_cost, cooling_cost):
    with st.expander(t("assump.title")):
        st.write(t("assump.temp", v=f"{temp:.1f}"))
        st.write(t("assump.eggs", v=f"{eggs:,.0f}"))
        st.write(t("assump.price", v=f"{price:,.2f}"))
        st.write(t("assump.opcost", v=f"{base_cost:,.2f}"))
        st.write(t("assump.cooling", v=f"{cooling_cost:,.2f}"))

        st.latex(
            r"N_{\mathrm{survivors}}"
            r"=N_0\times F\times H\times S_{72}"
        )
        st.latex(
            r"\mathrm{Net\ result}"
            r"=\mathrm{Revenue}-\mathrm{Total\ costs}"
        )


# ============================================================
# 6. PAGES
# ============================================================
def hatchery_inputs():
    """Read the sidebar hatchery assumptions from session state."""
    ss = st.session_state
    return ss["eggs"], ss["fry_price"], ss["base_cost"], ss["cooling_cost"]


def temperature_slider(key):
    return st.slider(
        t("in.temp"),
        min_value=T_MIN_DOMAIN,
        max_value=T_MAX_DOMAIN,
        step=0.5,
        key=key,
        help=t("in.temp.help"),
    )


# ------------------------------------------------------------
# 6.1 Overview
# ------------------------------------------------------------
def rate_curve_figure(selected_temp):
    """Interpolated biological rates with the source observations overlaid."""
    grid = np.linspace(T_MIN_DOMAIN, T_MAX_DOMAIN, 111)
    rates = np.array([biological_rates(x) for x in grid])

    series = [
        ("m.fert", REFERENCE["Fertilization rate"], rates[:, 0], COLOR_FERT),
        ("m.hatch", REFERENCE["Hatching rate"], rates[:, 1], COLOR_HATCH),
        ("m.surv72", REFERENCE["Survival rate to 72 h"], rates[:, 2], COLOR_SURVIVAL),
    ]

    fig = go.Figure()
    for key, observed, curve, color in series:
        name = t(key)
        fig.add_trace(go.Scatter(
            x=grid, y=curve, mode="lines",
            name=f"{name} {t('legend.interp_suffix')}",
            line=dict(color=color, width=2.5),
            hovertemplate=(
                f"{name}<br>%{{x:.1f}} °C: %{{y:.1%}}<extra></extra>"
            ),
        ))
        fig.add_trace(go.Scatter(
            x=REFERENCE["Temperature (°C)"], y=observed, mode="markers",
            name=f"{name} {t('legend.obs_suffix')}",
            marker=dict(color=color, size=11, symbol="diamond",
                        line=dict(color="#FFFFFF", width=1.5)),
            hovertemplate=(
                f"{name} {t('legend.obs_suffix')}<br>"
                f"%{{x}} °C: %{{y:.1%}}<extra></extra>"
            ),
        ))

    fig.add_vline(x=selected_temp, line_dash="dash", line_color=SLATE,
                  annotation_text=f"{selected_temp:.1f} °C",
                  annotation_position="top")
    style_fig(fig, t("ov.curve_title"), t("axis.temp"), t("axis.rate"), height=440)
    fig.update_yaxes(tickformat=".0%", range=[0, 0.8])
    return fig


def page_overview():
    page_header(t("nav.overview"), t("ov.desc"))
    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs()

    temp = temperature_slider("ov_temp")
    fert, hatch, survival = biological_rates(temp)

    survivors = eggs * fert * hatch * survival
    revenue = survivors * fry_price
    cost = base_cost + cooling_cost
    net_result = revenue - cost

    # Risk / status indicator relative to the two source observations
    st.markdown(f"**{t('ov.status_title')}**")
    if temp <= REFERENCE["Temperature (°C)"][0]:
        status_chip("ok", t("ov.status_low"))
    elif temp < REFERENCE["Temperature (°C)"][1]:
        status_chip("caution", t("ov.status_mid"))
    else:
        status_chip("alert", t("ov.status_high"))

    section(t("ov.bio"))
    a, b, c = st.columns(3)
    a.metric(t("m.fert"), f"{fert:.1%}", help=t("m.fert.help"))
    b.metric(t("m.hatch"), f"{hatch:.1%}", help=t("m.fert.help"))
    c.metric(t("m.surv72"), f"{survival:.1%}", help=t("m.fert.help"))

    section(t("ov.curve"))
    show_fig(rate_curve_figure(temp))
    st.caption(t("ov.curve_cap"))

    section(t("ov.econ"))
    d, e, f = st.columns(3)
    d.metric(t("m.survivors"), f"{survivors:,.0f}", help=t("m.survivors.help"))
    e.metric(t("m.revenue_ill"), f"฿{revenue:,.2f}")
    f.metric(t("m.cost"), f"฿{cost:,.2f}")

    st.metric(t("m.net"), f"฿{net_result:,.2f}", help=t("m.net.help"))

    assumptions_expander(temp, eggs, fry_price, base_cost, cooling_cost)
    st.warning(t("ov.warn"))


# ------------------------------------------------------------
# 6.2 Hatchery calculator
# ------------------------------------------------------------
def page_calculator():
    page_header(t("nav.calculator"), t("calc.desc"))
    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs()

    temp = temperature_slider("calc_temp")
    fert, hatch, survival = biological_rates(temp)

    # Biological calculations
    fertilized = eggs * fert
    hatched = fertilized * hatch
    survivors = hatched * survival

    # Economic calculations
    revenue = survivors * fry_price
    total_cost = base_cost + cooling_cost
    net_result = revenue - total_cost

    section(t("calc.s1"))
    a, b, c = st.columns(3)
    a.metric(t("m.fert"), f"{fert:.1%}", help=t("m.fert.help"))
    b.metric(t("m.hatch"), f"{hatch:.1%}", help=t("m.fert.help"))
    c.metric(t("m.surv72"), f"{survival:.1%}", help=t("m.fert.help"))

    section(t("calc.s2"))
    results = pd.DataFrame({
        "col.stage": [
            t("stage.eggs"), t("stage.fert"), t("stage.hatched"), t("stage.surv"),
        ],
        "col.count": [eggs, fertilized, hatched, survivors],
    })

    fig = go.Figure(go.Bar(
        x=results["col.stage"], y=results["col.count"],
        marker_color=[SLATE, TEAL, BLUE, NAVY],
        texttemplate="%{y:.3s}", textposition="outside", cliponaxis=False,
        hovertemplate=(
            f"%{{x}}<br>{t('col.count')}: %{{y:,.0f}}<extra></extra>"
        ),
    ))
    style_fig(fig, t("calc.chart_title"), t("axis.stage"), t("axis.count"),
              height=420, legend=False)
    show_fig(fig)
    st.caption(t("calc.chart_cap"))

    show_table(results, {"col.count": "{:,.0f}"})

    section(t("calc.s3"))
    x, y, z = st.columns(3)
    x.metric(t("m.revenue"), f"฿{revenue:,.2f}")
    y.metric(t("m.cost"), f"฿{total_cost:,.2f}")
    z.metric(t("m.net"), f"฿{net_result:,.2f}", help=t("m.net.help"))

    assumptions_expander(temp, eggs, fry_price, base_cost, cooling_cost)
    st.warning(t("calc.warn"))


# ------------------------------------------------------------
# 6.3 Climate simulation
# ------------------------------------------------------------
def page_climate():
    page_header(t("nav.climate"), t("clim.desc"))

    # Scenario controls
    section(t("clim.controls"))
    c1, c2 = st.columns(2)
    with c1:
        anomaly_sd = st.slider(
            t("in.anomaly_sd"),
            min_value=0.0, max_value=1.0, step=0.05,
            key="clim_sd", help=t("in.anomaly_sd.help"),
        )
    with c2:
        delta_g = st.slider(
            t("in.delta_g"),
            min_value=0.10, max_value=0.20, step=0.01,
            key="clim_dg", help=t("in.delta_g.help"),
        )

    seed = st.number_input(
        t("in.seed"),
        min_value=0, max_value=99999999, step=1,
        key="clim_seed", help=t("in.seed.help"),
    )

    # ---- Panel A: seasonal cycle for a representative year ----
    day = np.arange(1, 366)
    temp_day = seasonal_temperature(day, 0)

    survival_pct = SMAX * np.exp(
        -0.5 * ((temp_day - TOPT) / SIGMA) ** 2
    )

    seasonal_df = pd.DataFrame({
        "col.doy": day,
        "col.temp": temp_day,
        "col.surv_pct": survival_pct,
    })

    section(t("clim.a"))
    st.caption(t("clim.a_cap"))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("kpi.peak_temp"), f"{temp_day.max():.2f} °C")
    k2.metric(t("kpi.peak_day"), f"{int(day[int(np.argmax(temp_day))])}")
    k3.metric(
        t("kpi.days_above"), f"{int((temp_day > TCRIT0).sum())}",
        help=t("kpi.days_above.help"),
    )
    k4.metric(t("kpi.max_surv"), f"{survival_pct.max():.1f}%")
    st.caption(t("kpi.cap"))

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(
        x=day, y=temp_day, mode="lines", name=t("legend.mean"),
        line=dict(color=COLOR_TEMPERATURE, width=2.5),
        hovertemplate=(
            f"{t('hover.day')} %{{x}}<br>{t('hover.temp')}: "
            f"%{{y:.2f}} °C<extra></extra>"
        ),
    ))
    fig_temp.add_trace(go.Scatter(
        x=[day[0], day[-1]], y=[TCRIT0, TCRIT0], mode="lines",
        name=f"{t('legend.threshold_line')} ({TCRIT0} °C)",
        line=dict(color=COLOR_THRESHOLD_STATIC, width=1.8, dash="dash"),
        hovertemplate=f"{t('legend.threshold_line')}: {TCRIT0} °C<extra></extra>",
    ))
    style_fig(fig_temp, t("clim.seasonal_title"), t("axis.doy"), t("axis.temp"))
    show_fig(fig_temp)
    st.caption(t("clim.seasonal_cap"))

    fig_surv = go.Figure(go.Scatter(
        x=day, y=survival_pct, mode="lines", name=t("axis.surv_pct"),
        line=dict(color=COLOR_SURVIVAL, width=2.5),
        hovertemplate=(
            f"{t('hover.day')} %{{x}}<br>{t('hover.survival')}: "
            f"%{{y:.1f}} %<extra></extra>"
        ),
    ))
    style_fig(fig_surv, t("clim.survival_title"), t("axis.doy"),
              t("axis.surv_pct"), legend=False)
    fig_surv.update_yaxes(range=[0, 50])
    show_fig(fig_surv)
    st.caption(t("clim.survival_cap"))

    # ---- Panel B: multiyear climate scenario ----
    years = np.arange(2026, 2037)
    year_index = np.arange(len(years))
    n_days = len(years) * 365

    time_year = 2026 + np.arange(n_days) / 365.0
    yindex = np.minimum(np.arange(n_days) // 365, len(years) - 1)
    doy = (np.arange(n_days) % 365) + 1

    base_temp = seasonal_temperature(doy, yindex)

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

    tcrit_scenario = (
        TCRIT0
        + delta_g * yindex
    )

    climate_df = pd.DataFrame({
        "col.year": time_year,
        "col.mean_temp": mean_temp,
        "col.low_temp": lower_temp,
        "col.up_temp": upper_temp,
        "col.static": tcrit_static,
        "col.changing": tcrit_scenario,
    })

    section(t("clim.b"))
    st.caption(t("clim.b_cap"))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=time_year, y=mean_temp, mode="lines", name=t("legend.mean"),
        line=dict(color=COLOR_TEMPERATURE, width=1.6),
        customdata=np.column_stack([lower_temp, upper_temp]),
        hovertemplate=(
            f"{t('hover.year')} %{{x:.2f}}<br>{t('hover.temp')}: "
            f"%{{y:.2f}} °C<br>{t('hover.interval')}: "
            f"%{{customdata[0]:.2f}} to %{{customdata[1]:.2f}} °C<extra></extra>"
        ),
    ))
    fig.add_trace(go.Scatter(
        x=time_year, y=upper_temp, mode="lines",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=time_year, y=lower_temp, mode="lines",
        line=dict(width=0), fill="tonexty", fillcolor=BAND,
        name=t("legend.interval"), hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=time_year, y=tcrit_static, mode="lines", name=t("legend.static"),
        line=dict(color=COLOR_THRESHOLD_STATIC, width=2, dash="dash"),
        hovertemplate=(
            f"{t('legend.static')}: %{{y:.2f}} °C<extra></extra>"
        ),
    ))
    fig.add_trace(go.Scatter(
        x=time_year, y=tcrit_scenario, mode="lines", name=t("legend.changing"),
        line=dict(color=COLOR_THRESHOLD_CHANGING, width=2, dash="dot"),
        hovertemplate=(
            f"{t('legend.changing')}: %{{y:.2f}} °C<extra></extra>"
        ),
    ))
    style_fig(fig, t("clim.b_title"), t("axis.year_proj"), t("axis.temp"), height=460)
    show_fig(fig)

    # Annual summary of the seasonal model and Monte Carlo interval
    annual_df = pd.DataFrame({
        "col.year": years,
        "col.mean_annual": [
            TMEAN + ALPHA * i for i in year_index
        ],
        "col.amplitude": [
            AMP0 + BETA * i for i in year_index
        ],
        "col.anom_low": q025,
        "col.anom_high": q975,
        "col.static": TCRIT0,
        "col.changing": (
            TCRIT0 + delta_g * year_index
        ),
    })

    section(t("clim.annual"))
    show_table(annual_df, {
        "col.mean_annual": "{:.2f}",
        "col.amplitude": "{:.2f}",
        "col.anom_low": "{:.3f}",
        "col.anom_high": "{:.3f}",
        "col.static": "{:.2f}",
        "col.changing": "{:.2f}",
    })

    d1, d2, d3 = st.columns(3)
    d1.download_button(
        t("dl.annual"),
        data=csv_bytes(annual_df),
        file_name="catfish_climate_scenario_s1.csv",
        mime="text/csv",
        key="dl_annual",
    )
    d2.download_button(
        t("dl.seasonal"),
        data=csv_bytes(seasonal_df),
        file_name="catfish_seasonal_scenario_s1.csv",
        mime="text/csv",
        key="dl_seasonal",
    )
    d3.download_button(
        t("dl.multiyear"),
        data=csv_bytes(climate_df),
        file_name="catfish_multiyear_climate_s1.csv",
        mime="text/csv",
        key="dl_multiyear",
    )

    st.warning(t("clim.warn"))


# ------------------------------------------------------------
# 6.4 Sensitivity analysis
# ------------------------------------------------------------
def scenario_outcome(temp, eggs, price, total_cost):
    """Biological and illustrative economic outcome at one temperature."""
    f, h, s = biological_rates(temp)
    survivors = eggs * f * h * s
    revenue = survivors * price
    net = revenue - total_cost
    return f, h, s, survivors, revenue, net


def sensitivity_line(df, y_col, title, y_title, color, zero_line_label=None):
    fig = go.Figure(go.Scatter(
        x=df["col.dT"], y=df[y_col], mode="lines+markers",
        name=y_title, line=dict(color=color, width=2.5), marker=dict(size=6),
        customdata=df["col.scn_temp"],
        hovertemplate=(
            f"{t('axis.temp_change')}: %{{x:+.1f}}<br>"
            f"{t('col.scn_temp')}: %{{customdata:.1f}}<br>"
            f"{y_title}: %{{y:,.0f}}<extra></extra>"
        ),
    ))
    if zero_line_label:
        fig.add_hline(y=0, line_dash="dot", line_color=SLATE,
                      annotation_text=zero_line_label,
                      annotation_position="bottom right")
    style_fig(fig, title, t("axis.temp_change"), y_title, height=380, legend=False)
    return fig


def page_sensitivity():
    page_header(t("nav.sensitivity"), t("sens.desc"))

    section(t("sens.baseline_set"))
    s1, s2 = st.columns(2)

    with s1:
        base_temp = st.slider(
            t("in.base_temp"), T_MIN_DOMAIN, T_MAX_DOMAIN, step=0.5,
            key="sens_base_temp", help=t("in.temp.help"),
        )
        temp_range = st.slider(
            t("in.temp_range"), -3.0, 3.0, (-2.0, 2.0), 0.5,
            key="sens_temp_range", help=t("in.temp_range.help"),
        )
        base_eggs = st.number_input(
            t("in.eggs"), min_value=1, step=100_000,
            key="sens_eggs", help=t("in.eggs.help"),
        )

    with s2:
        price = st.number_input(
            t("in.price"), min_value=0.0, step=0.10,
            key="sens_price", help=t("in.price.help"),
        )
        operating = st.number_input(
            t("in.base_cost"), min_value=0.0, step=5_000.0,
            key="sens_cost", help=t("in.base_cost.help"),
        )
        cooling = st.number_input(
            t("in.cooling"), min_value=0.0, step=5_000.0,
            key="sens_cooling", help=t("in.cooling.help"),
        )

    include_cooling = st.checkbox(
        t("in.include_cooling"),
        help=t("in.include_cooling.help"),
        key="sens_include_cooling",
    )

    applied_cooling_cost = cooling if include_cooling else 0.0
    total_cost = operating + applied_cooling_cost

    (
        base_fert, base_hatch, base_survival,
        baseline_survivors, baseline_revenue, baseline_net,
    ) = scenario_outcome(base_temp, base_eggs, price, total_cost)

    section(t("sens.baseline_results"))
    m1, m2, m3 = st.columns(3)
    m1.metric(t("m.survivors"), f"{baseline_survivors:,.0f}", help=t("m.survivors.help"))
    m2.metric(t("m.revenue"), f"฿{baseline_revenue:,.0f}")
    m3.metric(t("m.net"), f"฿{baseline_net:,.0f}", help=t("m.net.help"))

    st.caption(t(
        "sens.baseline_cap",
        f=f"{base_fert:.1%}", h=f"{base_hatch:.1%}",
        s=f"{base_survival:.1%}", c=f"{total_cost:,.0f}",
    ))

    # Keep all scenario temperatures within the dashboard's 25–36°C range
    requested_min = base_temp + temp_range[0]
    requested_max = base_temp + temp_range[1]

    scenario_min = max(T_MIN_DOMAIN, requested_min)
    scenario_max = min(T_MAX_DOMAIN, requested_max)

    if scenario_min > scenario_max:
        # If the requested range is entirely outside the valid domain,
        # use the nearest boundary temperature as a single scenario.
        scenario_temps = np.array([
            float(np.clip(base_temp + np.mean(temp_range),
                          T_MIN_DOMAIN, T_MAX_DOMAIN))
        ])
    else:
        scenario_temps = np.linspace(scenario_min, scenario_max, 31)

    # Inform the user if the requested range was clipped
    if (
        scenario_min > requested_min
        or scenario_max < requested_max
    ):
        st.info(t("sens.clipped"))

    sens_rows = []
    for temp in scenario_temps:
        delta = temp - base_temp
        f, h, s, survivors, revenue, net = scenario_outcome(
            temp, base_eggs, price, total_cost
        )

        sens_rows.append({
            "col.dT": delta,
            "col.scn_temp": temp,
            "col.fert": f,
            "col.hatch": h,
            "col.surv72": s,
            "col.survivors": survivors,
            "col.revenue": revenue,
            "col.opcost": operating,
            "col.coolcost": applied_cooling_cost,
            "col.totcost": total_cost,
            "col.net": net,
            "col.dsurv": survivors - baseline_survivors,
            "col.dnet": net - baseline_net,
        })

    sens_df = pd.DataFrame(sens_rows)

    section(t("sens.effect"))

    fig1 = sensitivity_line(
        sens_df, "col.survivors", t("sens.chart1"), t("axis.survivors"), TEAL,
    )
    fig1.update_yaxes(rangemode="tozero")
    show_fig(fig1)

    show_fig(sensitivity_line(
        sens_df, "col.net", t("sens.chart2"), t("axis.net"), NAVY,
        zero_line_label=t("sens.breakeven"),
    ))

    show_fig(sensitivity_line(
        sens_df, "col.dsurv", t("sens.chart3"), t("axis.dsurv"), BLUE,
        zero_line_label=t("sens.baseline_line"),
    ))
    st.caption(t("sens.chart_cap"))

    section(t("sens.table"))
    show_table(sens_df, {
        "col.dT": "{:+.1f}",
        "col.scn_temp": "{:.1f}",
        "col.fert": "{:.1%}",
        "col.hatch": "{:.1%}",
        "col.surv72": "{:.1%}",
        "col.survivors": "{:,.0f}",
        "col.revenue": "฿{:,.0f}",
        "col.opcost": "฿{:,.0f}",
        "col.coolcost": "฿{:,.0f}",
        "col.totcost": "฿{:,.0f}",
        "col.net": "฿{:,.0f}",
        "col.dsurv": "{:+,.0f}",
        "col.dnet": "฿{:+,.0f}",
    })

    st.download_button(
        t("dl.sens"),
        data=csv_bytes(sens_df),
        file_name="catfish_sensitivity_analysis.csv",
        mime="text/csv",
        key="dl_sens",
    )

    st.info(t("sens.info"))


# ------------------------------------------------------------
# 6.5 AquaMonitor
# ------------------------------------------------------------
def _reset_aquamonitor():
    """Callback: clear every AquaMonitor input and hide the results."""
    for key in ("am_cr", "am_pb", "am_ni", "am_cd", "am_sediment"):
        st.session_state[key] = None
    st.session_state["am_weight"] = 50.0
    st.session_state["am_horizon"] = 5
    st.session_state["am_analyzed"] = False


def metal_input(label_key, key):
    return st.number_input(
        t(label_key),
        min_value=0.0, value=None, step=0.001, format="%.4f",
        key=key, help=t("in.metal.help"),
    )


def page_aquamonitor():
    page_header(t("nav.aquamonitor"), t("am.subtitle"))

    st.write(t("am.desc"))
    st.info(t("am.info"))

    # ---- Section 1: Fish muscle heavy metal concentrations ----
    section(t("am.s1"))
    st.caption(t("am.s1_cap"))

    with st.container(border=True):
        left_col, right_col = st.columns(2)
        with left_col:
            cr = metal_input("in.cr", "am_cr")
            ni = metal_input("in.ni", "am_ni")
        with right_col:
            pb = metal_input("in.pb", "am_pb")
            cd = metal_input("in.cd", "am_cd")

        st.markdown(f"**{t('am.exposure')}**")
        body_weight = st.number_input(
            t("in.bw"),
            min_value=1.0, step=1.0,
            key="am_weight", help=t("in.bw.help"),
        )
        st.caption(t("am.ir_cap", v=f"{FISH_CONSUMPTION_RATE:.4f}"))

    # ---- Section 2: Optional sediment scenario ----
    section(t("am.s2"))
    st.write(t("am.s2_desc"))

    with st.container(border=True):
        sediment_cr = st.number_input(
            t("in.sediment"),
            min_value=0.0, value=None, step=0.01, format="%.4f",
            key="am_sediment",
        )
        horizon = st.selectbox(
            t("in.horizon"),
            options=[1, 5, 10],
            format_func=lambda x: t("in.horizon.fmt", x=x),
            key="am_horizon",
        )

    b1, b2, _ = st.columns([1, 1, 3])
    if b1.button(t("btn.analyze"), type="primary", key="am_analyze"):
        st.session_state["am_analyzed"] = True
    b2.button(t("btn.reset"), key="am_reset", on_click=_reset_aquamonitor)

    if not st.session_state["am_analyzed"]:
        st.caption(t("am.prompt"))
        return

    # ---- Validate inputs ----
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
        st.error(t("am.err_nodata"))
        return

    if body_weight <= 0:
        st.error(t("am.err_bw"))
        return

    # ---- Calculate HQ and HI ----
    hq = {}

    for metal, concentration in measured.items():
        hq[metal] = (
            concentration
            * FISH_CONSUMPTION_RATE
            / body_weight
            / RFD[metal]
        )

    hi = sum(hq.values()) if hq else None

    # ---- Section 3: Screening summary ----
    section(t("am.s3"))

    c1, c2, c3 = st.columns(3)

    c1.metric(t("am.k_metals"), f"{len(measured)}")
    c2.metric(
        t("am.k_hi"),
        f"{hi:.4f}" if hi is not None else "N/A",
        help=t("am.k_hi.help"),
    )

    above_one = sum(value > 1 for value in hq.values())
    c3.metric(t("am.k_above"), f"{above_one}")

    if hi is not None and hi > 1:
        status_chip("alert", t("am.hi_high"))
    elif hi is not None:
        status_chip("ok", t("am.hi_low"))

    if not measured:
        st.info(t("am.no_fish"))

    # ---- Sections 4 and 5: concentration and HQ charts ----
    if measured:
        section(t("am.s4"))

        labels = [metal_label(m) for m in measured]
        fig_conc = go.Figure(go.Bar(
            x=labels,
            y=[float(v) for v in measured.values()],
            marker_color=TEAL,
            texttemplate="%{y:.4f}", textposition="outside", cliponaxis=False,
            hovertemplate=f"%{{x}}<br>{t('col.conc')}: %{{y:.4f}}<extra></extra>",
        ))
        style_fig(fig_conc, t("am.conc_title"), t("axis.metal"),
                  t("axis.conc"), height=380, legend=False)
        show_fig(fig_conc)
        st.caption(t("am.conc_cap"))

        section(t("am.s5"))

        hq_values = [float(hq[m]) for m in measured]
        fig_hq = go.Figure(go.Bar(
            x=labels,
            y=hq_values,
            marker_color=[RED if v > 1 else TEAL for v in hq_values],
            texttemplate="%{y:.4f}", textposition="outside", cliponaxis=False,
            hovertemplate="%{x}<br>HQ: %{y:.4f}<extra></extra>",
        ))
        fig_hq.add_hline(
            y=1, line_dash="dash", line_color=AMBER,
            annotation_text="HQ = 1", annotation_position="top left",
        )
        style_fig(fig_hq, t("am.hq_title"), t("axis.metal"), "HQ",
                  height=380, legend=False)
        show_fig(fig_hq)
        st.caption(t("am.hq_cap"))

        results_df = pd.DataFrame(
            [
                {
                    "col.metal": metal_label(metal),
                    "col.conc": float(measured[metal]),
                    "col.rfd": float(RFD[metal]),
                    "col.hq": float(hq[metal]),
                }
                for metal in measured
            ]
        )

        st.markdown(f"**{t('am.table')}**")
        show_table(results_df, {
            "col.conc": "{:.4f}",
            "col.rfd": "{:.4f}",
            "col.hq": "{:.4f}",
        })

    # ---- Section 6: Sediment scenario analysis ----
    sediment_scenarios_df = None

    if has_sediment:
        section(t("am.s6"))
        st.write(t("am.s6_desc"))

        scenarios = [
            (
                "A",
                t("scn.A"),
                float(sediment_cr),
                0.05,
            ),
            (
                "B",
                t("scn.B"),
                float(sediment_cr) * 0.85,
                0.07,
            ),
            (
                "C",
                t("scn.C"),
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
                        "scenario_id": scenario_id,
                        "col.scenario": scenario_name,
                        "col.year": year,
                        "col.sed_cr": concentration,
                    }
                )

        sediment_scenarios_df = pd.DataFrame(scenario_records)

        fig_sed = go.Figure()
        for scenario_id, scenario_name, _, _ in scenarios:
            sub = sediment_scenarios_df[
                sediment_scenarios_df["scenario_id"] == scenario_id
            ]
            fig_sed.add_trace(go.Scatter(
                x=sub["col.year"], y=sub["col.sed_cr"],
                mode="lines+markers", name=scenario_name,
                line=dict(color=COLOR_SCENARIO[scenario_id], width=2.5),
                marker=dict(size=6),
                hovertemplate=(
                    f"{scenario_name}<br>{t('axis.year')} %{{x}}: "
                    f"%{{y:.4f}} mg/kg<extra></extra>"
                ),
            ))
        style_fig(fig_sed, t("am.sed_title"), t("axis.year"), t("axis.sed"),
                  height=420)
        show_fig(fig_sed)
        st.caption(t("am.sed_cap"))

        final_year_df = sediment_scenarios_df[
            sediment_scenarios_df["col.year"] == int(horizon)
        ][["col.scenario", "col.year", "col.sed_cr"]].copy()

        st.markdown(f"**{t('am.sed_summary', h=horizon)}**")
        show_table(final_year_df, {"col.sed_cr": "{:.4f}"})

    # ---- Section 7: CSV export ----
    section(t("am.s7"))

    base_cols = {
        "col.bw": float(body_weight),
        "col.ir": float(FISH_CONSUMPTION_RATE),
    }
    export_rows = []

    for metal in measured:
        export_rows.append(
            {
                "col.record": t("rec.fish"),
                "col.metal": metal,
                "col.conc": float(measured[metal]),
                "col.rfd": float(RFD[metal]),
                "col.hq": float(hq[metal]),
                "col.hi": float(hi) if hi is not None else np.nan,
                **base_cols,
                "col.scenario": "",
                "col.year": np.nan,
                "col.sed_cr": np.nan,
            }
        )

    if has_sediment and sediment_scenarios_df is not None:
        for _, row in sediment_scenarios_df.iterrows():
            export_rows.append(
                {
                    "col.record": t("rec.sediment"),
                    "col.metal": "Cr",
                    "col.conc": np.nan,
                    "col.rfd": np.nan,
                    "col.hq": np.nan,
                    "col.hi": np.nan,
                    **base_cols,
                    "col.scenario": row["col.scenario"],
                    "col.year": int(row["col.year"]),
                    "col.sed_cr": float(row["col.sed_cr"]),
                }
            )

    if not export_rows:
        export_rows.append(
            {
                "col.record": t("rec.summary"),
                "col.metal": "",
                "col.conc": np.nan,
                "col.rfd": np.nan,
                "col.hq": np.nan,
                "col.hi": float(hi) if hi is not None else np.nan,
                **base_cols,
                "col.scenario": "",
                "col.year": np.nan,
                "col.sed_cr": np.nan,
            }
        )

    export_df = pd.DataFrame(export_rows)

    st.download_button(
        label=t("dl.am"),
        data=csv_bytes(export_df),
        file_name="AquaMonitor_results.csv",
        mime="text/csv",
        key="am_download",
    )

    # ---- Important limitations ----
    st.divider()
    st.subheader(t("am.limits"))
    st.warning(t("am.limits_text"))
    st.caption(t("am.footer"))


# ------------------------------------------------------------
# 6.6 Methods
# ------------------------------------------------------------
def page_methods():
    page_header(t("nav.methods"), t("me.desc"))

    section(t("me.1"))
    st.write(t("me.1_t"))

    reference_df = pd.DataFrame({
        "col.temp_ref": REFERENCE["Temperature (°C)"],
        "col.fert": REFERENCE["Fertilization rate"],
        "col.hatch": REFERENCE["Hatching rate"],
        "m.surv72": REFERENCE["Survival rate to 72 h"],
    })
    show_table(reference_df, {
        "col.fert": "{:.1%}",
        "col.hatch": "{:.1%}",
        "m.surv72": "{:.1%}",
    })
    st.caption(t("me.1_cap"))

    section(t("me.2"))
    st.latex(
        r"N_{\mathrm{survivors}} = N_0 "
        r"\times F \times H \times S_{72}"
    )
    st.write(t("me.2_t"))

    section(t("me.3"))
    st.write(t("me.3_t"))

    section(t("me.4"))
    st.latex(
        r"T(d,y)=T_{\mathrm{mean}}+\alpha y+"
        r"(A_0+\beta y)\cos\left(\frac{2\pi(d-D_{\mathrm{peak}})}{365}\right)"
    )
    st.write(t("me.4_t"))

    section(t("me.5"))
    st.latex(
        r"S(T)=S_{\max}\exp\left[-\frac{1}{2}"
        r"\left(\frac{T-T_{\mathrm{opt}}}{\sigma}\right)^2\right]"
    )
    st.write(t("me.5_t"))

    section(t("me.6"))
    st.write(t("me.6_t"))

    section(t("me.7"))
    st.latex(
        r"T_{\mathrm{crit}}(y)=T_{\mathrm{crit},0}"
        r"+\Delta_g(y-2026)"
    )
    st.write(t("me.7_t"))

    section(t("me.8"))
    st.write(t("me.8_t"))

    section(t("me.9"))
    st.warning(t("me.9_t"))

    section(t("me.10"))
    st.write(t("me.10_t"))

    section(t("me.11"))
    st.latex(
        r"\mathrm{HQ}=\frac{C\times IR}{BW\times \mathrm{RfD}},\qquad "
        r"\mathrm{HI}=\sum \mathrm{HQ}"
    )
    st.write(t("me.11_t1", ir=f"{FISH_CONSUMPTION_RATE:.4f}"))

    rfd_df = pd.DataFrame({
        "col.metal": [metal_label(m) for m in METAL_ORDER],
        "col.rfd": [RFD[m] for m in METAL_ORDER],
    })
    st.markdown(f"**{t('me.11_rfd')}**")
    show_table(rfd_df, {"col.rfd": "{:.4f}"})

    st.latex(
        r"C(t)=C_0e^{-kt}+\frac{I}{k}\left(1-e^{-kt}\right)"
    )
    st.write(t("me.11_t2"))


# ============================================================
# 7. SIDEBAR AND MAIN ENTRY POINT
# ============================================================
PAGES = {
    "overview": page_overview,
    "calculator": page_calculator,
    "climate": page_climate,
    "sensitivity": page_sensitivity,
    "aquamonitor": page_aquamonitor,
    "methods": page_methods,
}

HATCHERY_PAGES = ("overview", "calculator")


def render_sidebar():
    with st.sidebar:
        st.markdown(
            f'<div class="brand"><div class="name">{html.escape(t("app.name"))}</div>'
            f'<div class="tag">{html.escape(t("app.tagline"))}</div></div>',
            unsafe_allow_html=True,
        )

        st.selectbox(t("lang.label"), LANG_OPTIONS, key="language")

        st.markdown(f"**{t('nav.title')}**")
        st.radio(
            t("nav.label"),
            PAGE_IDS,
            format_func=lambda page_id: t(f"nav.{page_id}"),
            key="page",
            label_visibility="collapsed",
        )

        if st.session_state["page"] in HATCHERY_PAGES:
            st.divider()
            st.markdown(f"**{t('side.assump')}**")
            st.markdown(
                f'<div class="side-note">{html.escape(t("side.assump_note"))}</div>',
                unsafe_allow_html=True,
            )
            st.number_input(
                t("in.eggs"), min_value=1, step=100_000,
                key="eggs", help=t("in.eggs.help"),
            )
            st.number_input(
                t("in.price"), min_value=0.0, step=0.10,
                key="fry_price", help=t("in.price.help"),
            )
            st.number_input(
                t("in.base_cost"), min_value=0.0, step=5_000.0,
                key="base_cost", help=t("in.base_cost.help"),
            )
            st.number_input(
                t("in.cooling"), min_value=0.0, step=5_000.0,
                key="cooling_cost", help=t("in.cooling.help"),
            )

        st.divider()
        st.caption(t("app.disclaimer"))


def main():
    init_state()

    st.set_page_config(
        page_title=t("app.page_title"),
        page_icon="🐟",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Widgets are re-seeded from session state on every run; silence the
    # (harmless) "default value + session state" notice for the range slider.
    try:
        st._config.set_option("global.disableWidgetStateDuplicationWarning", True)
    except Exception:
        pass

    inject_css()
    render_sidebar()

    page_id = st.session_state.get("page", "overview")
    PAGES.get(page_id, page_overview)()


main()

"""
Catfish Thermal Risk Dashboard
==============================
Single-file Streamlit application (English / Thai).

File layout:
    0. Imports
    1. Scientific parameters and models
    2. Translation dictionary (single source of interface text)
    3. Language, state and formatting helpers
    4. Styling (CSS, Plotly theme)
    5. UI components
    6. Pages: overview, calculator, climate, sensitivity, aquamonitor, methods
    7. Sidebar and main entry point
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

# --- 1.1 Source-study observations ---
REFERENCE = {
    "Temperature (°C)": [29, 32],
    "Fertilization rate": [0.677, 0.590],
    "Hatching rate": [0.434, 0.266],
    "Survival rate to 72 h": [0.449, 0.0],
}

# --- 1.2 Supplementary File S1 parameters ---
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

# Temperature domain
T_MIN_DOMAIN = 25.0
T_MAX_DOMAIN = 36.0

# --- 1.3 AquaMonitor parameters ---
RFD = {
    "Cr": 0.003,
    "Pb": 0.0035,
    "Ni": 0.020,
    "Cd": 0.001,
}
METAL_ORDER = ["Cr", "Pb", "Ni", "Cd"]
FISH_CONSUMPTION_RATE = 0.0215  # kg/day


def seasonal_temperature(day, year_index):
    """Seasonal temperature scenario."""
    return (
        TMEAN
        + ALPHA * year_index
        + (AMP0 + BETA * year_index)
        * np.cos(2 * np.pi * (day - DPEAK) / 365.0)
    )


def biological_rates(temp):
    """Linear interpolation between observed rates."""
    fert = np.interp(
        temp, REFERENCE["Temperature (°C)"], REFERENCE["Fertilization rate"]
    )
    hatch = np.interp(
        temp, REFERENCE["Temperature (°C)"], REFERENCE["Hatching rate"]
    )
    survival = np.interp(
        temp, REFERENCE["Temperature (°C)"], REFERENCE["Survival rate to 72 h"]
    )
    return float(fert), float(hatch), float(survival)


def sediment_model(initial, years, input_rate, decay):
    """Illustrative sediment concentration scenario."""
    result = []
    for year in range(years + 1):
        if decay == 0:
            value = initial + input_rate * year
        else:
            value = (
                initial * np.exp(-decay * year)
                + input_rate / decay * (1 - np.exp(-decay * year))
            )
        result.append(max(0.0, float(value)))
    return result


# ============================================================
# 2. TRANSLATION DICTIONARY
# ============================================================
TEXT = {
    # App Shell & Navigation
    "app.page_title": ("Catfish Thermal Risk Dashboard", "แดชบอร์ดความเสี่ยงด้านอุณหภูมิต่อการเพาะเลี้ยงปลาดุก"),
    "app.name": ("Catfish Thermal Risk Dashboard", "แดชบอร์ดความเสี่ยงด้านอุณหภูมิต่อการเพาะเลี้ยงปลาดุก"),
    "app.tagline": (
        "Interactive decision-support tool under Data Repository section.",
        "เครื่องมือสนับสนุนการตัดสินใจเชิงโต้ตอบภายใต้หัวข้อคลังข้อมูล",
    ),
    "app.disclaimer": (
        "Exploratory research prototype. Outputs are scenario estimates.",
        "ต้นแบบเพื่อการวิจัยเชิงสำรวจ ผลลัพธ์เป็นค่าประมาณตามสถานการณ์",
    ),
    "lang.label": ("Language / ภาษา", "ภาษา / Language"),
    "nav.title": ("Data Repository Options", "เมนูคลังข้อมูล"),
    "nav.label": ("Select Module", "เลือกมอดูล"),
    "nav.overview": ("Overview", "ภาพรวม"),
    "nav.calculator": ("Hatchery Calculator", "เครื่องคำนวณการเพาะฟัก"),
    "nav.climate": ("Climate Simulation", "แบบจำลองสภาพภูมิอากาศ"),
    "nav.sensitivity": ("Sensitivity Analysis", "การวิเคราะห์ความไว"),
    "nav.aquamonitor": ("AquaMonitor", "AquaMonitor (ความเสี่ยงโลหะหนัก)"),
    "nav.methods": ("Methods & Documentation", "ระเบียบวิธีและเอกสารอ้างอิง"),
    "side.assump": ("Hatchery assumptions", "สมมติฐานการเพาะฟัก"),
    "side.assump_note": ("Used across estimation tools.", "ใช้สำหรับการคำนวณในหน้าต่าง ๆ"),

    # Shared Inputs & Metrics
    "in.eggs": ("Initial eggs", "จำนวนไข่เริ่มต้น"),
    "in.eggs.help": ("Number of eggs at start of cycle.", "จำนวนไข่เมื่อเริ่มรอบการเพาะฟัก"),
    "in.price": ("Price per fry (THB)", "ราคาต่อลูกปลา (บาท)"),
    "in.price.help": ("Assumed selling price per fry.", "ราคาขายสมมติของลูกปลาหนึ่งตัว"),
    "in.base_cost": ("Base operating cost (THB)", "ต้นทุนดำเนินงานพื้นฐาน (บาท)"),
    "in.base_cost.help": ("Fixed operating expenses.", "ต้นทุนดำเนินงานคงที่"),
    "in.cooling": ("Cooling cost (THB)", "ต้นทุนระบบทำความเย็น (บาท)"),
    "in.cooling.help": ("Fixed cost for water cooling.", "ต้นทุนระบบทำความเย็นคงที่"),
    "in.temp": ("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
    "in.temp.help": ("Select temperature between 25 and 36 °C.", "เลือกอุณหภูมิน้ำระหว่าง 25 ถึง 36 °C"),

    "m.fert": ("Fertilization rate", "อัตราการปฏิสนธิ"),
    "m.hatch": ("Hatching rate", "อัตราการฟัก"),
    "m.surv72": ("Survival to 72 h", "อัตรารอดถึง 72 ชั่วโมง"),
    "m.survivors": ("Estimated survivors", "จำนวนลูกปลารอดโดยประมาณ"),
    "m.revenue": ("Estimated revenue", "รายได้โดยประมาณ"),
    "m.revenue_ill": ("Illustrative revenue", "รายได้เชิงตัวอย่าง"),
    "m.cost": ("Total costs", "ต้นทุนรวมที่ระบุ"),
    "m.net": ("Net result", "ผลลัพธ์สุทธิเชิงตัวอย่าง"),
    "m.net.help": ("Revenue minus specified costs.", "รายได้หักด้วยต้นทุนดำเนินงานและต้นทุนระบบทำความเย็น"),
    "m.fert.help": ("Interpolated between observations.", "ประมาณค่าระหว่างค่าสังเกตจากงานต้นทาง"),
    "m.survivors.help": ("Eggs × fert × hatch × survival.", "ไข่เริ่มต้น × อัตราปฏิสนธิ × อัตราการฟัก × อัตรารอด"),
    "badge.scenario": ("Scenario estimate", "ค่าประมาณตามสถานการณ์"),
    "badge.observed": ("Source observation", "ค่าสังเกตจากงานต้นทาง"),

    # Overview
    "ov.desc": ("Water temperature effects on hatchery output.", "ผลของอุณหภูมิน้ำต่อผลผลิตการเพาะฟัก"),
    "ov.status_title": ("Temperature status", "สถานะตำแหน่งอุณหภูมิ"),
    "ov.status_low": ("<= 29 °C: Rates held at 29 °C baseline.", "ที่หรือต่ำกว่า 29 °C: อัตราคงที่เท่ากับค่าที่ 29 °C"),
    "ov.status_mid": ("29 - 32 °C: Linearly interpolated.", "ระหว่าง 29 ถึง 32 °C: อัตราได้จากการประมาณค่าเชิงเส้น"),
    "ov.status_high": (">= 32 °C: Rates held at 32 °C baseline (0% survival at 72h).", "ที่หรือสูงกว่า 32 °C: อัตรารอด 72 ชั่วโมงเท่ากับ 0%"),
    "ov.bio": ("Biological estimates", "ค่าประมาณทางชีววิทยา"),
    "ov.econ": ("Hatchery economics", "สถานการณ์เศรษฐศาสตร์"),
    "ov.curve": ("Survival analysis", "การวิเคราะห์อัตรารอดตามอุณหภูมิ"),
    "ov.curve_title": ("Biological rates vs temperature", "อัตราทางชีววิทยาเทียบกับอุณหภูมิน้ำ"),
    "ov.curve_cap": ("Diamonds represent observed points (29°C & 32°C). Lines show linear interpolation.", "จุดสี่เหลี่ยมแทนค่าสังเกตจริง เส้นแสดงการประมาณค่าเชิงเส้น"),
    "ov.warn": ("Model approximation note: Biological rates are interpolated between 29°C and 32°C.", "ข้อสังเกต: อัตราทางชีววิทยาอ้างอิงจากการประมาณค่าระหว่าง 29°C และ 32°C"),
    "axis.temp": ("Water temperature (°C)", "อุณหภูมิน้ำ (°C)"),
    "axis.rate": ("Rate (proportion)", "อัตรา (สัดส่วน)"),
    "legend.selected": ("Selected temperature", "อุณหภูมิที่เลือก"),
    "legend.obs_suffix": ("(observed)", "(ค่าสังเกต)"),
    "legend.interp_suffix": ("(model)", "(แบบจำลอง)"),

    # Assumptions Expander
    "assump.title": ("Calculation assumptions", "ดูสมมติฐานการคำนวณ"),
    "assump.temp": ("Water temperature: {v} °C", "อุณหภูมิน้ำ: {v} °C"),
    "assump.eggs": ("Initial egg count: {v}", "จำนวนไข่เริ่มต้น: {v}"),
    "assump.price": ("Price per fry: ฿{v}", "ราคาต่อลูกปลา: ฿{v}"),
    "assump.opcost": ("Operating cost: ฿{v}", "ต้นทุนดำเนินงาน: ฿{v}"),
    "assump.cooling": ("Cooling cost: ฿{v}", "ต้นทุนระบบทำความเย็น: ฿{v}"),

    # Calculator
    "calc.desc": ("Estimate production output under selected scenarios.", "ประมาณผลผลิตและเศรษฐศาสตร์เชิงตัวอย่าง"),
    "calc.s1": ("1. Biological rates", "1. ค่าประมาณทางชีววิทยา"),
    "calc.s2": ("2. Production breakdown", "2. ผลผลิตโดยประมาณตามขั้นตอน"),
    "calc.s3": ("3. Economic outcome", "3. ผลทางเศรษฐศาสตร์"),
    "stage.eggs": ("Initial eggs", "ไข่เริ่มต้น"),
    "stage.fert": ("Fertilized eggs", "ไข่ที่ปฏิสนธิ"),
    "stage.hatched": ("Hatched larvae", "ลูกปลาที่ฟักออก"),
    "stage.surv": ("Survivors at 72 h", "ลูกปลารอดที่ 72 ชั่วโมง"),
    "col.stage": ("Production stage", "ขั้นตอนการผลิต"),
    "col.count": ("Estimated count", "จำนวนโดยประมาณ"),
    "calc.chart_title": ("Production pipeline count", "ผลผลิตโดยประมาณในแต่ละขั้นตอน"),
    "calc.chart_cap": ("Computed counts based on model assumptions.", "จำนวนคำนวณจากอัตราของแบบจำลอง"),
    "axis.stage": ("Stage", "ขั้นตอน"),
    "axis.count": ("Count (n)", "จำนวน (ตัว)"),
    "calc.warn": ("Illustrative values based on simplified calculations.", "ค่าประมาณเชิงตัวอย่างเพื่อการวางแผนเบื้องต้น"),

    # Climate
    "clim.desc": ("Seasonal and multiyear temperature projections.", "สถานการณ์อุณหภูมิตามฤดูกาลและหลายปี"),
    "clim.controls": ("Climate parameters", "ตัวควบคุมสถานการณ์"),
    "in.anomaly_sd": ("Annual anomaly SD (°C)", "ส่วนเบี่ยงเบนมาตรฐานความผิดปกติรายปี (°C)"),
    "in.anomaly_sd.help": ("Standard deviation for Monte Carlo draws.", "ส่วนเบี่ยงเบนมาตรฐานสำหรับการสุ่ม"),
    "in.delta_g": ("Threshold change Δg (°C/year)", "การเปลี่ยนแปลงค่าเกณฑ์ Δg (°C/ปี)"),
    "in.delta_g.help": ("Sensitivity adaptation parameter.", "สมมติฐานการเปลี่ยนแปลงเกณฑ์ความทนทาน"),
    "in.seed": ("Random seed", "ค่าเริ่มต้นการสุ่ม (Random Seed)"),
    "in.seed.help": ("Seed for reproducible runs.", "กำหนดค่าเพื่อทำซ้ำการสุ่ม"),
    "clim.a": ("A. Seasonal vulnerability cycle", "A. วัฏจักรความเปราะบางตามฤดูกาลในรอบปี"),
    "clim.a_cap": ("Gaussian response curve based on S1 parameters.", "เส้นโค้งการตอบสนองแบบเกาส์เซียนตาม S1"),
    "kpi.peak_temp": ("Peak temperature", "อุณหภูมิสูงสุด"),
    "kpi.peak_day": ("Day of peak", "วันที่อุณหภูมิสูงสุด"),
    "kpi.days_above": ("Days above threshold", "จำนวนวันที่เกินค่าเกณฑ์"),
    "kpi.days_above.help": ("Days exceeding static threshold (30.75 °C).", "จำนวนวันที่อุณหภูมิสูงกว่า 30.75 °C"),
    "kpi.max_surv": ("Peak 72-h survival", "อัตรารอดสูงสุดที่ 72 ชั่วโมง"),
    "kpi.cap": ("Values read from 2026 baseline cycle.", "อ่านค่าจากเส้นสถานการณ์ฐานปี 2026"),
    "clim.seasonal_title": ("Seasonal temperature cycle", "สถานการณ์อุณหภูมิน้ำตามฤดูกาล"),
    "clim.survival_title": ("72-h Larval survival curve", "อัตรารอด 72 ชั่วโมงตามฤดูกาล"),
    "clim.seasonal_cap": ("Baseline year 2026 profile.", "โปรไฟล์ปีฐาน 2026"),
    "clim.survival_cap": ("Gaussian response equation plot.", "กราฟสมการตอบสนองแบบเกาส์เซียน"),
    "axis.doy": ("Day of year", "วันที่ในรอบปี"),
    "axis.surv_pct": ("72-h Survival (%)", "อัตรารอด 72 h (%)"),
    "legend.threshold_line": ("Static threshold", "ค่าเกณฑ์คงที่"),
    "clim.b": ("B. Multiyear stochastic scenario", "B. สถานการณ์ภูมิอากาศเชิงสุ่มหลายปี"),
    "clim.b_cap": ("10,000 Monte Carlo simulation runs with 95% interval.", "การจำลองมอนติคาร์โล 10,000 ครั้ง พร้อมช่วงความเชื่อมั่น 95%"),
    "clim.b_title": ("Temperature trend & 95% interval (2026–2036)", "แนวโน้มอุณหภูมิและช่วงจำลอง 95% (2026–2036)"),
    "axis.year_proj": ("Year", "ปี"),
    "legend.mean": ("Baseline temperature", "อุณหภูมิฐาน"),
    "legend.interval": ("95% simulation interval", "ช่วงการจำลอง 95%"),
    "legend.static": ("Static threshold", "ค่าเกณฑ์คงที่"),
    "legend.changing": ("Changing threshold", "ค่าเกณฑ์เปลี่ยนแปลง"),
    "hover.interval": ("95% simulation interval", "ช่วงการจำลอง 95%"),
    "hover.temp": ("Temperature", "อุณหภูมิ"),
    "hover.day": ("Day", "วันที่"),
    "hover.year": ("Year", "ปี"),
    "hover.survival": ("Survival", "อัตรารอด"),
    "clim.annual": ("Annual summary", "ตารางสรุปข้อมูลรายปี"),
    "col.year": ("Year", "ปี"),
    "col.mean_annual": ("Mean temp (°C)", "อุณหภูมิเฉลี่ย (°C)"),
    "col.amplitude": ("Amplitude (°C)", "แอมพลิจูด (°C)"),
    "col.anom_low": ("Lower 95% anomaly", "ขอบล่าง 95%"),
    "col.anom_high": ("Upper 95% anomaly", "ขอบบน 95%"),
    "col.static": ("Static threshold (°C)", "เกณฑ์คงที่ (°C)"),
    "col.changing": ("Changing threshold (°C)", "เกณฑ์เปลี่ยนแปลง (°C)"),
    "col.doy": ("Day of year", "วันที่ในรอบปี"),
    "col.temp": ("Temperature (°C)", "อุณหภูมิน้ำ (°C)"),
    "col.surv_pct": ("72-h survival (%)", "อัตรารอด 72 h (%)"),
    "col.mean_temp": ("Mean temp (°C)", "อุณหภูมิเฉลี่ย (°C)"),
    "col.low_temp": ("Lower 95% temp (°C)", "ขอบล่าง 95% (°C)"),
    "col.up_temp": ("Upper 95% temp (°C)", "ขอบบน 95% (°C)"),
    "dl.annual": ("Download annual data (CSV)", "ดาวน์โหลดข้อมูลรายปี (CSV)"),
    "dl.seasonal": ("Download seasonal data (CSV)", "ดาวน์โหลดข้อมูลตามฤดูกาล (CSV)"),
    "dl.multiyear": ("Download multiyear data (CSV)", "ดาวน์โหลดข้อมูลหลายปี (CSV)"),
    "clim.warn": ("Simulation scenario only. Not a calibrated weather forecast.", "การจำลองตามสถานการณ์สมมติ ไม่ใช่การพยากรณ์อากาศจริง"),

    # Sensitivity
    "sens.desc": ("Evaluate outcome changes against baseline temperature shifts.", "วิเคราะห์ผลกระทบจากการเปลี่ยนแปลงอุณหภูมิ"),
    "sens.baseline_set": ("Set baseline", "กำหนดอุณหภูมิและสมมติฐานฐาน"),
    "in.base_temp": ("Baseline temperature (°C)", "อุณหภูมิฐาน (°C)"),
    "in.temp_range": ("Range offset (°C)", "ช่วงการเปลี่ยนแปลงอุณหภูมิ (°C)"),
    "in.temp_range.help": ("Offsets relative to baseline.", "ค่าส่วนต่างจากอุณหภูมิฐาน"),
    "in.include_cooling": ("Deduct cooling cost in scenarios", "หักต้นทุนระบบทำความเย็นในทุกสถานการณ์"),
    "in.include_cooling.help": ("Include cooling expense across sensitivity runs.", "รวมค่าทำความเย็นในการวิเคราะห์"),
    "sens.baseline_results": ("Baseline summary", "สรุปผลลัพธ์ที่อุณหภูมิฐาน"),
    "sens.baseline_cap": ("Fert: {f}, Hatch: {h}, Surv72: {s}. Costs: ฿{c}", "อัตราการปฏิสนธิ: {f}, การฟัก: {h}, อัตรารอด: {s}. ต้นทุน: ฿{c}"),
    "sens.clipped": ("Scenarios clipped to the valid 25–36 °C domain.", "ปรับช่วงอุณหภูมิให้อยู่ในช่วง 25–36 °C"),
    "sens.effect": ("Sensitivity curves", "กราฟวิเคราะห์ความไว"),
    "sens.chart1": ("Survivors across temperature shifts", "จำนวนลูกปลารอดตามการเปลี่ยนแปลงอุณหภูมิ"),
    "sens.chart2": ("Net financial result", "ผลลัพธ์สุทธิทางการเงิน"),
    "sens.chart3": ("Change in survivors relative to baseline", "การเปลี่ยนแปลงของจำนวนลูกปลารอดเทียบกับอุณหภูมิฐาน"),
    "sens.chart_cap": ("Calculated outputs across specified temperature steps.", "ผลลัพธ์ตามช่วงอุณหภูมิที่วิเคราะห์"),
    "sens.breakeven": ("Breakeven (Net = 0)", "จุดคุ้มทุน (สุทธิ = 0)"),
    "sens.baseline_line": ("Zero change", "ไม่มีการเปลี่ยนแปลง"),
    "axis.temp_change": ("Temperature change (°C)", "การเปลี่ยนแปลงอุณหภูมิ (°C)"),
    "axis.survivors": ("Survivors (n)", "จำนวนลูกปลารอด (ตัว)"),
    "axis.net": ("Net result (THB)", "ผลลัพธ์สุทธิ (บาท)"),
    "axis.dsurv": ("Δ Survivors (n)", "การเปลี่ยนแปลงลูกปลารอด (ตัว)"),
    "sens.table": ("Sensitivity data table", "ตารางผลการวิเคราะห์ความไว"),
    "col.dT": ("Δ Temp (°C)", "การเปลี่ยนแปลงอุณหภูมิ (°C)"),
    "col.scn_temp": ("Scenario temp (°C)", "อุณหภูมิตามสถานการณ์ (°C)"),
    "col.fert": ("Fertilization", "อัตราปฏิสนธิ"),
    "col.hatch": ("Hatching", "อัตราการฟัก"),
    "col.surv72": ("Survival 72h", "อัตรารอด 72h"),
    "col.survivors": ("Survivors", "จำนวนลูกปลารอด"),
    "col.revenue": ("Revenue (THB)", "รายได้ (บาท)"),
    "col.opcost": ("Op Cost (THB)", "ต้นทุนดำเนินงาน (บาท)"),
    "col.coolcost": ("Cooling Cost (THB)", "ต้นทุนทำความเย็น (บาท)"),
    "col.totcost": ("Total Cost (THB)", "ต้นทุนรวม (บาท)"),
    "col.net": ("Net Result (THB)", "ผลสุทธิ (บาท)"),
    "col.dsurv": ("Δ Survivors", "ส่วนต่างลูกปลารอด"),
    "col.dnet": ("Δ Net (THB)", "ส่วนต่างผลสุทธิ (บาท)"),
    "dl.sens": ("Download sensitivity CSV", "ดาวน์โหลดผลการวิเคราะห์ความไว (CSV)"),
    "sens.info": ("Static comparison model assuming fixed operational parameters.", "การเปรียบเทียบภายใต้สมมติฐานพารามิเตอร์คงที่"),

    # AquaMonitor
    "am.subtitle": ("Heavy Metal Screening & Risk Index", "การประเมินคัดกรองความเสี่ยงจากโลหะหนัก"),
    "am.desc": ("Screening tool for heavy metal Hazard Quotients (HQ) and Hazard Index (HI).", "เครื่องมือคัดกรองดัชนีความเป็นอันตรายจากโลหะหนักในปลา"),
    "am.info": ("Screening-level risk assessment prototype. Verify with accredited lab analyses.", "เครื่องมือระดับการคัดกรอง ควรตรวจสอบด้วยผลจากห้องปฏิบัติการมาตรฐาน"),
    "am.s1": ("1. Heavy Metal Concentration in Fish Muscle", "1. ความเข้มข้นโลหะหนักในกล้ามเนื้อปลา"),
    "am.s1_cap": ("Unit: mg/kg wet weight.", "หน่วย: มิลลิกรัม/กิโลกรัม น้ำหนักเปียก"),
    "metal.Cr": ("Total Chromium (Cr)", "โครเมียมรวม (Cr)"),
    "metal.Pb": ("Lead (Pb)", "ตะกั่ว (Pb)"),
    "metal.Ni": ("Nickel (Ni)", "นิกเกิล (Ni)"),
    "metal.Cd": ("Cadmium (Cd)", "แคดเมียม (Cd)"),
    "in.cr": ("Chromium, Cr (mg/kg)", "โครเมียม Cr (mg/kg)"),
    "in.pb": ("Lead, Pb (mg/kg)", "ตะกั่ว Pb (mg/kg)"),
    "in.ni": ("Nickel, Ni (mg/kg)", "นิกเกิล Ni (mg/kg)"),
    "in.cd": ("Cadmium, Cd (mg/kg)", "แคดเมียม Cd (mg/kg)"),
    "in.metal.help": ("Enter measured concentration.", "กรอกค่าความเข้มข้นที่ตรวจวัดได้"),
    "am.exposure": ("Exposure parameters", "พารามิเตอร์การรับสัมผัส"),
    "in.bw": ("Body weight (kg)", "น้ำหนักตัวผู้บริโภค (kg)"),
    "in.bw.help": ("Consumer weight for HQ calculation.", "น้ำหนักตัวสำหรับคำนวณ HQ"),
    "am.ir_cap": ("Assumed consumption: {v} kg/day.", "ปริมาณการบริโภคปลาที่สมมติ: {v} kg/วัน"),
    "am.s2": ("2. Sediment Chromium Scenario (Optional)", "2. สถานการณ์โครเมียมในตะกอน (ไม่บังคับ)"),
    "am.s2_desc": ("Model hypothetical sediment chromium accumulation over time.", "จำลองการสะสมของโครเมียมในตะกอนตามช่วงเวลา"),
    "in.sediment": ("Initial sediment Cr (mg/kg)", "ความเข้มข้นโครเมียมเริ่มต้นในตะกอน (mg/kg)"),
    "in.horizon": ("Simulation period (years)", "ระยะเวลาจำลอง (ปี)"),
    "in.horizon.fmt": ("{x} years", "{x} ปี"),
    "btn.analyze": ("Analyze Risk", "คำนวณและประเมินผล"),
    "btn.reset": ("Clear Inputs", "ล้างข้อมูล"),
    "am.prompt": ("Enter measurements and click 'Analyze Risk'.", "กรอกข้อมูลแล้วกดปุ่มคำนวณและประเมินผล"),
    "am.err_nodata": ("Please enter at least one measurement.", "โปรดกรอกข้อมูลอย่างน้อย 1 รายการ"),
    "am.err_bw": ("Body weight must be greater than zero.", "น้ำหนักตัวต้องมากกว่า 0"),
    "am.s3": ("3. Risk Screening Results", "3. สรุปผลการคัดกรองความเสี่ยง"),
    "am.k_metals": ("Metals measured", "จำนวนโลหะที่ตรวจวัด"),
    "am.k_hi": ("Hazard Index (HI)", "ดัชนีความเป็นอันตรายรวม (HI)"),
    "am.k_hi.help": ("Sum of Hazard Quotients.", "ผลรวมของค่า HQ ของทุกโลหะ"),
    "am.k_above": ("HQ > 1 Count", "จำนวนโลหะที่มี HQ > 1"),
    "am.hi_high": ("ALERT: HI exceeds 1. Potential health risk under conservative assumptions.", "คำเตือน: ค่า HI เกิน 1 ซึ่งอาจมีความเสี่ยงภายใต้สมมติฐานการรับสัมผัส"),
    "am.hi_low": ("OK: HI is 1 or lower under current exposure assumptions.", "ปกติ: ค่า HI ไม่เกิน 1 ภายใต้สมมติฐานปัจจุบัน"),
    "am.no_fish": ("No fish concentration provided. HQ/HI omitted.", "ไม่มีข้อมูลโลหะในกล้ามเนื้อปลา จึงไม่ได้คำนวณ HQ/HI"),
    "am.s4": ("4. Concentration Comparison", "4. เปรียบเทียบความเข้มข้นโลหะหนัก"),
    "am.conc_title": ("Concentrations in Fish Muscle", "ความเข้มข้นในกล้ามเนื้อปลา"),
    "am.conc_cap": ("User input values (mg/kg wet weight).", "ค่าที่ป้อนเข้า (มก./กก. น้ำหนักเปียก)"),
    "axis.metal": ("Metal", "ชนิดโลหะ"),
    "axis.conc": ("Concentration (mg/kg)", "ความเข้มข้น (mg/kg)"),
    "am.s5": ("5. Hazard Quotients (HQ)", "5. ค่าดัชนีอันตรายรายสาร (HQ)"),
    "am.hq_title": ("Hazard Quotient by Metal", "ค่า HQ แยกตามชนิดโลหะ"),
    "am.hq_cap": ("Red bar indicates HQ > 1 screening threshold.", "แท่งสีแดงแสดงค่า HQ ที่เกินเกณฑ์มาตรฐาน 1"),
    "am.table": ("Summary Data Table", "ตารางสรุปผลการคัดกรอง"),
    "col.metal": ("Metal", "ชนิดโลหะ"),
    "col.conc": ("Concentration (mg/kg)", "ความเข้มข้น (mg/kg)"),
    "col.rfd": ("RfD (mg/kg/day)", "ค่า RfD (mg/kg/วัน)"),
    "col.hq": ("HQ", "ค่า HQ"),
    "col.hi": ("HI", "ค่า HI"),
    "col.bw": ("Body weight (kg)", "น้ำหนักตัว (kg)"),
    "col.ir": ("Consumption (kg/day)", "ปริมาณบริโภค (kg/วัน)"),
    "col.record": ("Record Type", "ประเภทระเบียน"),
    "col.scenario": ("Scenario", "สถานการณ์"),
    "col.sed_cr": ("Sediment Cr (mg/kg)", "โครเมียมในตะกอน (mg/kg)"),
    "rec.fish": ("Fish Muscle", "กล้ามเนื้อปลา"),
    "rec.sediment": ("Sediment Scenario", "สถานการณ์ตะกอน"),
    "rec.summary": ("Summary", "สรุป"),
    "am.s6": ("6. Sediment Chromium Scenarios", "6. การจำลองสถานการณ์โครเมียมในตะกอน"),
    "am.s6_desc": ("Simulated dynamics over time under 3 intervention scenarios.", "การเปลี่ยนแปลงของโครเมียมในตะกอนภายใต้ 3 สถานการณ์"),
    "scn.A": ("A - Baseline (No action)", "A - สถานการณ์ฐาน (ไม่ดำเนินมาตรการ)"),
    "scn.B": ("B - Partial reduction", "B - ลดการปนเปื้อนบางส่วน"),
    "scn.C": ("C - Active remediation", "C - ฟื้นฟูสภาพอย่างเข้มข้น"),
    "am.sed_title": ("Sediment Cr Concentration Trajectory", "แนวโน้มความเข้มข้นโครเมียมในตะกอน"),
    "am.sed_cap": ("Hypothetical decay/accumulation trends.", "การจำลองการเพิ่มขึ้นหรือลดลงตามสมมติฐาน"),
    "axis.year": ("Year", "ปี"),
    "axis.sed": ("Sediment Cr (mg/kg)", "โครเมียมในตะกอน (mg/kg)"),
    "am.sed_summary": ("Year {h} Projections", "ประมาณการ ณ ปีที่ {h}"),
    "am.s7": ("7. Export", "7. ส่งออกผลลัพธ์"),
    "dl.am": ("Download AquaMonitor CSV", "ดาวน์โหลดผลการประเมิน (CSV)"),
    "am.limits": ("Limitations", "ข้อจำกัดสำคัญ"),
    "am.limits_text": ("Screening-level model based on assumed RfD parameters.", "แบบจำลองระดับการคัดกรอง อ้างอิงพารามิเตอร์ RfD สมมติ"),
    "am.footer": ("AquaMonitor Module | Part of Data Repository", "AquaMonitor Module | ส่วนหนึ่งของคลังข้อมูล"),

    # Methods
    "me.desc": ("Methods and mathematical formulas.", "ระเบียบวิธี คำนวณ และเอกสารอ้างอิง"),
    "me.1": ("1. Biological baseline observations", "1. ข้อมูลทางชีววิทยาอ้างอิง"),
    "me.1_t": ("Source experimental observations at 29°C and 32°C.", "ค่าจากการทดลองจริงที่ 29°C และ 32°C"),
    "me.1_cap": ("Reference data reproduced in Supplementary File S1.", "ข้อมูลอ้างอิงจากเอกสารเสริม S1"),
    "col.temp_ref": ("Temperature (°C)", "อุณหภูมิ (°C)"),
    "me.2": ("2. Production pipeline formulas", "2. สมการการคำนวณผลผลิต"),
    "me.2_t": ("Linear multiplication cascade across stages.", "การคูณตามลำดับขั้นของการฟักและการรอด"),
    "me.3": ("3. Rate interpolation model", "3. แบบจำลองการประมาณค่าอัตราทางชีววิทยา"),
    "me.3_t": ("Linear interpolation with boundary clamps.", "การประมาณค่าเชิงเส้นร่วมกับการคงค่าปลายทาง"),
    "me.4": ("4. Climate scenario model", "4. แบบจำลองสถานการณ์ภูมิอากาศ"),
    "me.4_t": ("Sinusoidal seasonal variation with trend terms.", "แบบจำลองฤดูกาลแบบไซน์ร่วมกับแนวโน้มระยะยาว"),
    "me.5": ("5. Seasonal response model", "5. แบบจำลองการตอบสนองตามฤดูกาล"),
    "me.5_t": ("Gaussian survival equation.", "สมการอัตรารอดแบบเกาส์เซียน"),
    "me.6": ("6. Monte Carlo simulations", "6. การจำลองสุ่มมอนติคาร์โล"),
    "me.6_t": ("10,000 iterations for climate uncertainty.", "การสุ่มจำลอง 10,000 ครั้งเพื่อประเมินความไม่แน่นอน"),
    "me.7": ("7. Thermal threshold shift", "7. การเปลี่ยนแปลงเกณฑ์ความทนทาน"),
    "me.7_t": ("Annual threshold progression.", "การขยับของเกณฑ์ความทนทานรายปี"),
    "me.8": ("8. Sensitivity analysis methodology", "8. ระเบียบวิธีวิเคราะห์ความไว"),
    "me.8_t": ("Stepwise parameter variation.", "การปรับเปลี่ยนตัวแปรตามลำดับขั้นตอน"),
    "me.9": ("9. Limitations and scope", "9. ข้อจำกัดและขอบเขต"),
    "me.9_t": ("Prototype decision-support tool. Not a substitute for local trials.", "ต้นแบบเครื่องมือสนับสนุน ไม่สามารถทดแทนการทดลองจริงในพื้นที่"),
    "me.10": ("10. Reproducibility", "10. การทำซ้ำผลลัพธ์"),
    "me.10_t": ("Fixed random seeds and exportable CSVs.", "ใช้ค่า Random Seed คงที่และสามารถส่งออก CSV ได้"),
    "me.11": ("11. Heavy metal HQ calculation", "11. การคำนวณดัชนีความเสี่ยงโลหะหนัก"),
    "me.11_t1": ("HQ = (Conc * IR) / (BW * RfD); HI = Sum(HQ)", "สมการ HQ = (ความเข้มข้น * ปริมาณบริโภค) / (น้ำหนักตัว * RfD) และ HI = ผลรวม HQ"),
    "me.11_rfd": ("Reference Dose (RfD) Values", "ค่าอ้างอิงความเป็นพิษ (RfD)"),
    "me.11_t2": ("First-order sediment accumulation/decay dynamics.", "พลวัตการสะสมและการสลายตัวของโลหะหนักในตะกอน"),
}


# ============================================================
# 3. STATE AND HELPERS
# ============================================================
WIDGET_DEFAULTS = {
    "language": "English",
    "page": "overview",
    "eggs": 5_000_000,
    "fry_price": 1.50,
    "base_cost": 100_000.0,
    "cooling_cost": 80_000.0,
    "ov_temp": 29.0,
    "calc_temp": 29.0,
    "clim_sd": float(E_SD),
    "clim_dg": float(DELTA_G),
    "clim_seed": int(SEED),
    "sens_base_temp": 29.0,
    "sens_temp_range": (-2.0, 2.0),
    "sens_eggs": 5_000_000,
    "sens_price": 1.50,
    "sens_cost": 100_000.0,
    "sens_cooling": 80_000.0,
    "sens_include_cooling": False,
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
    for key, default in WIDGET_DEFAULTS.items():
        st.session_state.setdefault(key, default)


def is_thai():
    return st.session_state.get("language", "English") == "ไทย"


def t(key, **kwargs):
    english, thai = TEXT[key]
    text = thai if is_thai() else english
    return text.format(**kwargs) if kwargs else text


def relabel(df):
    return df.rename(columns={c: t(c) for c in df.columns if c in TEXT})


def csv_bytes(df):
    return relabel(df).to_csv(index=False).encode("utf-8-sig")


_STRETCH = {"use_container_width": True}


def show_table(df, formats=None, index=False):
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

.stApp { background-color: #F4F8FA; color: #1F2D3A; }
.block-container { padding-top: 2rem !important; padding-bottom: 3.5rem; max-width: 1180px; }

[data-testid="stSidebar"] {
    background-color: #E8F1F4;
    border-right: 1px solid #D4E2E8;
}

h1 { color: #123B4A; font-weight: 700; }
h2, h3, h4 { color: #1B5565; font-weight: 600; }

.pg-head { border-bottom: 2px solid #CFE0E6; padding-bottom: 0.8rem; margin-bottom: 1.2rem; }
.pg-head h1 { margin: 0 0 0.2rem 0; font-size: 1.8rem; }
.pg-head p { margin: 0; color: #4A6270; font-size: 1rem; }

.brand { margin-bottom: 0.8rem; }
.brand .name { font-weight: 700; color: #123B4A; font-size: 1.1rem; }
.brand .tag { color: #4A6270; font-size: 0.85rem; margin-top: 0.2rem; }

[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border: 1px solid #DCE7EC;
    border-left: 4px solid #1F7A8C;
    padding: 14px;
    border-radius: 8px;
}

.sec { margin: 1.8rem 0 0.5rem 0; }
.sec h3 { margin: 0; font-size: 1.2rem; color: #1B5565; }
.sec .rule { height: 3px; width: 40px; background: #1F7A8C; margin-top: 0.3rem; border-radius: 2px; }

.chip { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 0.9rem;
        border-radius: 8px; border: 1px solid; font-size: 0.95rem; margin: 0.5rem 0 1rem 0; }
.chip-ok { background: #E6F3F5; border-color: #BCDCE2; color: #14505D; }
.chip-caution { background: #FDF1E3; border-color: #F0D2AC; color: #7A4510; }
.chip-alert { background: #FBE9E7; border-color: #F0BDB6; color: #7C241A; }

footer { visibility: hidden; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def style_fig(fig, title, x_title, y_title, height=400, legend=True):
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0.0, font=dict(size=15, color=NAVY, family=FONT_STACK)),
        font=dict(family=FONT_STACK, size=12, color="#1F2D3A"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=10, r=10, t=50, b=10),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="left", x=0.0),
        xaxis=dict(title=dict(text=x_title), gridcolor=GRID, linecolor="#B9CAD2"),
        yaxis=dict(title=dict(text=y_title), gridcolor=GRID, linecolor="#B9CAD2"),
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
    st.markdown(
        f'<div class="chip chip-{level}"><span>{html.escape(text)}</span></div>',
        unsafe_allow_html=True,
    )


def assumptions_expander(temp, eggs, price, base_cost, cooling_cost):
    with st.expander(t("assump.title")):
        st.write(t("assump.temp", v=f"{temp:.1f}"))
        st.write(t("assump.eggs", v=f"{eggs:,.0f}"))
        st.write(t("assump.price", v=f"{price:,.2f}"))
        st.write(t("assump.opcost", v=f"{base_cost:,.2f}"))
        st.write(t("assump.cooling", v=f"{cooling_cost:,.2f}"))


# ============================================================
# 6. PAGES
# ============================================================
def hatchery_inputs():
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


# --- 6.1 Overview ---
def page_overview():
    page_header(t("nav.overview"), t("ov.desc"))
    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs()

    temp = temperature_slider("ov_temp")
    fert, hatch, survival = biological_rates(temp)

    survivors = eggs * fert * hatch * survival
    revenue = survivors * fry_price
    cost = base_cost + cooling_cost
    net_result = revenue - cost

    st.markdown(f"**{t('ov.status_title')}**")
    if temp <= REFERENCE["Temperature (°C)"][0]:
        status_chip("ok", t("ov.status_low"))
    elif temp < REFERENCE["Temperature (°C)"][1]:
        status_chip("caution", t("ov.status_mid"))
    else:
        status_chip("alert", t("ov.status_high"))

    section(t("ov.bio"))
    a, b, c = st.columns(3)
    a.metric(t("m.fert"), f"{fert:.1%}")
    b.metric(t("m.hatch"), f"{hatch:.1%}")
    c.metric(t("m.surv72"), f"{survival:.1%}")

    section(t("ov.econ"))
    d, e, f = st.columns(3)
    d.metric(t("m.survivors"), f"{survivors:,.0f}")
    e.metric(t("m.revenue_ill"), f"฿{revenue:,.2f}")
    f.metric(t("m.cost"), f"฿{cost:,.2f}")

    st.metric(t("m.net"), f"฿{net_result:,.2f}")
    assumptions_expander(temp, eggs, fry_price, base_cost, cooling_cost)


# --- 6.2 Calculator ---
def page_calculator():
    page_header(t("nav.calculator"), t("calc.desc"))
    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs()

    temp = temperature_slider("calc_temp")
    fert, hatch, survival = biological_rates(temp)

    fertilized = eggs * fert
    hatched = fertilized * hatch
    survivors = hatched * survival

    revenue = survivors * fry_price
    total_cost = base_cost + cooling_cost
    net_result = revenue - total_cost

    section(t("calc.s1"))
    a, b, c = st.columns(3)
    a.metric(t("m.fert"), f"{fert:.1%}")
    b.metric(t("m.hatch"), f"{hatch:.1%}")
    c.metric(t("m.surv72"), f"{survival:.1%}")

    section(t("calc.s2"))
    results = pd.DataFrame({
        "col.stage": [t("stage.eggs"), t("stage.fert"), t("stage.hatched"), t("stage.surv")],
        "col.count": [eggs, fertilized, hatched, survivors],
    })

    fig = go.Figure(go.Bar(
        x=results["col.stage"], y=results["col.count"],
        marker_color=[SLATE, TEAL, BLUE, NAVY],
        texttemplate="%{y:.3s}", textposition="outside",
    ))
    style_fig(fig, t("calc.chart_title"), t("axis.stage"), t("axis.count"), legend=False)
    show_fig(fig)

    show_table(results, {"col.count": "{:,.0f}"})

    section(t("calc.s3"))
    x, y, z = st.columns(3)
    x.metric(t("m.revenue"), f"฿{revenue:,.2f}")
    y.metric(t("m.cost"), f"฿{total_cost:,.2f}")
    z.metric(t("m.net"), f"฿{net_result:,.2f}")


# --- 6.3 Climate ---
def page_climate():
    page_header(t("nav.climate"), t("clim.desc"))

    section(t("clim.controls"))
    c1, c2, c3 = st.columns(3)
    with c1:
        anomaly_sd = st.slider(t("in.anomaly_sd"), 0.0, 1.0, key="clim_sd")
    with c2:
        delta_g = st.slider(t("in.delta_g"), 0.10, 0.20, key="clim_dg")
    with c3:
        seed = st.number_input(t("in.seed"), min_value=0, key="clim_seed")

    day = np.arange(1, 366)
    temp_day = seasonal_temperature(day, 0)
    survival_pct = SMAX * np.exp(-0.5 * ((temp_day - TOPT) / SIGMA) ** 2)

    section(t("clim.a"))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("kpi.peak_temp"), f"{temp_day.max():.2f} °C")
    k2.metric(t("kpi.peak_day"), f"{int(day[int(np.argmax(temp_day))])}")
    k3.metric(t("kpi.days_above"), f"{int((temp_day > TCRIT0).sum())}")
    k4.metric(t("kpi.max_surv"), f"{survival_pct.max():.1f}%")

    fig_temp = go.Figure()
    fig_temp.add_trace(go.Scatter(x=day, y=temp_day, mode="lines", name=t("legend.mean"), line=dict(color=COLOR_TEMPERATURE)))
    style_fig(fig_temp, t("clim.seasonal_title"), t("axis.doy"), t("axis.temp"))
    show_fig(fig_temp)


# --- 6.4 Sensitivity ---
def page_sensitivity():
    page_header(t("nav.sensitivity"), t("sens.desc"))
    section(t("sens.baseline_set"))
    base_temp = st.slider(t("in.base_temp"), T_MIN_DOMAIN, T_MAX_DOMAIN, key="sens_base_temp")
    
    fert, hatch, surv = biological_rates(base_temp)
    eggs, fry_price, base_cost, cooling_cost = hatchery_inputs()
    survivors = eggs * fert * hatch * surv
    
    st.metric(t("m.survivors"), f"{survivors:,.0f}")


# --- 6.5 AquaMonitor (Heavy Metal Assessment) ---
def _reset_aquamonitor():
    for key in ("am_cr", "am_pb", "am_ni", "am_cd", "am_sediment"):
        st.session_state[key] = None
    st.session_state["am_weight"] = 50.0
    st.session_state["am_horizon"] = 5
    st.session_state["am_analyzed"] = False


def page_aquamonitor():
    page_header(t("nav.aquamonitor"), t("am.subtitle"))
    st.write(t("am.desc"))
    st.info(t("am.info"))

    section(t("am.s1"))
    st.caption(t("am.s1_cap"))

    with st.container():
        left, right = st.columns(2)
        with left:
            cr = st.number_input(t("metal.Cr"), min_value=0.0, key="am_cr", format="%.4f")
            ni = st.number_input(t("metal.Ni"), min_value=0.0, key="am_ni", format="%.4f")
        with right:
            pb = st.number_input(t("metal.Pb"), min_value=0.0, key="am_pb", format="%.4f")
            cd = st.number_input(t("metal.Cd"), min_value=0.0, key="am_cd", format="%.4f")

        bw = st.number_input(t("in.bw"), min_value=1.0, key="am_weight")

    section(t("am.s2"))
    sed_cr = st.number_input(t("in.sediment"), min_value=0.0, key="am_sediment", format="%.2f")
    horizon = st.slider(t("in.horizon"), 1, 20, key="am_horizon")

    b1, b2 = st.columns(2)
    with b1:
        if st.button(t("btn.analyze"), type="primary", **_STRETCH):
            st.session_state["am_analyzed"] = True
    with b2:
        st.button(t("btn.reset"), on_click=_reset_aquamonitor, **_STRETCH)

    if not st.session_state.get("am_analyzed"):
        st.info(t("am.prompt"))
        return

    # Process Results
    measured = {"Cr": cr, "Pb": pb, "Ni": ni, "Cd": cd}
    valid_measured = {k: v for k, v in measured.items() if v is not None and v > 0}

    if not valid_measured and (sed_cr is None or sed_cr == 0):
        st.error(t("am.err_nodata"))
        return

    section(t("am.s3"))
    if valid_measured:
        hqs = {}
        for m, c in valid_measured.items():
            hqs[m] = (c * FISH_CONSUMPTION_RATE) / (bw * RFD[m])
        hi = sum(hqs.values())
        above_one = sum(1 for v in hqs.values() if v > 1.0)

        m1, m2, m3 = st.columns(3)
        m1.metric(t("am.k_metals"), f"{len(valid_measured)}")
        m2.metric(t("am.k_hi"), f"{hi:.3f}")
        m3.metric(t("am.k_above"), f"{above_one}")

        if hi > 1.0:
            status_chip("alert", t("am.hi_high"))
        else:
            status_chip("ok", t("am.hi_low"))

        # Bar chart for HQ
        section(t("am.s5"))
        fig_hq = go.Figure(go.Bar(
            x=list(hqs.keys()), y=list(hqs.values()),
            marker_color=[RED if v > 1.0 else TEAL for v in hqs.values()]
        ))
        fig_hq.add_hline(y=1.0, line_dash="dash", line_color=RED)
        style_fig(fig_hq, t("am.hq_title"), t("axis.metal"), "HQ", legend=False)
        show_fig(fig_hq)

    if sed_cr and sed_cr > 0:
        section(t("am.s6"))
        years = np.arange(horizon + 1)
        scenarios = {
            "A": sediment_model(sed_cr, horizon, sed_cr, 0.05),
            "B": sediment_model(sed_cr, horizon, 0.85 * sed_cr, 0.07),
            "C": sediment_model(sed_cr, horizon, 0.0, 0.10),
        }
        fig_sed = go.Figure()
        for k, v in scenarios.items():
            fig_sed.add_trace(go.Scatter(x=years, y=v, mode="lines+markers", name=t(f"scn.{k}")))
        style_fig(fig_sed, t("am.sed_title"), t("axis.year"), t("axis.sed"))
        show_fig(fig_sed)


# --- 6.6 Methods ---
def page_methods():
    page_header(t("nav.methods"), t("me.desc"))
    section(t("me.1"))
    st.write(t("me.1_t"))
    show_table(pd.DataFrame(REFERENCE))

    section(t("me.11"))
    st.write(t("me.11_t1"))
    show_table(pd.DataFrame({"Metal": list(RFD.keys()), "RfD (mg/kg/day)": list(RFD.values())}))


# ============================================================
# 7. MAIN ENTRY POINT
# ============================================================
def main():
    st.set_page_config(
        page_title="Catfish Thermal Risk Dashboard",
        page_icon="🐟",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_state()
    inject_css()

    # Sidebar Header
    st.sidebar.markdown(
        f'<div class="brand"><div class="name">{html.escape(t("app.name"))}</div>'
        f'<div class="tag">{html.escape(t("app.tagline"))}</div></div>',
        unsafe_allow_html=True,
    )

    # Language Selector
    st.sidebar.selectbox(
        t("lang.label"),
        options=LANG_OPTIONS,
        key="language",
    )

    # Data Repository Sub-navigation Menu
    st.sidebar.markdown(f"### {t('nav.title')}")
    page_map = {
        t("nav.overview"): "overview",
        t("nav.calculator"): "calculator",
        t("nav.climate"): "climate",
        t("nav.sensitivity"): "sensitivity",
        t("nav.aquamonitor"): "aquamonitor",
        t("nav.methods"): "methods",
    }

    selected_label = st.sidebar.radio(
        t("nav.label"),
        options=list(page_map.keys()),
        index=0,
        label_visibility="collapsed",
    )
    st.session_state["page"] = page_map[selected_label]

    st.sidebar.markdown("---")

    # Global Hatchery Parameters (Sidebar)
    if st.session_state["page"] in ["overview", "calculator", "sensitivity"]:
        st.sidebar.markdown(f"**{t('side.assump')}**")
        st.sidebar.number_input(t("in.eggs"), min_value=1, key="eggs")
        st.sidebar.number_input(t("in.price"), min_value=0.0, step=0.1, key="fry_price")
        st.sidebar.number_input(t("in.base_cost"), min_value=0.0, step=5000.0, key="base_cost")
        st.sidebar.number_input(t("in.cooling"), min_value=0.0, step=5000.0, key="cooling_cost")

    # Page Routing
    page = st.session_state["page"]
    if page == "overview":
        page_overview()
    elif page == "calculator":
        page_calculator()
    elif page == "climate":
        page_climate()
    elif page == "sensitivity":
        page_sensitivity()
    elif page == "aquamonitor":
        page_aquamonitor()
    elif page == "methods":
        page_methods()


if __name__ == "__main__":
    main()

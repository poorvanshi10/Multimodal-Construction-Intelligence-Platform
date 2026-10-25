"""
Multimodal Construction Intelligence Platform
Skill Wallet Capstone Project 1
Streamlit + Google Gemini (google-genai SDK). No database. 1-click deploy.
"""
import io
import json
import re
import urllib.parse
from datetime import datetime

import streamlit as st
from PIL import Image

try:
    from google import genai
    from google.genai import types
    GENAI_OK = True
except Exception:  # SDK missing -> demo mode still works
    GENAI_OK = False

st.set_page_config(page_title="Construction Intelligence Platform", page_icon="🏗️", layout="wide")

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown("""
<style>
.hero{background:linear-gradient(120deg,#0f2027,#203a43,#2c5364);color:#fff;padding:1.4rem 1.8rem;
      border-radius:14px;margin-bottom:1rem}
.hero h1{margin:0;font-size:1.9rem;color:#fff}.hero p{margin:.3rem 0 0;opacity:.85}
.card{background:var(--secondary-background-color);border:1px solid rgba(128,128,128,.25);
      border-radius:12px;padding:1rem 1.2rem;text-align:center}
.card .v{font-size:1.8rem;font-weight:700}.card .l{font-size:.8rem;opacity:.7;text-transform:uppercase;letter-spacing:.05em}
.pill{display:inline-block;padding:.2rem .8rem;border-radius:999px;font-weight:600;font-size:.82rem;color:#fff}
.p-ok{background:#2e9e5b}.p-warn{background:#e0a100}.p-bad{background:#e67e22}.p-crit{background:#c0392b}.p-info{background:#3b82c4}
.hz{border-left:5px solid #888;padding:.6rem 1rem;margin:.5rem 0;border-radius:6px;background:var(--secondary-background-color)}
.hz.Low{border-color:#2e9e5b}.hz.Medium{border-color:#e0a100}.hz.High{border-color:#e67e22}.hz.Critical{border-color:#c0392b}
.alert{padding:.8rem 1rem;border-radius:8px;margin:.4rem 0;border-left:5px solid #c0392b;background:rgba(192,57,43,.1)}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Gemini helpers
# ----------------------------------------------------------------------------
def get_client(api_key: str):
    if not (api_key and GENAI_OK):
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.sidebar.error(f"Gemini client error: {e}")
        return None


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
        raise


def analyze_image(client, model: str, image: Image.Image, prompt: str) -> dict:
    """Send image + prompt to Gemini, return parsed JSON."""
    resp = client.models.generate_content(
        model=model,
        contents=[image, prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2),
    )
    return parse_json(resp.text)


def load_image(upload) -> Image.Image:
    img = Image.open(io.BytesIO(upload.getvalue())).convert("RGB")
    img.thumbnail((1600, 1600))
    return img


def card(label, value):
    return f'<div class="card"><div class="v">{value}</div><div class="l">{label}</div></div>'


def pill(text, kind):
    return f'<span class="pill p-{kind}">{text}</span>'


SEV_KIND = {"Low": "ok", "Medium": "warn", "High": "bad", "Critical": "crit"}

# ----------------------------------------------------------------------------
# Prompts
# ----------------------------------------------------------------------------
SAFETY_PROMPT = """You are a certified construction safety officer (OSHA 1926 and IS 456 / Indian site practice).
Analyse this construction site photo. Audit each visible worker's PPE: helmet, high-vis vest, steel-toe boots,
safety harness (needed for work at height). Also identify site hazards (unprotected edges, poor scaffolding,
housekeeping, electrical, formwork/reinforcement defects relevant to IS 456, etc.).
If something cannot be seen, mark it "Not Visible" rather than guessing.
Return ONLY JSON in this schema:
{"safety_score": int 0-100,
 "overall_status": "Compliant" | "Needs Improvement" | "Non-Compliant" | "Critical Risk",
 "workers_detected": int,
 "ppe_detection": {"helmet": "Detected|Missing|Not Visible", "high_vis_vest": "...", "steel_toe_boots": "...", "safety_harness": "..."},
 "hazards": [{"hazard": str, "severity": "Low|Medium|High|Critical", "standard_reference": str, "remedy": str}],
 "summary": str}"""

CRACK_PROMPT = """You are a senior structural engineer. Examine this concrete/wall surface image.
Classify the defect as exactly one of: Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling.
Estimate crack width in mm (visual estimate; state uncertainty). Return ONLY JSON:
{"defect_type": str, "confidence_pct": int, "estimated_crack_width_mm": float,
 "pattern_description": str, "root_causes": [str], 
 "recommended_repairs": [{"method": str, "details": str}],
 "urgency": "Low|Medium|High|Critical", "monitoring_advice": str,
 "disclaimer": "Visual AI estimate; confirm with an on-site structural engineer."}
Repair options may include epoxy injection, structural re-grouting, polymer-modified mortar patching, jacketing, flexible sealant."""

# ----------------------------------------------------------------------------
# Demo-mode data
# ----------------------------------------------------------------------------
DEMO_SAFETY = {
    "safety_score": 58, "overall_status": "Needs Improvement", "workers_detected": 4,
    "ppe_detection": {"helmet": "Detected", "high_vis_vest": "Missing", "steel_toe_boots": "Not Visible", "safety_harness": "Missing"},
    "hazards": [
        {"hazard": "Worker at height without harness", "severity": "Critical", "standard_reference": "OSHA 1926.501",
         "remedy": "Stop work; provide full-body harness anchored to a rated lifeline."},
        {"hazard": "Exposed rebar ends without caps", "severity": "High", "standard_reference": "OSHA 1926.701(b)",
         "remedy": "Fit mushroom caps on all protruding reinforcement."},
        {"hazard": "Debris on walkways", "severity": "Medium", "standard_reference": "OSHA 1926.25",
         "remedy": "Daily housekeeping and designated material stacking zones."}],
    "summary": "DEMO: Partial PPE compliance; fall-protection gaps need immediate action."}

DEMO_CRACK = {
    "defect_type": "Settlement", "confidence_pct": 72, "estimated_crack_width_mm": 3.5,
    "pattern_description": "DEMO: Diagonal stepped crack widening toward the top.",
    "root_causes": ["Differential foundation settlement", "Poor soil compaction", "Nearby excavation or water-table change"],
    "recommended_repairs": [
        {"method": "Epoxy injection", "details": "Low-viscosity epoxy after settlement has stabilised."},
        {"method": "Structural re-grouting", "details": "Cement/polymer grout under footing if settlement is active."}],
    "urgency": "High", "monitoring_advice": "Install tell-tale gauges; re-measure every 2 weeks for 3 months.",
    "disclaimer": "Demonstration output. Confirm with an on-site structural engineer."}

WEATHER = {
    "High Wind": ("💨", "p-crit", [
        "Suspend all crane and hoisting operations when wind exceeds ~35 km/h (check manufacturer limit).",
        "Secure scaffolding sheets, formwork panels and loose materials.",
        "Stop work at height; evacuate workers from edges and top floors."]),
    "Heavy Rain": ("🌧️", "p-info", [
        "De-energise temporary electrical panels; use RCCB/ELCB-protected, waterproof connections.",
        "Cover freshly poured concrete with tarpaulin; halt pours if rain is forecast.",
        "Pump out excavations and inspect trench shoring for collapse risk.",
        "Anti-slip measures on ramps and scaffold boards."]),
    "Extreme Heat": ("🔥", "p-bad", [
        "Mandatory hydration breaks (water + ORS) every 45–60 min; shaded rest areas.",
        "Concrete curing: begin within 2 hrs of finishing, wet-cure / use curing compound, pour in early morning or evening (IS 456 cl. 13.5).",
        "Avoid heavy tasks 12:00–15:00; monitor workers for heat stress."]),
    "Normal": ("☀️", "p-ok", [
        "Conditions favourable. Proceed with the planned schedule.",
        "Continue daily toolbox talk and PPE checks."]),
}

# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.title("🏗️ CIP Control")
    api_key = st.text_input("Google Gemini API Key", type="password",
                            help="Never stored; kept in session memory only.",
                            value=st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else "")
    model_name = st.selectbox("Model", ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"])
    client = get_client(api_key)
    if client:
        st.success("Live AI mode")
    else:
        st.warning("Demonstration mode (sample outputs)" + ("" if GENAI_OK else " – google-genai not installed"))
    st.divider()
    st.markdown("**Modules**\n1. Site Safety & PPE Audit\n2. Crack Diagnostics\n3. Planning & Valuation\n4. Site Assistant")
    with st.expander("Architecture overview"):
        st.markdown(
            "- **UI:** Streamlit tabs, custom CSS\n"
            "- **Vision/LLM:** Gemini multimodal → strict JSON\n"
            "- **Valuation:** deterministic rate model\n"
            "- **Rendering:** Pollinations AI image URL\n"
            "- **State:** `st.session_state` only (no DB)")
    st.caption("AI output is advisory; verify with qualified engineers.")

st.markdown('<div class="hero"><h1>🏗️ Multimodal Construction Intelligence Platform</h1>'
            '<p>Safety auditing · Structural diagnostics · Valuation · Weather-aware site advisory</p></div>',
            unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🦺 Safety & PPE", "🧱 Crack Diagnostics", "📈 Planning & Valuation", "🌦️ Site Assistant"])

# ----------------------------------------------------------------------------
# Tab 1 – Safety
# ----------------------------------------------------------------------------
with tab1:
    st.subheader("Site Safety & PPE Audit")
    up = st.file_uploader("Upload site photo", type=["jpg", "jpeg", "png"], key="safety_up")
    if up:
        try:
            img = load_image(up)
        except Exception as e:
            st.error(f"Could not read image: {e}")
            img = None
        if img:
            c1, c2 = st.columns([1, 1.3])
            c1.image(img, use_container_width=True)
            if c2.button("Run safety audit", type="primary", key="run_safety"):
                with st.spinner("Analysing site…"):
                    try:
                        st.session_state.safety = analyze_image(client, model_name, img, SAFETY_PROMPT) if client else DEMO_SAFETY
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
    r = st.session_state.get("safety")
    if r:
        score = int(r.get("safety_score", 0))
        status = r.get("overall_status", "Unknown")
        kind = "ok" if score >= 80 else "warn" if score >= 60 else "bad" if score >= 40 else "crit"
        m = st.columns(3)
        m[0].markdown(card("Safety Score", f"{score}/100"), unsafe_allow_html=True)
        m[1].markdown(card("Workers Detected", r.get("workers_detected", "–")), unsafe_allow_html=True)
        m[2].markdown(card("Status", pill(status, kind)), unsafe_allow_html=True)
        st.progress(max(0, min(score, 100)) / 100)
        st.markdown("##### PPE Checklist")
        labels = {"helmet": "⛑️ Helmet", "high_vis_vest": "🦺 High-Vis Vest",
                  "steel_toe_boots": "🥾 Steel-Toe Boots", "safety_harness": "🪢 Safety Harness"}
        cols = st.columns(4)
        for col, (k, lab) in zip(cols, labels.items()):
            v = r.get("ppe_detection", {}).get(k, "Not Visible")
            col.markdown(card(lab, pill(v, {"Detected": "ok", "Missing": "crit"}.get(v, "info"))), unsafe_allow_html=True)
        st.markdown("##### Identified Hazards")
        for h in r.get("hazards", []):
            sev = h.get("severity", "Low")
            st.markdown(
                f'<div class="hz {sev}"><b>{h.get("hazard")}</b> {pill(sev, SEV_KIND.get(sev, "info"))}<br>'
                f'<small>{h.get("standard_reference", "")}</small><br>🔧 {h.get("remedy", "")}</div>',
                unsafe_allow_html=True)
        st.info(r.get("summary", ""))
        st.download_button("⬇️ Download JSON report", json.dumps(r, indent=2),
                           f"safety_report_{datetime.now():%Y%m%d_%H%M%S}.json", "application/json")

# ----------------------------------------------------------------------------
# Tab 2 – Cracks
# ----------------------------------------------------------------------------
with tab2:
    st.subheader("Crack Diagnostics & Structural Integrity")
    up2 = st.file_uploader("Upload concrete / wall surface", type=["jpg", "jpeg", "png"], key="crack_up")
    if up2:
        try:
            img2 = load_image(up2)
        except Exception as e:
            st.error(f"Could not read image: {e}")
            img2 = None
        if img2:
            c1, c2 = st.columns([1, 1.3])
            c1.image(img2, use_container_width=True)
            if c2.button("Diagnose defect", type="primary", key="run_crack"):
                with st.spinner("Inspecting surface…"):
                    try:
                        st.session_state.crack = analyze_image(client, model_name, img2, CRACK_PROMPT) if client else DEMO_CRACK
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
    c = st.session_state.get("crack")
    if c:
        urg = c.get("urgency", "Low")
        m = st.columns(4)
        m[0].markdown(card("Defect Type", c.get("defect_type", "–")), unsafe_allow_html=True)
        m[1].markdown(card("Crack Width", f'{c.get("estimated_crack_width_mm", "–")} mm'), unsafe_allow_html=True)
        m[2].markdown(card("Confidence", f'{c.get("confidence_pct", "–")}%'), unsafe_allow_html=True)
        m[3].markdown(card("Urgency", pill(urg, SEV_KIND.get(urg, "info"))), unsafe_allow_html=True)
        st.markdown(f"**Pattern:** {c.get('pattern_description', '')}")
        l, rr = st.columns(2)
        with l:
            st.markdown("##### Probable Root Causes")
            for x in c.get("root_causes", []):
                st.markdown(f"- {x}")
        with rr:
            st.markdown("##### Recommended Repairs")
            for x in c.get("recommended_repairs", []):
                st.markdown(f"- **{x.get('method')}** – {x.get('details')}")
        st.markdown(f"**Monitoring:** {c.get('monitoring_advice', '')}")
        st.caption(c.get("disclaimer", ""))
        st.download_button("⬇️ Download JSON report", json.dumps(c, indent=2),
                           f"crack_report_{datetime.now():%Y%m%d_%H%M%S}.json", "application/json")

# ----------------------------------------------------------------------------
# Tab 3 – Planning & Valuation
# ----------------------------------------------------------------------------
BUILD_COST = {"Residential House": 1800, "Apartment Block": 2200, "Commercial Office": 2600, "Industrial Warehouse": 1500}
TIER_COST_MULT = {"Tier 1": 1.25, "Tier 2": 1.0, "Tier 3": 0.85}
TIER_MARKET_RATE = {"Tier 1": 9500, "Tier 2": 5200, "Tier 3": 3000}  # INR/sqft, completed asset incl. land
STRUCT_VALUE_MULT = {"Residential House": 1.0, "Apartment Block": 1.1, "Commercial Office": 1.35, "Industrial Warehouse": 0.7}
STEEL_KG_SQFT = {"Residential House": 4.0, "Apartment Block": 4.5, "Commercial Office": 5.0, "Industrial Warehouse": 3.5}
CEMENT_BAGS_SQFT = 0.4
MILESTONES = [(15, "Foundation"), (30, "Plinth"), (55, "Superstructure"), (75, "Masonry & MEP"), (90, "Finishing"), (100, "Handover")]


def inr(v: float) -> str:
    if v >= 1e7:
        return f"₹{v / 1e7:,.2f} Cr"
    return f"₹{v / 1e5:,.2f} L"


with tab3:
    st.subheader("Planning & Real Estate Valuation")
    a, b, c3, d = st.columns(4)
    stype = a.selectbox("Structure type", list(BUILD_COST))
    sqft = b.number_input("Built-up area (sqft)", 200, 500000, 2000, 100)
    tier = c3.selectbox("Location tier", list(TIER_COST_MULT), index=1,
                        help="Tier 1: Mumbai, Delhi, Bengaluru · Tier 2: Indore, Pune, Jaipur · Tier 3: smaller cities")
    pct = d.slider("Completion %", 0, 100, 40)

    budget = sqft * BUILD_COST[stype] * TIER_COST_MULT[tier]
    capex = budget * pct / 100
    full_value = sqft * TIER_MARKET_RATE[tier] * STRUCT_VALUE_MULT[stype]
    land_share = 0.30  # land value exists regardless of construction progress
    current_value = full_value * (land_share + (1 - land_share) * pct / 100)
    steel_t = sqft * STEEL_KG_SQFT[stype] / 1000
    cement = sqft * CEMENT_BAGS_SQFT

    m = st.columns(4)
    m[0].markdown(card("Total Project Budget", inr(budget)), unsafe_allow_html=True)
    m[1].markdown(card("CapEx Incurred", inr(capex)), unsafe_allow_html=True)
    m[2].markdown(card("Current Asset Value", inr(current_value)), unsafe_allow_html=True)
    m[3].markdown(card("Value on Completion", inr(full_value)), unsafe_allow_html=True)
    m = st.columns(3)
    m[0].markdown(card("Steel Required", f"{steel_t:,.1f} t"), unsafe_allow_html=True)
    m[1].markdown(card("Cement Required", f"{cement:,.0f} bags"), unsafe_allow_html=True)
    m[2].markdown(card("Cement Remaining", f"{cement * (1 - pct / 100):,.0f} bags"), unsafe_allow_html=True)

    nxt = next((n for p, n in MILESTONES if pct < p), "Handover")
    st.markdown(f"##### Milestone progress – next: **{nxt}**")
    st.progress(pct / 100)
    st.markdown(" → ".join(f"{'✅' if pct >= p else '⬜'} {n} ({p}%)" for p, n in MILESTONES))
    st.caption("Indicative estimates from benchmark rates; not a certified valuation or BoQ.")

    st.markdown("##### 🎨 Conceptual 3D Architectural Rendering")
    style = st.selectbox("Style", ["modern minimalist", "contemporary Indian", "glass facade", "sustainable green building"])
    default_prompt = (f"Photorealistic 3D architectural rendering of a {style} {stype.lower()}, about {sqft} sqft, "
                      f"{'under construction, ' + str(pct) + '% complete with scaffolding' if pct < 100 else 'completed'}, "
                      f"Indian {tier} city setting, golden hour, ultra detailed")
    prompt = st.text_area("Image prompt (editable)", default_prompt, height=80)
    if st.button("Generate rendering"):
        st.session_state.render_url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
                                       + "?width=1024&height=640&nologo=true")
    if st.session_state.get("render_url"):
        st.image(st.session_state.render_url, caption="Generated via Pollinations AI (conceptual only)")

# ----------------------------------------------------------------------------
# Tab 4 – Assistant
# ----------------------------------------------------------------------------
CHAT_SYSTEM = ("You are a senior construction engineering assistant for Indian sites. Give concise, practical, "
               "standards-aware answers (IS codes, NBC 2016, OSHA). Flag safety-critical items clearly and "
               "recommend a licensed engineer for structural decisions.")


def demo_reply(q: str) -> str:
    q = q.lower()
    rules = [
        (("cure", "curing"), "Cure concrete for at least 7 days (OPC) or 10 days (blended cement) per IS 456; keep surfaces continuously moist."),
        (("m20", "mix", "grade"), "M20 nominal mix is 1:1.5:3 (cement:sand:aggregate) with w/c ≈ 0.5; use design mix for higher grades."),
        (("crane", "wind"), "Suspend crane lifts in high wind per the manufacturer's limit (commonly ~35 km/h)."),
        (("rebar", "steel", "cover"), "Nominal cover: 20 mm slabs, 25 mm beams, 40 mm columns (mild exposure) per IS 456 Table 16."),
        (("ppe", "helmet", "harness"), "Mandatory PPE: helmet, high-vis vest, safety boots, gloves; harness for work above 1.8 m."),
    ]
    for keys, ans in rules:
        if any(k in q for k in keys):
            return f"**(Demo mode)** {ans}"
    return "**(Demo mode)** Add a Gemini API key in the sidebar for full answers. Try asking about curing, concrete mix, rebar cover, or PPE."


with tab4:
    st.subheader("Daily Site Assistant & Weather-Aware Advisory")
    wx = st.radio("Today's weather condition", list(WEATHER), horizontal=True, index=3)
    icon, cls, alerts = WEATHER[wx]
    st.markdown(f'{icon} <span class="pill {cls}">{wx}</span>', unsafe_allow_html=True)
    for al in alerts:
        st.markdown(f'<div class="alert">⚠️ {al}</div>' if wx != "Normal" else f"✅ {al}", unsafe_allow_html=True)

    st.divider()
    st.markdown("##### 💬 Construction Engineering Assistant")
    if "chat" not in st.session_state:
        st.session_state.chat = [{"role": "assistant", "content": "Hello! Ask me anything about site work, materials, codes or safety."}]
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if st.button("Clear chat"):
        st.session_state.pop("chat")
        st.rerun()

    if user_q := st.chat_input("Ask the site assistant…"):
        st.session_state.chat.append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.markdown(user_q)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    if client:
                        history = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in st.session_state.chat[-12:])
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=f"Current weather on site: {wx}.\n{history}\nASSISTANT:",
                            config=types.GenerateContentConfig(system_instruction=CHAT_SYSTEM, temperature=0.4))
                        reply = resp.text
                    else:
                        reply = demo_reply(user_q)
                except Exception as e:
                    reply = f"⚠️ Assistant error: {e}"
            st.markdown(reply)
        st.session_state.chat.append({"role": "assistant", "content": reply})

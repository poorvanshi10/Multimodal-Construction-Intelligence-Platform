# 🏗️ Multimodal Construction Intelligence Platform

> AI-powered Streamlit app for construction site safety audits, structural crack diagnostics, project valuation and weather-aware site advisory, built on Google Gemini. *Skill Wallet Capstone Project 1.*

## Overview
Construction sites generate visual data (photos of workers, walls, slabs) that is rarely analysed systematically. This platform uses a multimodal LLM (Google Gemini) to turn site photos into structured, actionable reports, and pairs it with a planning calculator and a site assistant. It needs no database, so it deploys in one click on Streamlit Community Cloud.

## Features
| Module | What it does |
|---|---|
| 🦺 **Site Safety & PPE Audit** | Checks helmets, high-vis vests, steel-toe boots and harnesses against OSHA / IS 456 practice. Returns a 0–100 safety score, status, hazard list with severity (Low–Critical) and remedies, plus a downloadable JSON report. |
| 🧱 **Crack Diagnostics** | Classifies Hairline, Settlement, Structural Shear, Thermal Expansion or Spalling defects. Estimates crack width (mm), root causes, repairs (epoxy injection, re-grouting) and urgency. |
| 📈 **Planning & Valuation** | Estimates budget, capex incurred and current asset value in ₹ Lakhs/Crores by structure type, area, city tier (1/2/3) and completion %. Also gives steel/cement needs, a milestone tracker and an AI concept render (Pollinations). |
| 🌦️ **Site Assistant** | Weather-aware alerts (high wind, heavy rain, extreme heat) and a multi-turn engineering chatbot. |

A **demonstration mode** runs automatically when no API key is supplied.

## Tech Stack
Python · Streamlit · Google Gemini (`google-genai`) · Pillow · Pollinations AI

## Quick Start
```bash
git clone https://github.com/<your-username>/construction-intelligence-platform.git
cd construction-intelligence-platform
pip install -r requirements.txt
streamlit run app.py
```
Get a free key at [Google AI Studio](https://aistudio.google.com/apikey) and paste it into the sidebar. Without one, the app runs in demo mode.

## Deploy on Streamlit Community Cloud
1. Push this repo to GitHub.
2. Create a new app at [share.streamlit.io](https://share.streamlit.io) pointing to `app.py`.
3. *(Optional)* Add `GEMINI_API_KEY = "your-key"` under **Settings → Secrets**.

## Project Structure
```
├── app.py            # Streamlit application (all modules)
├── requirements.txt  # Dependencies
└── README.md
```

## Architecture
Streamlit tabs, with Gemini returning strict JSON for image analysis. Valuation uses a deterministic rate model, and state lives in `st.session_state` only.

## Disclaimer
Outputs are AI-generated and advisory. Valuation figures use benchmark assumptions and are not a certified valuation or bill of quantities. Always confirm structural and safety decisions with a qualified engineer.

## License
MIT

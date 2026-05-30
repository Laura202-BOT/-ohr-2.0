from flask import Flask, render_template_string, request
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ohr — Pre-Session Behavioral Summary</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #f4f3ee;
  color: #2c2c2a;
  min-height: 100vh;
  padding: 2rem;
  transition: background 0.3s, color 0.3s;
}
body.dark { background: #1a1a18; color: #e8e6e0; }

.container { max-width: 680px; margin: 0 auto; }

/* TOGGLE */
.theme-toggle {
  position: fixed;
  top: 16px;
  right: 20px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 2px solid #0F6E56;
  border-radius: 24px;
  padding: 8px 16px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  color: #0F6E56;
  box-shadow: 0 2px 10px rgba(0,0,0,0.12);
  transition: all 0.3s;
}
body.dark .theme-toggle { background: #242421; border-color: #1D9E75; color: #1D9E75; }
.theme-toggle:hover { opacity: 0.85; }
.toggle-icon { font-size: 16px; }

/* HEADER */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 14px;
  border-bottom: 2px solid #0F6E56;
  margin-bottom: 16px;
  margin-top: 56px;
}
.orh-tag { font-size: 11px; font-weight: 700; color: #0F6E56; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 4px; }
.patient-name { font-size: 22px; font-weight: 700; color: #2c2c2a; }
body.dark .patient-name { color: #f0ede6; }
.patient-meta { font-size: 12px; color: #888780; margin-top: 3px; }
.appt-lbl { font-size: 11px; color: #0F6E56; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 3px; text-align: right; font-weight: 700; }
.appt-date { font-size: 14px; font-weight: 700; color: #2c2c2a; text-align: right; }
body.dark .appt-date { color: #f0ede6; }
.appt-dr { font-size: 12px; color: #888780; margin-top: 2px; text-align: right; }

/* PLAIN ENGLISH SUMMARY */
.plain-summary {
  background: #fff;
  border-left: 5px solid #0F6E56;
  border-radius: 0 12px 12px 0;
  padding: 16px 20px;
  margin-bottom: 16px;
  font-size: 17px;
  font-weight: 600;
  color: #2c2c2a;
  line-height: 1.6;
  box-shadow: 0 3px 10px rgba(0,0,0,0.07);
}
body.dark .plain-summary { background: #242421; color: #e8e6e0; box-shadow: 0 3px 10px rgba(0,0,0,0.3); }
.plain-summary.concern { border-left-color: #C0392B; }
.plain-summary.warning { border-left-color: #BA7517; }
.plain-summary.stable { border-left-color: #0F6E56; }

/* ALERT BOX */
.alert-box {
  background: #fff8ee;
  border: 2px solid #BA7517;
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 16px;
  box-shadow: 0 3px 10px rgba(186,117,23,0.1);
}
body.dark .alert-box { background: #2a1f0e; box-shadow: none; }
.alert-title { font-size: 14px; font-weight: 700; color: #854F0B; margin-bottom: 5px; }
body.dark .alert-title { color: #EF9F27; }
.alert-body { font-size: 13px; color: #5c3a08; line-height: 1.6; }
body.dark .alert-body { color: #c4a05a; }
.stable-box {
  background: #f0faf6;
  border: 2px solid #0F6E56;
  border-radius: 12px;
  padding: 14px 18px;
  margin-bottom: 16px;
}
body.dark .stable-box { background: #0d2218; }
.stable-title { font-size: 14px; font-weight: 700; color: #0F6E56; margin-bottom: 4px; }
.stable-body { font-size: 13px; color: #1D9E75; line-height: 1.5; }

/* STATS ROW */
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.08);
  border: 1px solid #e8e6e0;
}
body.dark .stat-card { background: #242421; border-color: #333331; box-shadow: 0 3px 10px rgba(0,0,0,0.3); }
.stat-lbl { font-size: 10px; color: #888780; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 4px; font-weight: 700; }
.stat-val { font-size: 16px; font-weight: 700; }
.stat-sub { font-size: 10px; color: #888780; margin-top: 3px; line-height: 1.4; }
.c-amber { color: #BA7517; }
.c-teal { color: #0F6E56; }
.c-red { color: #C0392B; }
.c-light { color: #2c2c2a; }
body.dark .c-light { color: #e8e6e0; }

/* PASSIVE NOTE */
.passive-note {
  background: #f0faf6;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 16px;
  font-size: 11px;
  color: #5f5e5a;
  line-height: 1.6;
  border: 1px solid #c8eed9;
}
body.dark .passive-note { background: #0d2218; border-color: #0F6E56; color: #888780; }
.passive-note span { color: #0F6E56; font-weight: 700; }

/* SECTION LABEL */
.section-lbl { font-size: 11px; font-weight: 700; color: #888780; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 10px; }

/* FLIP CARD SYSTEM */
.signals { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }

.flip-card {
  width: 100%;
  height: 160px;
  perspective: 1200px;
  cursor: pointer;
}
.flip-card.expanded { height: auto; min-height: 160px; }

.flip-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.55s cubic-bezier(0.4, 0.2, 0.2, 1);
  transform-style: preserve-3d;
}
.flip-card.flipped .flip-card-inner { transform: rotateY(180deg); }

.flip-front, .flip-back {
  position: absolute;
  width: 100%;
  border-radius: 14px;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

/* FRONT */
.flip-front {
  background: #fff;
  border: 1px solid #e8e6e0;
  box-shadow: 0 4px 14px rgba(0,0,0,0.09);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 160px;
}
body.dark .flip-front { background: #242421; border-color: #333331; box-shadow: 0 4px 14px rgba(0,0,0,0.35); }

.front-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.sig-name { font-size: 14px; font-weight: 700; color: #2c2c2a; }
body.dark .sig-name { color: #e8e6e0; }
.badge { font-size: 10px; padding: 3px 10px; border-radius: 10px; font-weight: 700; }
.b-concern { background: #fde8e8; color: #C0392B; border: 1.5px solid #C0392B; }
.b-elevated { background: #fef3e2; color: #854F0B; border: 1.5px solid #BA7517; }
.b-stable { background: #e8f8f0; color: #0F6E56; border: 1.5px solid #0F6E56; }
.b-depressive { background: #e8f0fe; color: #1a56c4; border: 1.5px solid #2563EB; }
body.dark .b-concern { background: #3a1a1a; }
body.dark .b-elevated { background: #2a1f0e; }
body.dark .b-stable { background: #0d2218; }
body.dark .b-depressive { background: #0c1a2e; }

.sig-val-large { font-size: 28px; font-weight: 700; margin-bottom: 4px; }
.sig-plain-front { font-size: 12px; color: #5f5e5a; line-height: 1.5; }
body.dark .sig-plain-front { color: #aaa8a0; }
.flip-hint {
  font-size: 10px;
  color: #0F6E56;
  font-weight: 700;
  text-align: right;
  margin-top: 6px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
}
.flip-hint-arrow { font-size: 12px; }

/* BACK */
.flip-back {
  background: #fff;
  border: 1px solid #e8e6e0;
  box-shadow: 0 4px 14px rgba(0,0,0,0.09);
  padding: 18px 20px;
  transform: rotateY(180deg);
  min-height: 160px;
  height: auto;
}
body.dark .flip-back { background: #242421; border-color: #333331; box-shadow: 0 4px 14px rgba(0,0,0,0.35); }
.back-title { font-size: 12px; font-weight: 700; color: #0F6E56; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 10px; }
.back-item {
  font-size: 14px;
  color: #2c2c2a;
  line-height: 1.7;
  padding-left: 14px;
  position: relative;
  margin-bottom: 6px;
  font-weight: 500;
}
body.dark .back-item { color: #d8d6d0; }
.back-item::before { content: "·"; position: absolute; left: 0; color: #0F6E56; font-weight: 700; }
.back-conf { font-size: 12px; color: #888780; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e8e6e0; font-style: italic; line-height: 1.5; }
body.dark .back-conf { color: #666663; border-top-color: #333331; }
.flip-back-hint {
  font-size: 10px;
  color: #0F6E56;
  font-weight: 700;
  text-align: right;
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
}

/* MEDICATION */
.med-card {
  background: #fff;
  border-radius: 14px;
  padding: 16px 18px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.09);
  border: 1px solid #e8e6e0;
  margin-bottom: 16px;
}
body.dark .med-card { background: #242421; border-color: #333331; box-shadow: 0 4px 14px rgba(0,0,0,0.35); }
.med-title { font-size: 14px; font-weight: 700; color: #2c2c2a; margin-bottom: 6px; }
body.dark .med-title { color: #e8e6e0; }
.med-pill {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  margin-bottom: 8px;
}
.med-concern { background: #fde8e8; color: #C0392B; border: 1.5px solid #C0392B; }
.med-ok { background: #e8f8f0; color: #0F6E56; border: 1.5px solid #0F6E56; }
body.dark .med-concern { background: #3a1a1a; }
body.dark .med-ok { background: #0d2218; }
.med-text { font-size: 13px; color: #5f5e5a; line-height: 1.6; }
body.dark .med-text { color: #aaa8a0; }

/* AI SUMMARY */
.summary-box {
  background: #fff;
  border-radius: 14px;
  padding: 18px 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.09);
  border: 1px solid #e8e6e0;
  font-size: 14px;
  color: #2c2c2a;
  line-height: 1.8;
  white-space: pre-wrap;
}
body.dark .summary-box { background: #242421; border-color: #333331; color: #c8c6c0; box-shadow: 0 4px 14px rgba(0,0,0,0.35); }

/* FOOTER */
.footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-top: 14px;
  border-top: 1.5px solid #e8e6e0;
  margin-top: 8px;
  flex-wrap: wrap;
  gap: 8px;
}
body.dark .footer { border-top-color: #333331; }
.footer-brand { font-size: 14px; font-weight: 700; color: #0F6E56; letter-spacing: .08em; }
.footer-disc { font-size: 9px; color: #888780; margin-top: 3px; line-height: 1.5; max-width: 300px; }
.footer-right { font-size: 10px; color: #888780; text-align: right; line-height: 1.7; }

/* FORM */
.form-wrap { margin-top: 56px; }
.ohr-title { text-align: center; margin-bottom: 28px; }
.ohr-title .brand { font-size: 36px; font-weight: 700; color: #0F6E56; letter-spacing: .06em; }
.ohr-title .tagline { font-size: 15px; color: #888780; margin-top: 6px; }
.ohr-title .disc { font-size: 12px; color: #aaa8a0; margin-top: 6px; font-style: italic; }
.form-section {
  background: #fff;
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.09);
  border: 1px solid #e8e6e0;
}
body.dark .form-section { background: #242421; border-color: #333331; }
.form-title { font-size: 17px; font-weight: 700; color: #2c2c2a; margin-bottom: 20px; }
body.dark .form-title { color: #f0ede6; }
.form-group { margin-bottom: 18px; }
label { font-size: 12px; color: #888780; display: block; margin-bottom: 7px; text-transform: uppercase; letter-spacing: .05em; font-weight: 700; }
select, input[type=text] {
  width: 100%;
  background: #f4f3ee;
  border: 1.5px solid #d3d1c7;
  border-radius: 10px;
  color: #2c2c2a;
  padding: 12px 16px;
  font-size: 15px;
}
body.dark select, body.dark input[type=text] { background: #1a1a18; border-color: #444442; color: #e8e6e0; }
select:focus, input:focus { outline: none; border-color: #0F6E56; }
.btn {
  background: #0F6E56;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 14px 24px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  width: 100%;
  margin-top: 8px;
  box-shadow: 0 4px 14px rgba(15,110,86,0.3);
  transition: background 0.2s;
}
.btn:hover { background: #1D9E75; }
.back-link { display: block; text-align: center; margin-top: 18px; color: #0F6E56; font-size: 14px; font-weight: 700; text-decoration: none; }
</style>
</head>
<body id="body">

<button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">
  <span class="toggle-icon">🌙</span>
  <span id="themeLabel">Dark Mode</span>
</button>

<div class="container">

{% if not summary %}
<div class="form-wrap">
  <div class="ohr-title">
    <div class="brand">OHR</div>
    <div class="tagline">Pre-Session Behavioral Summary</div>
    <div class="disc">Clinical decision-support only. Not a diagnostic tool.</div>
  </div>
  <div class="form-section">
    <div class="form-title">Generate Pre-Session Summary</div>
    <form method="POST">
      <div class="form-group">
        <label>Patient File</label>
        <select name="patient_file">
          <option value="ohr_synthetic_patient_001.csv">Patient 001 — Manic Episode (Synthetic)</option>
          <option value="ohr_synthetic_patient_002_depressive.csv">Patient 002 — Depressive Episode (Synthetic)</option>
        </select>
      </div>
      <div class="form-group">
        <label>Patient Name / ID</label>
        <input type="text" name="patient_id" value="James R. — Patient #OHR-0042">
      </div>
      <div class="form-group">
        <label>Clinician</label>
        <input type="text" name="clinician" value="Dr. N. Hussain · Rutgers Psychiatry">
      </div>
      <div class="form-group">
        <label>Appointment</label>
        <input type="text" name="appt_date" value="Jun 2, 2026 · 11:00 AM">
      </div>
      <button type="submit" class="btn">Generate Summary</button>
    </form>
  </div>
</div>
{% endif %}

{% if summary %}
<div class="header">
  <div>
    <div class="orh-tag">Pre-Session Behavioral Summary</div>
    <div class="patient-name">{{ patient_id }}</div>
    <div class="patient-meta">Bipolar I Disorder · Outpatient · Monitoring period: 21 days</div>
  </div>
  <div>
    <div class="appt-lbl">Appointment</div>
    <div class="appt-date">{{ appt_date }}</div>
    <div class="appt-dr">{{ clinician }}</div>
  </div>
</div>

<div class="plain-summary {{ plain_class }}">{{ plain_english }}</div>

{% if alert %}
<div class="alert-box">
  <div class="alert-title">Behavioral change detected</div>
  <div class="alert-body">{{ alert }}</div>
</div>
{% else %}
<div class="stable-box">
  <div class="stable-title">No significant changes detected</div>
  <div class="stable-body">Behavioral patterns are within this patient's normal range since your last visit.</div>
</div>
{% endif %}

<div class="stats">
  <div class="stat-card">
    <div class="stat-lbl">Overall Pattern</div>
    <div class="stat-val {{ trend_color }}">{{ overall_trend }}</div>
    <div class="stat-sub">compared to patient's own baseline</div>
  </div>
  <div class="stat-card">
    <div class="stat-lbl">Confidence</div>
    <div class="stat-val c-teal">{{ confidence }}</div>
    <div class="stat-sub">{{ confidence_plain }}</div>
  </div>
  <div class="stat-card">
    <div class="stat-lbl">Medication Pattern</div>
    <div class="stat-val {{ med_color }}">{{ med_status }}</div>
    <div class="stat-sub">behavioral pattern only</div>
  </div>
</div>

<div class="passive-note">
  <span>How Ohr collects this data:</span> Sleep-wake timing, phone screen time, late-night activity, and 24-hour movement — collected automatically from Apple Health or Google Fit. The patient does not need to do anything.
</div>

<div class="section-lbl">Behavioral signals — tap any card to continue reading</div>
<div class="signals">

  <!-- SLEEP-WAKE PATTERN -->
  <div class="flip-card" id="card-sleep" onclick="flipCard('card-sleep')">
    <div class="flip-card-inner">
      <div class="flip-front">
        <div>
          <div class="front-top">
            <span class="sig-name">Sleep-Wake Pattern</span>
            <span class="badge {{ sleep_badge }}">{{ sleep_label }}</span>
          </div>
          <div class="sig-val-large {{ sleep_color }}">{{ sleep_avg }} hrs/night</div>
          <div class="sig-plain-front">{{ sleep_plain }}</div>
        </div>
        <div class="flip-hint"><span>Tap for details</span><span class="flip-hint-arrow">↷</span></div>
      </div>
      <div class="flip-back">
        <div class="back-title">Sleep-Wake Pattern — Detail</div>
        <div class="back-item">Average sleep over last 14 days: {{ sleep_avg }} hours per night</div>
        <div class="back-item">Patient's normal baseline: {{ baseline_sleep }} hours per night</div>
        <div class="back-item">Change from baseline: {{ sleep_pct }}%</div>
        <div class="back-item">Sleep data includes time asleep, time in bed, and periods of wakefulness collected via Apple Health or Google Fit</div>
        <div class="back-item">Note: Sleep tracking carries a margin of error. This signal is surfaced only when associated with other behavioral changes.</div>
        <div class="back-conf">Confidence: {{ sleep_confidence }} — {{ sleep_conf_reason }}</div>
        <div class="flip-back-hint"><span>Tap to return</span><span class="flip-hint-arrow">↶</span></div>
      </div>
    </div>
  </div>

  <!-- PHONE ACTIVITY -->
  <div class="flip-card" id="card-phone" onclick="flipCard('card-phone')">
    <div class="flip-card-inner">
      <div class="flip-front">
        <div>
          <div class="front-top">
            <span class="sig-name">Phone Activity</span>
            <span class="badge {{ phone_badge }}">{{ phone_label }}</span>
          </div>
          <div class="sig-val-large {{ phone_color }}">{{ phone_avg }} mins/day</div>
          <div class="sig-plain-front">{{ phone_plain }}</div>
        </div>
        <div class="flip-hint"><span>Tap for details</span><span class="flip-hint-arrow">↷</span></div>
      </div>
      <div class="flip-back">
        <div class="back-title">Phone Activity — Detail</div>
        <div class="back-item">Average daily screen time over last 14 days: {{ phone_avg }} minutes</div>
        <div class="back-item">Patient's normal baseline: {{ baseline_phone }} minutes per day</div>
        <div class="back-item">Change from baseline: {{ phone_pct }}%</div>
        <div class="back-item">Data collected passively via Apple Screen Time or Google Digital Wellbeing — no patient input required</div>
        <div class="back-conf">Elevated phone activity, particularly late at night, is associated with reduced sleep need and racing thoughts in bipolar disorder literature.</div>
        <div class="flip-back-hint"><span>Tap to return</span><span class="flip-hint-arrow">↶</span></div>
      </div>
    </div>
  </div>

  <!-- LATE NIGHT USAGE -->
  <div class="flip-card" id="card-night" onclick="flipCard('card-night')">
    <div class="flip-card-inner">
      <div class="flip-front">
        <div>
          <div class="front-top">
            <span class="sig-name">Late Night Usage</span>
            <span class="badge {{ night_badge }}">{{ night_label }}</span>
          </div>
          <div class="sig-val-large {{ night_color }}">{{ night_avg }} mins/night</div>
          <div class="sig-plain-front">{{ night_plain }}</div>
        </div>
        <div class="flip-hint"><span>Tap for details</span><span class="flip-hint-arrow">↷</span></div>
      </div>
      <div class="flip-back">
        <div class="back-title">Late Night Usage — Detail</div>
        <div class="back-item">Average phone usage between midnight and 4am over last 14 days: {{ night_avg }} minutes</div>
        <div class="back-item">Patient's normal late-night baseline: {{ baseline_night }} minutes</div>
        <div class="back-item">Change from baseline: {{ night_pct }}%</div>
        <div class="back-item">Late night phone activity is a validated proxy for nocturnal restlessness — a patient active on their phone at 2am may also be moving or pacing when they should be asleep</div>
        <div class="back-conf">Late night phone usage is associated with circadian rhythm disruption and reduced sleep need in bipolar disorder research.</div>
        <div class="flip-back-hint"><span>Tap to return</span><span class="flip-hint-arrow">↶</span></div>
      </div>
    </div>
  </div>

  <!-- 24-HOUR MOVEMENT -->
  <div class="flip-card" id="card-steps" onclick="flipCard('card-steps')">
    <div class="flip-card-inner">
      <div class="flip-front">
        <div>
          <div class="front-top">
            <span class="sig-name">24-Hour Movement</span>
            <span class="badge {{ steps_badge }}">{{ steps_label }}</span>
          </div>
          <div class="sig-val-large {{ steps_color }}">{{ steps_avg }} steps/day</div>
          <div class="sig-plain-front">{{ steps_plain }}</div>
        </div>
        <div class="flip-hint"><span>Tap for details</span><span class="flip-hint-arrow">↷</span></div>
      </div>
      <div class="flip-back">
        <div class="back-title">24-Hour Movement — Detail</div>
        <div class="back-item">Average daily step count over last 14 days: {{ steps_avg }} steps</div>
        <div class="back-item">Patient's normal baseline: {{ baseline_steps }} steps per day</div>
        <div class="back-item">Change from baseline: {{ steps_pct }}%</div>
        <div class="back-item">Movement is tracked across the full 24-hour period — including nighttime. A patient pacing at night when they should be asleep would register elevated step count during late hours, which combined with late night phone activity may indicate nocturnal restlessness.</div>
        <div class="back-conf">All movement data is relative to this patient's individual baseline — not compared to population averages.</div>
        <div class="flip-back-hint"><span>Tap to return</span><span class="flip-hint-arrow">↶</span></div>
      </div>
    </div>
  </div>

  <!-- CIRCADIAN RHYTHM -->
  <div class="flip-card" id="card-circadian" onclick="flipCard('card-circadian')">
    <div class="flip-card-inner">
      <div class="flip-front">
        <div>
          <div class="front-top">
            <span class="sig-name">Circadian Rhythm</span>
            <span class="badge {{ social_badge }}">{{ social_label }}</span>
          </div>
          <div class="sig-val-large {{ social_color }}">{{ social_avg }} / 4</div>
          <div class="sig-plain-front">{{ social_plain }}</div>
        </div>
        <div class="flip-hint"><span>Tap for details</span><span class="flip-hint-arrow">↷</span></div>
      </div>
      <div class="flip-back">
        <div class="back-title">Circadian Rhythm — Detail</div>
        <div class="back-item">Circadian rhythm refers to the patient's internal biological clock — when their body signals sleep and wakefulness relative to a 24-hour cycle. Disruption of this clock is associated with mood episode onset in bipolar disorder.</div>
        <div class="back-item">Current score: {{ social_avg }}/4 — Patient's normal baseline: {{ baseline_social }}/4 — Change: {{ social_change }} points</div>
        <div class="back-item">Score of 4 means stable circadian rhythm with consistent sleep-wake timing. Score of 1 means severely disrupted with no predictable biological rhythm pattern.</div>
        <div class="back-item">This score is derived from the consistency of sleep onset and wake times across the monitoring period, aligned with the BRIAN (Biological Rhythms Interview of Assessment in Neuropsychiatry) validated clinical framework.</div>
        <div class="back-conf">Circadian rhythm disruption has been identified as a pivotal driver in the pathophysiology of bipolar disorder — World Journal of Psychiatry, 2026.</div>
        <div class="flip-back-hint"><span>Tap to return</span><span class="flip-hint-arrow">↶</span></div>
      </div>
    </div>
  </div>

</div>

<!-- MEDICATION -->
<div class="section-lbl">Medication pattern</div>
<div class="med-card">
  <div class="med-title">Medication Adherence — Behavioral Pattern Only</div>
  <div class="med-pill {{ med_pill_class }}">{{ med_status }}</div>
  <div class="med-text">{{ med_note }}</div>
</div>

<!-- AI SUMMARY -->
<div class="section-lbl">AI-generated collateral summary</div>
<div class="summary-box">{{ summary }}</div>

<div class="footer">
  <div>
    <div class="footer-brand">OHR</div>
    <div class="footer-disc">Clinical decision-support only. Not a diagnostic tool. All signals are relative to this patient's individual baseline. Clinician judgment supersedes all outputs.</div>
  </div>
  <div class="footer-right">
    Generated {{ generated_time }}<br>
    Signal framework validated by Dr. Wirtz and Dr. Hussain<br>
    Rutgers University Hospital · Dept. of Psychiatry
  </div>
</div>

<a href="/" class="back-link">Generate another summary</a>
{% endif %}

</div>

<script>
function toggleTheme() {
  const body = document.getElementById('body');
  const label = document.getElementById('themeLabel');
  const icon = document.querySelector('.toggle-icon');
  body.classList.toggle('dark');
  if (body.classList.contains('dark')) {
    label.textContent = 'Light Mode';
    icon.textContent = '☀️';
  } else {
    label.textContent = 'Dark Mode';
    icon.textContent = '🌙';
  }
}

function flipCard(cardId) {
  const card = document.getElementById(cardId);
  card.classList.toggle('flipped');
  if (card.classList.contains('flipped')) {
    card.classList.add('expanded');
    const back = card.querySelector('.flip-back');
    card.style.height = Math.max(160, back.scrollHeight + 20) + 'px';
  } else {
    card.classList.remove('expanded');
    card.style.height = '160px';
  }
}
</script>
</body>
</html>
"""

def get_badge_and_color(pct_change, signal_type="generic"):
    if signal_type == "sleep_manic":
        if pct_change < -20: return "b-concern", "c-red", "Much less than usual"
        elif pct_change < -10: return "b-elevated", "c-amber", "Slightly less than usual"
        else: return "b-stable", "c-teal", "Normal range"
    elif signal_type == "sleep_depressive":
        if pct_change > 20: return "b-depressive", "c-light", "Much more than usual"
        else: return "b-stable", "c-teal", "Normal range"
    elif signal_type == "phone_manic":
        if pct_change > 50: return "b-elevated", "c-amber", "Much more than usual"
        else: return "b-stable", "c-teal", "Normal range"
    elif signal_type == "phone_depressive":
        if pct_change < -30: return "b-depressive", "c-light", "Much less than usual"
        else: return "b-stable", "c-teal", "Normal range"
    elif signal_type == "night":
        if pct_change > 100: return "b-concern", "c-red", "Very elevated"
        elif pct_change > 50: return "b-elevated", "c-amber", "Higher than usual"
        elif pct_change < -50: return "b-depressive", "c-light", "Lower than usual"
        else: return "b-stable", "c-teal", "Normal range"
    else:
        if pct_change > 30: return "b-elevated", "c-amber", "Higher than usual"
        elif pct_change < -30: return "b-depressive", "c-light", "Lower than usual"
        else: return "b-stable", "c-teal", "Normal range"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template_string(HTML_TEMPLATE, summary=None)

    patient_file = request.form.get("patient_file")
    patient_id   = request.form.get("patient_id")
    clinician    = request.form.get("clinician")
    appt_date    = request.form.get("appt_date")

    df = pd.read_csv(os.path.join(BASE_DIR, patient_file))

    baseline = df[df['day'] <= 7]
    recent   = df[df['day'] > 7]

    b_sleep  = baseline['sleep_hours'].mean()
    b_phone  = baseline['phone_usage_minutes'].mean()
    b_night  = baseline['late_night_usage_minutes'].mean()
    b_steps  = baseline['step_count'].mean()
    b_social = baseline['social_rhythm_score'].mean()

    r_sleep  = recent['sleep_hours'].mean()
    r_phone  = recent['phone_usage_minutes'].mean()
    r_night  = recent['late_night_usage_minutes'].mean()
    r_steps  = recent['step_count'].mean()
    r_social = recent['social_rhythm_score'].mean()

    med_gaps = (recent['medication_taken'] == 0).sum()

    sleep_pct  = round(((r_sleep - b_sleep) / b_sleep) * 100)
    phone_pct  = round(((r_phone - b_phone) / b_phone) * 100)
    night_pct  = round(((r_night - b_night) / max(b_night, 1)) * 100)
    steps_pct  = round(((r_steps - b_steps) / b_steps) * 100)
    social_chg = round(r_social - b_social, 1)

    sleep_flagged  = abs(sleep_pct)  > 20
    phone_flagged  = abs(phone_pct)  > 30
    night_flagged  = abs(night_pct)  > 50 and b_night > 2
    steps_flagged  = abs(steps_pct)  > 25
    social_flagged = abs(social_chg) > 0.5
    med_flagged    = med_gaps >= 3

    corroborating = sum([phone_flagged, night_flagged, steps_flagged, social_flagged, med_flagged])

    if sleep_flagged and corroborating >= 2:
        sleep_conf = "High"
        sleep_conf_reason = "multiple other behavioral signals changed simultaneously, confirming this is not data noise"
    elif sleep_flagged and corroborating == 1:
        sleep_conf = "Medium"
        sleep_conf_reason = "one additional signal also changed, partially supporting this finding"
    elif sleep_flagged:
        sleep_conf = "Low"
        sleep_conf_reason = "no other signals changed — this may be data noise rather than a clinical finding"
    else:
        sleep_conf = "Within baseline"
        sleep_conf_reason = "sleep is within this patient's expected range"

    total_flags = sum([sleep_flagged, phone_flagged, night_flagged, steps_flagged, social_flagged, med_flagged])

    if total_flags >= 4:
        confidence = "High"
        confidence_plain = "Multiple signals point in the same direction"
    elif total_flags >= 2:
        confidence = "Medium"
        confidence_plain = "Some signals have changed"
    else:
        confidence = "Low"
        confidence_plain = "Minimal signal deviation detected"

    is_depressive = sleep_pct > 15 and phone_pct < -20 and steps_pct < -20
    is_manic      = sleep_pct < -15 and (phone_pct > 30 or steps_pct > 25)

    first_name = patient_id.split()[0] if patient_id else "This patient"

    if is_manic:
        overall_trend = "Changes detected"
        trend_color   = "c-red"
        plain_class   = "concern"
        plain_english = f"{first_name} has been sleeping significantly less than usual and activity patterns have changed noticeably since your last visit. Worth exploring today."
        alert_text    = f"Sleep is {abs(sleep_pct)}% below {first_name}'s normal level. Late-night phone activity is also elevated. These changes together are associated with patterns seen prior to manic episodes."
    elif is_depressive:
        overall_trend = "Changes detected"
        trend_color   = "c-light"
        plain_class   = "warning"
        plain_english = f"{first_name} has been sleeping more than usual and appears to be moving and engaging less than their normal pattern. Worth exploring today."
        alert_text    = f"Sleep is {sleep_pct}% above {first_name}'s normal level. Daily movement and phone activity have both reduced significantly. These changes together are associated with patterns seen in depressive episodes."
    elif total_flags >= 2:
        overall_trend = "Some changes"
        trend_color   = "c-amber"
        plain_class   = "warning"
        plain_english = f"Some of {first_name}'s behavioral patterns look different from their usual baseline since your last visit."
        alert_text    = f"Multiple behavioral signals have shifted from {first_name}'s normal baseline. Confidence is medium."
    else:
        overall_trend = "Stable"
        trend_color   = "c-teal"
        plain_class   = "stable"
        plain_english = f"{first_name}'s behavioral patterns look consistent with their normal baseline since your last visit."
        alert_text    = None

    if med_flagged:
        med_status     = "Pattern shift detected"
        med_color      = "c-amber"
        med_pill_class = "med-concern"
        med_note       = f"Behavioral patterns over the past 14 days are associated with what is typically observed when patients in this population miss doses. Ohr cannot confirm whether medication was actually taken — this is a behavioral pattern signal only."
    else:
        med_status     = "No pattern shift"
        med_color      = "c-teal"
        med_pill_class = "med-ok"
        med_note       = f"Behavioral patterns do not suggest a medication adherence concern at this time. Ohr cannot confirm whether medication was actually taken — this is a behavioral pattern signal only."

    if is_depressive:
        sleep_badge, sleep_color, sleep_label = get_badge_and_color(sleep_pct, "sleep_depressive")
        phone_badge, phone_color, phone_label = get_badge_and_color(phone_pct, "phone_depressive")
    else:
        sleep_badge, sleep_color, sleep_label = get_badge_and_color(sleep_pct, "sleep_manic")
        phone_badge, phone_color, phone_label = get_badge_and_color(phone_pct, "phone_manic")

    night_badge, night_color, night_label = get_badge_and_color(night_pct, "night")
    steps_badge, steps_color, steps_label = get_badge_and_color(steps_pct)

    social_badge = "b-elevated" if abs(social_chg) > 0.5 else "b-stable"
    social_color = "c-amber" if abs(social_chg) > 0.5 else "c-teal"
    social_label = "Disrupted" if abs(social_chg) > 0.5 else "Stable circadian rhythm"

    sleep_plain = f"Usually sleeps {round(b_sleep,1)} hrs — now averaging {round(r_sleep,1)} hrs. That is {abs(sleep_pct)}% {'less' if sleep_pct < 0 else 'more'} than usual."
    phone_plain = f"Usually uses phone {round(b_phone):.0f} mins/day — now averaging {round(r_phone):.0f} mins. That is {abs(phone_pct)}% {'more' if phone_pct > 0 else 'less'} than usual."
    night_plain = f"Usually {round(b_night):.0f} mins of late-night phone use — now averaging {round(r_night):.0f} mins between midnight and 4am."
    steps_plain = f"Usually {round(b_steps):.0f} steps/day — now averaging {round(r_steps):.0f} steps across the full 24-hour period. That is {abs(steps_pct)}% {'more' if steps_pct > 0 else 'less'} than usual."
    social_plain = f"Circadian rhythm score: {round(r_social,1)}/4 compared to normal baseline of {round(b_social,1)}/4. {'Biological clock pattern has shifted.' if social_chg < -0.5 else 'Stable circadian rhythm.'}"

    clinical_data = f"""
PATIENT: {patient_id} | DIAGNOSIS: Bipolar I Disorder
APPOINTMENT: {appt_date} | {clinician}

BASELINE (Days 1-7):
  Sleep-Wake Pattern: {b_sleep:.1f} hrs/night | Phone: {b_phone:.0f} mins/day | Late-night: {b_night:.0f} mins | 24-Hour Movement: {b_steps:.0f} steps | Circadian Rhythm: {b_social:.1f}/4

RECENT (Days 8-21):
  Sleep-Wake Pattern: {r_sleep:.1f} hrs/night ({sleep_pct:+d}%) | Phone: {r_phone:.0f} mins/day ({phone_pct:+d}%) | Late-night: {r_night:.0f} mins ({night_pct:+d}%)
  24-Hour Movement: {r_steps:.0f} steps ({steps_pct:+d}%) | Circadian Rhythm: {r_social:.1f}/4 (change: {social_chg:+.1f})

MEDICATION PATTERN:
  {med_note}

CONFIDENCE: Sleep={sleep_conf} | Overall={confidence} | Corroborating signals={corroborating}/5
DATA SOURCE: Passively collected via Apple HealthKit and Google Fit. No patient input required.
NOTE: All signals are relative to this patient's individual baseline. Sleep data has a margin of error and is only surfaced when associated with other signals.
"""

    prompt = f"""You are Ohr, a passive behavioral monitoring collateral tool for psychiatrists treating bipolar disorder patients.

Generate a concise AI-generated collateral summary based on the behavioral data below. Follow these rules strictly:

1. Write in plain, clear clinical language. Avoid jargon.
2. Never tell the clinician what to do. Never make recommendations or suggest actions. Surface patterns only — the clinician decides what to do with them.
3. Never state that medication was or was not taken. Only describe behavioral patterns associated with what is typically observed during medication non-adherence.
4. Never present sleep as a standalone finding. Always reference associated signals.
5. Never make diagnostic conclusions. Ohr is a collateral tool — pattern observation only.
6. Do not use urgent or alarming language. Use measured, neutral clinical tone.
7. Use "associated with" instead of "correlated with" throughout.
8. Format the summary as concise bullet points — minimum words, maximum clarity. No paragraph sentences.
9. Only reference signals that can be passively collected from phone health APIs.

{clinical_data}

Format:
OVERALL PATTERN: [one neutral phrase]

SIGNAL OBSERVATIONS:
• Sleep-Wake Pattern: [one line]
• Phone Activity: [one line]
• Late Night Usage: [one line]
• 24-Hour Movement: [one line]
• Circadian Rhythm: [one line]

MEDICATION PATTERN: [one line — behavioral proxy only, never confirm or deny actual medication use]

IMPORTANT: Clinical decision-support only. Ohr is a collateral tool. All patterns relative to individual baseline. Clinician judgment supersedes all outputs."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=600
    )

    summary = response.choices[0].message.content
    generated_time = datetime.now().strftime("%b %d, %Y · %I:%M %p")

    return render_template_string(HTML_TEMPLATE,
        summary=summary,
        patient_id=patient_id,
        clinician=clinician,
        appt_date=appt_date,
        alert=alert_text,
        plain_english=plain_english,
        plain_class=plain_class,
        overall_trend=overall_trend,
        trend_color=trend_color,
        confidence=confidence,
        confidence_plain=confidence_plain,
        corroborating=corroborating,
        med_status=med_status,
        med_color=med_color,
        med_note=med_note,
        med_pill_class=med_pill_class,
        sleep_avg=round(r_sleep, 1),
        sleep_pct=f"{sleep_pct:+d}",
        sleep_badge=sleep_badge,
        sleep_color=sleep_color,
        sleep_label=sleep_label,
        sleep_plain=sleep_plain,
        sleep_confidence=sleep_conf,
        sleep_conf_reason=sleep_conf_reason,
        baseline_sleep=round(b_sleep, 1),
        phone_avg=round(r_phone),
        phone_pct=f"{phone_pct:+d}",
        phone_badge=phone_badge,
        phone_color=phone_color,
        phone_label=phone_label,
        phone_plain=phone_plain,
        baseline_phone=round(b_phone),
        night_avg=round(r_night),
        night_pct=f"{night_pct:+d}",
        night_badge=night_badge,
        night_color=night_color,
        night_label=night_label,
        night_plain=night_plain,
        baseline_night=round(b_night),
        steps_avg=round(r_steps),
        steps_pct=f"{steps_pct:+d}",
        steps_badge=steps_badge,
        steps_color=steps_color,
        steps_label=steps_label,
        steps_plain=steps_plain,
        baseline_steps=round(b_steps),
        social_avg=round(r_social, 1),
        social_change=social_chg,
        social_badge=social_badge,
        social_color=social_color,
        social_label=social_label,
        social_plain=social_plain,
        baseline_social=round(b_social, 1),
        generated_time=generated_time
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)

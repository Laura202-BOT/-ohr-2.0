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
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a18; color: #e8e6e0; min-height: 100vh; padding: 2rem; }
.container { max-width: 720px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 14px; border-bottom: 0.5px solid #333331; margin-bottom: 16px; }
.orh-tag { font-size: 10px; font-weight: 600; color: #1D9E75; text-transform: uppercase; letter-spacing: .1em; margin-bottom: 3px; }
.patient-name { font-size: 18px; font-weight: 500; color: #f0ede6; }
.patient-meta { font-size: 11px; color: #888780; margin-top: 2px; }
.appt-lbl { font-size: 10px; color: #1D9E75; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 2px; text-align: right; }
.appt-date { font-size: 13px; font-weight: 500; color: #f0ede6; text-align: right; }
.appt-dr { font-size: 11px; color: #888780; margin-top: 2px; text-align: right; }
.alert-box { background: #2a1f0e; border: 0.5px solid #BA7517; border-radius: 8px; padding: 12px 14px; margin-bottom: 14px; }
.alert-title { font-size: 12px; font-weight: 500; color: #EF9F27; margin-bottom: 4px; }
.alert-body { font-size: 11px; color: #c4a05a; line-height: 1.5; }
.stable-box { background: #0d2218; border: 0.5px solid #0F6E56; border-radius: 8px; padding: 12px 14px; margin-bottom: 14px; }
.stable-title { font-size: 12px; font-weight: 500; color: #1D9E75; margin-bottom: 4px; }
.stable-body { font-size: 11px; color: #1D9E75; line-height: 1.5; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 14px; }
.stat-card { background: #242421; border: 0.5px solid #333331; border-radius: 8px; padding: 10px 12px; }
.stat-lbl { font-size: 9px; color: #888780; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 3px; }
.stat-val { font-size: 14px; font-weight: 500; }
.stat-sub { font-size: 9px; color: #888780; margin-top: 2px; }
.c-amber { color: #EF9F27; }
.c-teal { color: #1D9E75; }
.c-red { color: #E24B4A; }
.c-light { color: #e8e6e0; }
.section-lbl { font-size: 9px; font-weight: 500; color: #888780; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }
.signals { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 14px; }
.sig-card { background: #242421; border: 0.5px solid #333331; border-radius: 8px; padding: 10px 12px; }
.sig-name { font-size: 12px; font-weight: 500; color: #e8e6e0; margin-bottom: 4px; }
.sig-val { font-size: 11px; margin-bottom: 2px; }
.sig-note { font-size: 10px; color: #888780; line-height: 1.4; }
.badge { font-size: 9px; padding: 2px 7px; border-radius: 8px; font-weight: 500; float: right; }
.b-concern { background: #3a1a1a; color: #E24B4A; border: 0.5px solid #A32D2D; }
.b-elevated { background: #2a1f0e; color: #EF9F27; border: 0.5px solid #BA7517; }
.b-stable { background: #0d2218; color: #1D9E75; border: 0.5px solid #0F6E56; }
.b-depressive { background: #0c1a2e; color: #60a5fa; border: 0.5px solid #2563EB; }
.summary-box { background: #242421; border: 0.5px solid #333331; border-radius: 8px; padding: 14px; margin-bottom: 14px; white-space: pre-wrap; font-size: 12px; color: #c8c6c0; line-height: 1.7; }
.footer { display: flex; justify-content: space-between; align-items: flex-end; padding-top: 12px; border-top: 0.5px solid #333331; margin-top: 8px; }
.footer-brand { font-size: 12px; font-weight: 600; color: #1D9E75; letter-spacing: .08em; }
.footer-disc { font-size: 8px; color: #666663; margin-top: 2px; line-height: 1.4; max-width: 280px; }
.footer-right { font-size: 9px; color: #666663; text-align: right; line-height: 1.6; }
.form-section { background: #242421; border: 0.5px solid #333331; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
.form-title { font-size: 14px; font-weight: 500; color: #f0ede6; margin-bottom: 16px; }
.form-group { margin-bottom: 14px; }
label { font-size: 11px; color: #888780; display: block; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .04em; }
select, input[type=text] { width: 100%; background: #1a1a18; border: 0.5px solid #444442; border-radius: 6px; color: #e8e6e0; padding: 8px 12px; font-size: 13px; }
select:focus, input:focus { outline: none; border-color: #1D9E75; }
.btn { background: #0F6E56; color: #fff; border: none; border-radius: 6px; padding: 10px 24px; font-size: 13px; font-weight: 500; cursor: pointer; width: 100%; margin-top: 4px; }
.btn:hover { background: #1D9E75; }
</style>
</head>
<body>
<div class="container">

{% if not summary %}
<div style="text-align:center; margin-bottom: 24px;">
  <div style="font-size: 28px; font-weight: 500; color: #1D9E75; letter-spacing: .06em;">OHR</div>
  <div style="font-size: 13px; color: #888780; margin-top: 4px;">Pre-Session Behavioral Summary Generator</div>
  <div style="font-size: 11px; color: #444442; margin-top: 8px; font-style: italic;">Clinical decision-support only. Not a diagnostic tool.</div>
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
      <label>Patient ID</label>
      <input type="text" name="patient_id" value="Marcus T. — Patient #OHR-0042">
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

{% if alert %}
<div class="alert-box">
  <div class="alert-title">Behavioral Alert — Review Recommended</div>
  <div class="alert-body">{{ alert }}</div>
</div>
{% else %}
<div class="stable-box">
  <div class="stable-title">No Alert — Behavioral Patterns Within Expected Range</div>
  <div class="stable-body">All signals within or near individual baseline. No significant deviations detected.</div>
</div>
{% endif %}

<div class="stats">
  <div class="stat-card">
    <div class="stat-lbl">Overall Trend</div>
    <div class="stat-val {{ trend_color }}">{{ overall_trend }}</div>
    <div class="stat-sub">vs. patient baseline</div>
  </div>
  <div class="stat-card">
    <div class="stat-lbl">Summary Confidence</div>
    <div class="stat-val c-teal">{{ confidence }}</div>
    <div class="stat-sub">{{ corroborating }} signals corroborated</div>
  </div>
  <div class="stat-card">
    <div class="stat-lbl">Medication Signal</div>
    <div class="stat-val {{ med_color }}">{{ med_status }}</div>
    <div class="stat-sub">Behavioral proxy only</div>
  </div>
</div>

<div class="section-lbl">Behavioral Signals — Last 14 Days vs. Individual Baseline</div>
<div class="signals">
  <div class="sig-card">
    <span class="badge {{ sleep_badge }}">{{ sleep_label }}</span>
    <div class="sig-name">Sleep</div>
    <div class="sig-val {{ sleep_color }}">{{ sleep_avg }} hrs/night</div>
    <div class="sig-note">Baseline {{ baseline_sleep }} hrs · {{ sleep_pct }}% vs baseline<br>Confidence: {{ sleep_confidence }}</div>
  </div>
  <div class="sig-card">
    <span class="badge {{ phone_badge }}">{{ phone_label }}</span>
    <div class="sig-name">Phone Activity</div>
    <div class="sig-val {{ phone_color }}">{{ phone_avg }} mins/day</div>
    <div class="sig-note">Baseline {{ baseline_phone }} mins · {{ phone_pct }}% vs baseline</div>
  </div>
  <div class="sig-card">
    <span class="badge {{ steps_badge }}">{{ steps_label }}</span>
    <div class="sig-name">Mobility</div>
    <div class="sig-val {{ steps_color }}">{{ steps_avg }} steps/day</div>
    <div class="sig-note">Baseline {{ baseline_steps }} steps · {{ steps_pct }}% vs baseline</div>
  </div>
  <div class="sig-card">
    <span class="badge {{ social_badge }}">{{ social_label }}</span>
    <div class="sig-name">Social Rhythm</div>
    <div class="sig-val {{ social_color }}">{{ social_avg }}/4</div>
    <div class="sig-note">Baseline {{ baseline_social }}/4 · {{ social_change }} point change</div>
  </div>
</div>

<div class="section-lbl">AI-Generated Clinical Summary</div>
<div class="summary-box">{{ summary }}</div>

<div class="footer">
  <div>
    <div class="footer-brand">OHR</div>
    <div class="footer-disc">Clinical decision-support only. Not a diagnostic tool. All signals relative to individual baseline. Sleep data weighted against corroborating signals. Clinician judgment supersedes all outputs.</div>
  </div>
  <div class="footer-right">
    Generated {{ generated_time }}<br>
    Signal framework validated by Dr. Wirtz and Dr. Hussain<br>
    Rutgers University Hospital · Dept. of Psychiatry
  </div>
</div>

<div style="margin-top: 16px; text-align: center;">
  <a href="/" style="color: #1D9E75; font-size: 12px; text-decoration: none;">Generate another summary</a>
</div>
{% endif %}

</div>
</body>
</html>
"""

def get_badge_and_color(pct_change, signal_type="generic"):
    if signal_type == "sleep_manic":
        if pct_change < -20: return "b-concern", "c-red", "High Concern"
        elif pct_change < -10: return "b-elevated", "c-amber", "Elevated"
        else: return "b-stable", "c-teal", "Stable"
    elif signal_type == "sleep_depressive":
        if pct_change > 20: return "b-depressive", "c-light", "Elevated"
        else: return "b-stable", "c-teal", "Stable"
    elif signal_type == "phone_manic":
        if pct_change > 50: return "b-elevated", "c-amber", "Elevated"
        else: return "b-stable", "c-teal", "Stable"
    elif signal_type == "phone_depressive":
        if pct_change < -30: return "b-depressive", "c-light", "Withdrawn"
        else: return "b-stable", "c-teal", "Stable"
    else:
        if abs(pct_change) > 30: return "b-elevated", "c-amber", "Elevated"
        else: return "b-stable", "c-teal", "Stable"

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
    r_meal   = recent['meal_regularity_score'].mean()

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
    elif sleep_flagged and corroborating == 1:
        sleep_conf = "Medium"
    elif sleep_flagged:
        sleep_conf = "Low — possible noise"
    else:
        sleep_conf = "Within baseline"

    total_flags = sum([sleep_flagged, phone_flagged, steps_flagged, social_flagged, med_flagged])
    confidence  = "High" if total_flags >= 4 else ("Medium" if total_flags >= 2 else "Low")

    is_depressive = sleep_pct > 15 and phone_pct < -20 and steps_pct < -20
    is_manic      = sleep_pct < -15 and (phone_pct > 30 or steps_pct > 25)

    if is_manic:
        overall_trend = "High Concern"
        trend_color   = "c-red"
        alert_text    = f"Pattern consistent with possible manic shift. Sleep {sleep_pct}% below baseline. Late-night activity significantly elevated. Confidence: {confidence}."
    elif is_depressive:
        overall_trend = "Depressive Pattern"
        trend_color   = "c-light"
        alert_text    = f"Pattern consistent with possible depressive episode. Sleep {sleep_pct}% above baseline. Mobility and social engagement significantly reduced. Confidence: {confidence}."
    elif total_flags >= 2:
        overall_trend = "Elevated"
        trend_color   = "c-amber"
        alert_text    = f"Multiple behavioral signals deviating from baseline. Review flagged signals. Confidence: {confidence}."
    else:
        overall_trend = "Stable"
        trend_color   = "c-teal"
        alert_text    = None

    med_status = "Possible Gap" if med_flagged else "No Signal"
    med_color  = "c-red" if med_flagged else "c-teal"

    if is_depressive:
        sleep_badge, sleep_color, sleep_label = get_badge_and_color(sleep_pct, "sleep_depressive")
        phone_badge, phone_color, phone_label = get_badge_and_color(phone_pct, "phone_depressive")
    else:
        sleep_badge, sleep_color, sleep_label = get_badge_and_color(sleep_pct, "sleep_manic")
        phone_badge, phone_color, phone_label = get_badge_and_color(phone_pct, "phone_manic")

    steps_badge, steps_color, steps_label = get_badge_and_color(steps_pct)
    social_badge = "b-elevated" if abs(social_chg) > 0.5 else "b-stable"
    social_color = "c-amber" if abs(social_chg) > 0.5 else "c-teal"
    social_label = "Disrupted" if abs(social_chg) > 0.5 else "Stable"

    clinical_data = f"""
PATIENT: {patient_id} | DIAGNOSIS: Bipolar I Disorder
APPOINTMENT: {appt_date} | {clinician}

BASELINE (Days 1-7):
  Sleep: {b_sleep:.1f} hrs/night | Phone: {b_phone:.0f} mins/day | Steps: {b_steps:.0f}/day | Social rhythm: {b_social:.1f}/4

RECENT (Days 8-21):
  Sleep: {r_sleep:.1f} hrs/night ({sleep_pct:+d}%) | Phone: {r_phone:.0f} mins/day ({phone_pct:+d}%) | Steps: {r_steps:.0f}/day ({steps_pct:+d}%)
  Social rhythm: {r_social:.1f}/4 | Meal regularity: {r_meal:.1f}/4 | Medication not taken: {med_gaps}/14 days

CONFIDENCE: Sleep={sleep_conf} | Overall={confidence} | Corroborating signals={corroborating}/5
NOTE: Sleep data carries margin of error. Weighted against corroborating signals only.
"""

    prompt = f"""You are Ohr, a clinical decision-support AI for psychiatrists.
Generate a concise Pre-Session Behavioral Summary. Use plain clinical language. Reference confidence levels. Never present sleep as a standalone finding. Never make diagnostic conclusions.

{clinical_data}

Format:
OVERALL TREND: [one word]
BEHAVIORAL ALERT: [Yes/No and one sentence if Yes]
SIGNAL HIGHLIGHTS: [4 bullet points, one per signal]
MEDICATION ADHERENCE SIGNAL: [one sentence, note it is a behavioral proxy]
CLINICAL FOCUS AREAS: [3 to 4 specific patterns worth exploring today]
IMPORTANT: Clinical decision-support only."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )

    summary = response.choices[0].message.content
    generated_time = datetime.now().strftime("%b %d, %Y · %I:%M %p")

    return render_template_string(HTML_TEMPLATE,
        summary=summary,
        patient_id=patient_id,
        clinician=clinician,
        appt_date=appt_date,
        alert=alert_text,
        overall_trend=overall_trend,
        trend_color=trend_color,
        confidence=confidence,
        corroborating=corroborating,
        med_status=med_status,
        med_color=med_color,
        sleep_avg=round(r_sleep, 1),
        sleep_pct=f"{sleep_pct:+d}",
        sleep_badge=sleep_badge,
        sleep_color=sleep_color,
        sleep_label=sleep_label,
        sleep_confidence=sleep_conf,
        baseline_sleep=round(b_sleep, 1),
        phone_avg=round(r_phone),
        phone_pct=f"{phone_pct:+d}",
        phone_badge=phone_badge,
        phone_color=phone_color,
        phone_label=phone_label,
        baseline_phone=round(b_phone),
        steps_avg=round(r_steps),
        steps_pct=f"{steps_pct:+d}",
        steps_badge=steps_badge,
        steps_color=steps_color,
        steps_label=steps_label,
        baseline_steps=round(b_steps),
        social_avg=round(r_social, 1),
        social_change=social_chg,
        social_badge=social_badge,
        social_color=social_color,
        social_label=social_label,
        baseline_social=round(b_social, 1),
        generated_time=generated_time
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)

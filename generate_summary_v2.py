import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# CHOOSE PATIENT FILE
# Switch between patients by changing the filename below
#PATIENT_FILE = "ohr_synthetic_patient_001.csv"          # Manic episode
PATIENT_FILE = "ohr_synthetic_patient_002_depressive.csv"  # Depressive episode

PATIENT_ID   = "Sarah M. — Patient #OHR-0043"
DIAGNOSIS    = "Bipolar I Disorder"
CLINICIAN    = "Dr. N. Hussain · Rutgers Psychiatry"
APPT_DATE    = "Apr 29, 2026 · 2:00 PM"

df = pd.read_csv(PATIENT_FILE)

# Baseline: first 7 days
baseline = df[df['day'] <= 7]
b_sleep   = baseline['sleep_hours'].mean()
b_phone   = baseline['phone_usage_minutes'].mean()
b_night   = baseline['late_night_usage_minutes'].mean()
b_steps   = baseline['step_count'].mean()
b_meal    = baseline['meal_regularity_score'].mean()
b_social  = baseline['social_rhythm_score'].mean()

# Recent: days 8-21
recent = df[df['day'] > 7]
r_sleep   = recent['sleep_hours'].mean()
r_phone   = recent['phone_usage_minutes'].mean()
r_night   = recent['late_night_usage_minutes'].mean()
r_steps   = recent['step_count'].mean()
r_meal    = recent['meal_regularity_score'].mean()
r_social  = recent['social_rhythm_score'].mean()

med_gaps           = (recent['medication_taken'] == 0).sum()
interrupted_nights = recent['sleep_interrupted'].sum()

# Percentage deviations
sleep_chg  = ((r_sleep  - b_sleep)  / b_sleep)  * 100
phone_chg  = ((r_phone  - b_phone)  / b_phone)  * 100
night_chg  = ((r_night  - b_night)  / max(b_night, 1)) * 100
steps_chg  = ((r_steps  - b_steps)  / b_steps)  * 100
meal_chg   = r_meal  - b_meal
social_chg = r_social - b_social

# CONFIDENCE SCORING
# Sleep is NEVER standalone — must be corroborated by at least one other signal
sleep_flagged  = abs(sleep_chg)  > 20
phone_flagged  = abs(phone_chg)  > 30
night_flagged  = abs(night_chg)  > 50 and b_night > 2
steps_flagged  = abs(steps_chg)  > 25
meal_flagged   = meal_chg        < -0.5
social_flagged = social_chg      < -0.5
med_flagged    = med_gaps        >= 3

corroborating_signals = sum([
    phone_flagged, night_flagged, steps_flagged,
    meal_flagged, social_flagged, med_flagged
])

if sleep_flagged and corroborating_signals >= 2:
    sleep_confidence = "High — corroborated by multiple signals"
elif sleep_flagged and corroborating_signals == 1:
    sleep_confidence = "Medium — corroborated by one additional signal"
elif sleep_flagged and corroborating_signals == 0:
    sleep_confidence = "Low — sleep change detected but no corroborating signals. Possible data noise."
else:
    sleep_confidence = "Within baseline range"

total_flags = sum([sleep_flagged, phone_flagged, steps_flagged,
                   meal_flagged, social_flagged, med_flagged])

if total_flags >= 4:
    overall_confidence = "High"
elif total_flags >= 2:
    overall_confidence = "Medium"
else:
    overall_confidence = "Low"

clinical_data = f"""
PATIENT: {PATIENT_ID}
DIAGNOSIS: {DIAGNOSIS}
APPOINTMENT: {APPT_DATE} | {CLINICIAN}
MONITORING PERIOD: 21 days

BASELINE (Days 1-7):
  Sleep:            {b_sleep:.1f} hrs/night
  Phone usage:      {b_phone:.0f} mins/day
  Late-night usage: {b_night:.0f} mins/night
  Daily steps:      {b_steps:.0f}
  Meal regularity:  {b_meal:.1f}/4
  Social rhythm:    {b_social:.1f}/4

RECENT PERIOD (Days 8-21):
  Sleep:            {r_sleep:.1f} hrs/night  ({sleep_chg:+.0f}% vs baseline)
  Phone usage:      {r_phone:.0f} mins/day   ({phone_chg:+.0f}% vs baseline)
  Late-night usage: {r_night:.0f} mins/night  ({night_chg:+.0f}% vs baseline)
  Daily steps:      {r_steps:.0f}            ({steps_chg:+.0f}% vs baseline)
  Meal regularity:  {r_meal:.1f}/4           ({meal_chg:+.1f} vs baseline)
  Social rhythm:    {r_social:.1f}/4         ({social_chg:+.1f} vs baseline)
  Interrupted sleep nights: {interrupted_nights} of 14
  Medication not taken:     {med_gaps} of 14 days

SIGNAL CONFIDENCE ASSESSMENT:
  Sleep signal confidence: {sleep_confidence}
  Corroborating signals flagged: {corroborating_signals} of 6
  Overall summary confidence: {overall_confidence}

IMPORTANT NOTE ON SLEEP DATA:
Sleep tracking from consumer devices carries an inherent margin of error.
This summary treats sleep as a contributory signal only, never as standalone evidence.
All sleep findings are weighted against corroborating behavioral signals before surfacing.
"""

prompt = f"""
You are Ohr, a clinical decision-support AI for psychiatrists treating bipolar disorder patients.

You are generating a Pre-Session Behavioral Summary delivered to the psychiatrist the night before an appointment. This is NOT a diagnostic tool. It surfaces behavioral patterns for the clinician to interpret using their own clinical judgment.

Based on the behavioral data and confidence assessment below, generate a concise Pre-Session Behavioral Summary. Use plain clinical language. Be specific with numbers. Always reflect the confidence levels provided. If sleep confidence is Low, explicitly note that the sleep finding is unconfirmed by other signals. Never present any single signal as a definitive clinical conclusion.

{clinical_data}

Format the output as follows:

OVERALL TREND: [Stable / Elevated / Depressive / High Concern]
SUMMARY CONFIDENCE: [High / Medium / Low] — [one sentence explaining why]

BEHAVIORAL ALERT: [Yes or No]
If Yes: [one sentence describing the pattern and confidence level]

SIGNAL HIGHLIGHTS:
Sleep: [finding + confidence note]
Phone activity: [finding]
Mobility: [finding]
Meal regularity: [finding]
Social rhythm: [finding]

MEDICATION ADHERENCE SIGNAL:
[What the behavioral data suggests — note this is a behavioral proxy, not confirmed adherence data]

CLINICAL FOCUS AREAS FOR TODAY'S SESSION:
[3 to 5 specific behavioral patterns worth exploring — not questions, just what the data flags, ordered by signal confidence]

IMPORTANT: Clinical decision-support only. All signals relative to individual baseline. Sleep data carries margin of error and is weighted against corroborating signals. Clinician judgment supersedes all outputs.
"""

print("\nGenerating Pre-Session Behavioral Summary...\n")
print("=" * 65)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
    max_tokens=1000
)

summary = response.choices[0].message.content
print(summary)
print("\n" + "=" * 65)
print("Summary generated by Ohr | Clinical decision-support only")

output_file = PATIENT_FILE.replace(".csv", "_summary.txt")
with open(output_file, "w") as f:
    f.write("OHR — PRE-SESSION BEHAVIORAL SUMMARY\n")
    f.write("=" * 65 + "\n\n")
    f.write(clinical_data)
    f.write("\n" + "=" * 65 + "\n\n")
    f.write("AI-GENERATED CLINICAL SUMMARY:\n\n")
    f.write(summary)
    f.write("\n\n" + "=" * 65 + "\n")
    f.write("Clinical decision-support only. Not a diagnostic tool.\n")
    f.write("All signals relative to individual patient baseline.\n")
    f.write("Sleep data weighted against corroborating signals.\n")

print(f"\nOutput saved to {output_file}")

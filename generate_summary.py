import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load patient data
df = pd.read_csv("ohr_synthetic_patient_001.csv")

# Calculate baseline (first 7 days)
baseline = df[df['day'] <= 7]
baseline_sleep = baseline['sleep_hours'].mean()
baseline_phone = baseline['phone_usage_minutes'].mean()
baseline_late_night = baseline['late_night_usage_minutes'].mean()
baseline_steps = baseline['step_count'].mean()

# Get recent period (last 14 days)
recent = df[df['day'] > 7]
recent_sleep = recent['sleep_hours'].mean()
recent_phone = recent['phone_usage_minutes'].mean()
recent_late_night = recent['late_night_usage_minutes'].mean()
recent_steps = recent['step_count'].mean()
medication_gaps = (recent['medication_taken'] == 0).sum()
sleep_interrupted_nights = recent['sleep_interrupted'].sum()

# Calculate deviations
sleep_change = ((recent_sleep - baseline_sleep) / baseline_sleep) * 100
phone_change = ((recent_phone - baseline_phone) / baseline_phone) * 100
late_night_change = ((recent_late_night - baseline_late_night) / baseline_late_night) * 100
steps_change = ((recent_steps - baseline_steps) / baseline_steps) * 100

# Build clinical data summary
clinical_data = f"""
PATIENT: Marcus T. | Patient #OHR-0042
DIAGNOSIS: Bipolar I Disorder
MONITORING PERIOD: 21 days
APPOINTMENT: Apr 29, 2026 | Dr. N. Hussain | Rutgers Psychiatry

BASELINE (Days 1-7):
- Sleep: {baseline_sleep:.1f} hrs/night
- Phone usage: {baseline_phone:.0f} mins/day
- Late night usage: {baseline_late_night:.0f} mins/night
- Daily steps: {baseline_steps:.0f}

RECENT PERIOD (Days 8-21):
- Sleep: {recent_sleep:.1f} hrs/night ({sleep_change:.0f}% vs baseline)
- Phone usage: {recent_phone:.0f} mins/day ({phone_change:.0f}% vs baseline)
- Late night usage: {recent_late_night:.0f} mins/night ({late_night_change:.0f}% vs baseline)
- Daily steps: {recent_steps:.0f} ({steps_change:.0f}% vs baseline)
- Nights with interrupted sleep: {sleep_interrupted_nights} of 14
- Days medication not taken: {medication_gaps} of 14
"""

# Generate Pre-Session Behavioral Summary using Groq
prompt = f"""
You are Ohr, a clinical decision-support AI for psychiatrists treating bipolar disorder patients.

You are generating a Pre-Session Behavioral Summary to be delivered to the psychiatrist the night before an appointment. This is NOT a diagnostic tool. It surfaces behavioral patterns for the clinician to interpret using their own clinical judgment.

Based on the following passive behavioral data, generate a concise one-page Pre-Session Behavioral Summary. Use plain clinical language. Be specific with numbers. Flag deviations clearly. Include an overall trend assessment, key signal highlights, medication adherence signal, and 3 to 5 clinical focus areas worth exploring in today's session — not prescribed questions, just signals that warrant attention.

{clinical_data}

Format the output as follows:

OVERALL TREND: [Stable / Elevated / Depressive / High Concern]

BEHAVIORAL ALERT: [Yes or No — and one sentence summary if yes]

SIGNAL HIGHLIGHTS:
- Sleep: [specific finding]
- Phone activity: [specific finding]
- Mobility: [specific finding]
- Social rhythm: [specific finding]

MEDICATION ADHERENCE SIGNAL:
[What the behavioral data suggests about medication compliance]

CLINICAL FOCUS AREAS FOR TODAY'S SESSION:
[3 to 5 specific behavioral signals worth exploring — not questions, just what the data flags]

IMPORTANT: This summary is a clinical decision-support tool only. All signals are relative to this patient's individual baseline. Clinician judgment supersedes all outputs.
"""

print("Generating Pre-Session Behavioral Summary...\n")
print("=" * 60)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=1000
)

summary = response.choices[0].message.content
print(summary)
print("\n" + "=" * 60)
print("\nSummary generated successfully by Ohr.")
print("Powered by Groq | Clinical decision-support only")

# Save output to file
with open("ohr_summary_output.txt", "w") as f:
    f.write("OHR — PRE-SESSION BEHAVIORAL SUMMARY\n")
    f.write("=" * 60 + "\n\n")
    f.write(clinical_data)
    f.write("\n" + "=" * 60 + "\n\n")
    f.write("AI-GENERATED CLINICAL SUMMARY:\n\n")
    f.write(summary)
    f.write("\n\n" + "=" * 60)
    f.write("\nClinical decision-support only. Not a diagnostic tool.")
    f.write("\nAll signals relative to individual patient baseline.")

print("\nOutput saved to ohr_summary_output.txt")
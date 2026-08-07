import numpy as np
import pandas as pd

np.random.seed(42)

N = 750

patient_id = [f"P{100000+i}" for i in range(N)]

age = np.random.randint(18, 75, N)

sex = np.random.choice(["Male", "Female"], N)

bmi = np.round(np.random.normal(26.5, 4.8, N), 1)
bmi = np.clip(bmi, 17, 42)

microbiome_diversity_index = np.round(
    np.random.normal(58, 14, N), 1
)
microbiome_diversity_index = np.clip(
    microbiome_diversity_index, 20, 95
)

beneficial_strain_count = np.random.randint(35, 180, N)

inflammatory_marker = np.round(
    np.random.normal(4.2, 1.8, N), 2
)
inflammatory_marker = np.clip(
    inflammatory_marker, 0.3, 10
)

bloating_score = np.random.randint(0, 11, N)

brain_fog_score = np.random.randint(0, 11, N)

fatigue_score = np.random.randint(0, 11, N)

bowel_irregularity_score = np.random.randint(0, 11, N)

stress_score = np.random.randint(0, 11, N)

probiotic_strains_prescribed = np.random.randint(8, 21, N)

adherence_percent = np.round(
    np.random.normal(86, 12, N), 1
)
adherence_percent = np.clip(
    adherence_percent, 45, 100
)

baseline_gut_health_score = (
    microbiome_diversity_index * 0.55
    + beneficial_strain_count * 0.18
    - inflammatory_marker * 2.3
    - bloating_score * 1.6
    - bowel_irregularity_score * 1.4
    - fatigue_score * 1.2
    - stress_score * 0.8
)

baseline_gut_health_score = np.round(
    np.clip(baseline_gut_health_score, 0, 100), 1
)

followup_days = np.random.randint(88, 95, N)

# --------------------------------------------------------------------
# Hidden relationship
# --------------------------------------------------------------------

score = (
    microbiome_diversity_index * 0.42
    + beneficial_strain_count * 0.19
    + adherence_percent * 0.27
    + probiotic_strains_prescribed * 1.4
    - inflammatory_marker * 4.8
    - bloating_score * 2.5
    - bowel_irregularity_score * 2.2
    - fatigue_score * 1.8
    - stress_score * 1.3
    + np.random.normal(0, 6, N)
)

threshold = np.percentile(score, 42)

treatment_response = (score > threshold).astype(int)

df = pd.DataFrame({
    "patient_id": patient_id,
    "age": age,
    "sex": sex,
    "bmi": bmi,
    "microbiome_diversity_index": microbiome_diversity_index,
    "beneficial_strain_count": beneficial_strain_count,
    "inflammatory_marker": inflammatory_marker,
    "bloating_score": bloating_score,
    "brain_fog_score": brain_fog_score,
    "fatigue_score": fatigue_score,
    "bowel_irregularity_score": bowel_irregularity_score,
    "stress_score": stress_score,
    "probiotic_strains_prescribed": probiotic_strains_prescribed,
    "adherence_percent": adherence_percent,
    "baseline_gut_health_score": baseline_gut_health_score,
    "followup_days": followup_days,
    "treatment_response": treatment_response
})

df.to_csv(
    "synthetic_microbiome_probiotic_response_v1.csv",
    index=False
)

print(df.head())

print("\nRows:", len(df))

print("\nTreatment Response Distribution")

print(df["treatment_response"].value_counts())
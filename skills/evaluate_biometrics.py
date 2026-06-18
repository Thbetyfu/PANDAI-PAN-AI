# PAN-AI/skills/evaluate_biometrics.py
# Module for evaluating biometric telemetry and classifying student cognitive/mental states.

from typing import Dict, Any

def evaluate_student_state(
    heart_rate: float,
    hrv: float,
    ear: float,
    gsr: float,
    focus_score: float
) -> Dict[str, Any]:
    """
    Classify student's cognitive and mental state based on raw biometric sensors.
    
    Why: By classifying these values on the server, we decouple the classification logic
    from the hardware client, allowing us to tweak diagnostic thresholds globally without
    having to redeploy client updates to individual school computers.
    """
    # Typical baselines:
    # Heart Rate (HR): normal resting 60-90 bpm. High stress > 95 bpm.
    # HRV: normal > 50 ms. Low HRV (high stress) < 40 ms.
    # Eye Aspect Ratio (EAR): open eyes ~0.25-0.30. Closed/drooping eyes < 0.20.
    # GSR (Galvanic Skin Response): normal 1.0-5.0 uS. High stress > 6.0 uS.
    
    state = "NORMAL"
    reason = "Kondisi belajar terpantau stabil dan optimal."

    if ear < 0.20 or focus_score < 40:
        state = "MENGANTUK"
        reason = "Deteksi kedipan mata lambat (EAR rendah) atau skor atensi menurun di bawah ambang batas."
    elif heart_rate > 95.0 or hrv < 40.0:
        state = "STRES"
        reason = "Detak jantung meningkat secara fisiologis disertai penurunan variabilitas detak jantung (HRV)."
    elif gsr > 6.0 and focus_score < 60:
        state = "FRUSTRASI"
        reason = "Lonjakan konduktansi kulit (GSR tinggi) dibarengi penurunan skor fokus belajar."
        
    return {
        "state": state,
        "reason": reason,
        "biometrics_snapshot": {
            "heart_rate": heart_rate,
            "hrv": hrv,
            "ear": ear,
            "gsr": gsr,
            "focus_score": focus_score
        }
    }

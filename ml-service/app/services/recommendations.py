"""Tövsiyələr: yalnız konkret model nəticələrinə və göstəricilərə bağlı, səbəbi və etibarlılığı göstərilən mətnlər.

Bu modul QƏRAR VERMİR və avtomatik idarəetmə əmri yaratmır: bütün tövsiyələr mühəndis təsdiqi tələb edir.
Hər tövsiyənin tətikləyici şərti aşağıdakı sabitlərlə aydın verilmişdir.
"""
from __future__ import annotations

import numpy as np

from app.services.quality import confidence_level
from app.utils.messages import label

FORECAST_DROP_PCT = -10.0      # 30 günlük proqnoz cari baza ilə müqayisədə bu həddən çox azalırsa
EFFICIENCY_DROP_POINTS = -5.0  # səmərəlilik 30 gündə bu qədər b.b.-dən çox azalırsa
WATERCUT_TREND_PTS_DAY = 0.05  # su payı artımı (faiz bəndi/gün)
TARGET_LOW = 0.85              # 30 günlük orta hasilat hədəfin bu hissəsindən azdırsa
DECLINE_FAST_PCT_DAY = 0.25    # hasilatın azalma sürəti (%/gün)


def _rec(rid, category, priority, text, reason, evidence, base_conf, strength) -> dict:
    score = float(np.clip(base_conf * strength, 0, 1))
    return {"id": rid, "category": category, "priority": priority, "text": text, "reason": reason,
            "evidence": evidence, "confidence": {"score": round(score, 2), "level": confidence_level(score)},
            "requiresEngineerReview": True}


def build(res: dict, feats: dict, quality: dict, base_conf: float) -> list[dict]:
    recs: list[dict] = []
    an, rk, eq, ef, pr = (res.get(k, {}) or {} for k in ("anomaly", "risk", "equipment", "efficiency", "production"))

    if an.get("anomalyDetected"):
        items = an.get("detectedAnomalies", [])
        names = ", ".join(i["label"] for i in items[:3]) or "bir sıra göstərici"
        high = any(i["severity"] == "high" for i in items)
        recs.append(_rec(
            "ANOM-1", "anomaly", "high" if high else "medium",
            f"Qeyri-adi dəyişiklik aşkarlanıb ({names}). Sensor göstəricilərinin düzgünlüyünün və quyunun əməliyyat "
            "şəraitinin mühəndis tərəfindən yoxlanılması məsləhətdir.",
            "İzolyasiya meşəsi balı həddi keçib və/və ya parametr quyunun öz son 30 günlük tarixçəsindən kəskin fərqlənir.",
            {"anomalyScore": an.get("anomalyScore"), "parameters": [{k: i[k] for k in ("parameter", "value", "expectedValue", "zScore")} for i in items[:3]]},
            base_conf, 0.9 if high else 0.7))

    if rk.get("riskLevel") in ("medium", "high"):
        top = ", ".join(r["label"] for r in rk.get("riskReasons", [])[:3]) or "model nəticəsi"
        recs.append(_rec(
            "RISK-1", "risk", "high" if rk["riskLevel"] == "high" else "medium",
            f"Quyunun əməliyyat risk səviyyəsi '{rk['riskLevel']}' qiymətləndirilib (əsas amillər: {top}). "
            "Quyunun vəziyyətinin mühəndis tərəfindən nəzərdən keçirilməsi məsləhətdir.",
            "Risk modeli çıxışı və tipik səviyyədən kənarlaşan göstəricilər.",
            {"riskScore": rk.get("riskScore"), "reasons": [r["text"] for r in rk.get("riskReasons", [])[:3]]},
            base_conf, 0.9 if rk["riskLevel"] == "high" else 0.65))

    if eq.get("maintenanceRecommended"):
        top = ", ".join(r["label"] for r in eq.get("failureFactors", [])[:3]) or "model nəticəsi"
        recs.append(_rec(
            "EQ-1", "equipment", "high" if eq.get("maintenanceRisk") == "high" else "medium",
            f"Nasos/avadanlıq üçün növbəti 30 gündə nasazlıq ehtimalı yüksək qiymətləndirilib (≈{eq['equipmentFailureProbability']*100:.0f}%). "
            f"Planlı texniki baxışın vaxtının yenidən nəzərdən keçirilməsi məsləhətdir (əsas amillər: {top}).",
            "Nasazlıq ehtimalı modelin qərar həddini keçib.",
            {"probability": eq.get("equipmentFailureProbability"), "threshold": eq.get("decisionThreshold"),
             "expectedDowntimeHours": eq.get("estimatedDowntime")},
            base_conf, 0.85))

    chg = pr.get("productionChangePct")
    if chg is not None and chg <= FORECAST_DROP_PCT:
        recs.append(_rec(
            "PROD-1", "production", "medium",
            f"Növbəti 30 gün üçün hasilatın cari səviyyədən təxminən {abs(chg):.1f}% azalması proqnozlaşdırılır. "
            "Təzyiq, su payı və avadanlıq göstəricilərinin səbəb təhlili məsləhətdir.",
            "30 günlük median proqnoz cari 7 günlük orta ilə müqayisə edilib.",
            {"productionChangePct": chg, "predictedProduction30d": pr.get("predictedProduction30d"),
             "baseline": pr.get("baselineProduction7dAvg")}, base_conf, 0.7))

    d = feats.get("production_decline_rate", np.nan)
    if np.isfinite(d) and d >= DECLINE_FAST_PCT_DAY:
        recs.append(_rec(
            "PROD-2", "production", "low",
            f"Son 90 gündə hasilat orta hesabla gündə ≈{d:.2f}% azalır. Azalmanın təbii (yataq) və ya əməliyyat səbəbli "
            "olduğunun müəyyənləşdirilməsi məsləhətdir.",
            "Hasilatın loqarifmik trendi (90 gün).", {"declineRatePctPerDay": round(float(d), 3)}, base_conf, 0.6))

    wct = feats.get("waterCut_trend", np.nan)
    if np.isfinite(wct) and wct >= WATERCUT_TREND_PTS_DAY:
        recs.append(_rec(
            "WC-1", "production", "medium",
            f"Su payı artım tendensiyasındadır (≈{wct*30:.1f} faiz bəndi/30 gün). Su payının monitorinqinin "
            "gücləndirilməsi və səbəblərinin təhlili məsləhətdir.",
            "Son 30 gün üzrə su payının xətti trendi.", {"waterCutTrendPtsPerDay": round(float(wct), 3)}, base_conf, 0.7))

    ta = feats.get("target_attainment_30d", np.nan)
    if np.isfinite(ta) and ta < TARGET_LOW:
        recs.append(_rec(
            "TGT-1", "efficiency", "medium",
            f"30 günlük orta hasilat hədəfin ≈{ta*100:.0f}%-ni təşkil edir. Hədəfdən geri qalma səbəblərinin təhlili məsləhətdir.",
            "30 günlük orta hasilat / productionTarget.", {"targetAttainment30d": round(float(ta), 3)}, base_conf, 0.8))

    chp = (ef.get("efficiencyDetails") or {}).get("changePoints")
    if chp is not None and chp <= EFFICIENCY_DROP_POINTS:
        recs.append(_rec(
            "EFF-1", "efficiency", "medium",
            f"Əməliyyat səmərəliliyi əvvəlki 30 günlə müqayisədə {abs(chp):.1f} faiz bəndi azalıb. "
            f"{(ef['efficiencyDetails'] or {}).get('explanation', '')}",
            "Səmərəlilik KPI-nin iki ardıcıl 30 günlük dövr üzrə müqayisəsi.",
            {"changePoints": chp, "current": ef.get("operationalEfficiency")}, base_conf, 0.8))

    if quality["level"] == "poor" or quality["missingFields"]:
        miss = ", ".join(label(m) for m in quality["missingFields"][:5]) or "bəzi göstəricilər"
        recs.append(_rec(
            "DATA-1", "data_quality", "low" if quality["level"] != "poor" else "medium",
            f"Məlumat tamlığı {quality['completenessPct']:.0f}% təşkil edir (çatışan: {miss}). Daha dəqiq təhlil üçün "
            "həmin göstəricilərin müntəzəm qeydiyyatının təmin edilməsi məsləhətdir.",
            "Son 30 gündə ölçmələrin tamlığı və tarixçənin uzunluğu.",
            {"completenessPct": quality["completenessPct"], "historyDays": quality["historyDays"]}, 1.0, 1.0))

    if not recs:
        recs.append(_rec("OK-1", "monitoring", "low",
                         "Modelə görə hazırda əhəmiyyətli kənarlaşma aşkarlanmayıb. Adi monitorinqin davam etdirilməsi məsləhətdir.",
                         "Anomaliya, risk, nasazlıq və proqnoz göstəriciləri müəyyən edilmiş hədlərdən kənara çıxmayıb.",
                         {}, base_conf, 0.8))
    order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda r: order[r["priority"]])
    return recs

"""Analytique : statistiques pilote, prédictions, comparaisons."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from race_engineer.database import get_pilot_laps, get_relay_events
from race_engineer.utils import (
    parse_lap_time,
    safe_mean,
    safe_median,
    safe_stdev,
    safe_min,
    safe_max,
)


# ---------------------------------------------------------------------------
# Stats pilote
# ---------------------------------------------------------------------------
def compute_pilot_stats(
    numero: str,
    pilot_name: str,
    aliases: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Calcule les stats complètes d'un pilote pour une moto donnée."""
    names = {pilot_name.strip().lower()} if pilot_name else set()
    if aliases:
        names.update(a.strip().lower() for a in aliases if a)

    all_laps = [dict(r) for r in get_pilot_laps(numero=numero)]
    pilot_laps = [
        l for l in all_laps
        if (l.get("pilote") or "").strip().lower() in names
    ] if names else []

    relays = [dict(r) for r in get_relay_events(numero)]

    lap_secs = [l["lap_seconds"] for l in pilot_laps if l.get("lap_seconds") is not None]
    relay_numbers = sorted({l.get("relay_number") for l in pilot_laps if l.get("relay_number")})

    # Relais en cours = max(relay_number observé sur les laps) du pilote
    current_relay_num = max(relay_numbers) if relay_numbers else None
    current_relay_laps = [
        l["lap_seconds"] for l in pilot_laps
        if l.get("relay_number") == current_relay_num and l.get("lap_seconds") is not None
    ]
    prev_relay_num = (current_relay_num - 1) if current_relay_num else None
    last_relay_laps = [
        l["lap_seconds"] for l in pilot_laps
        if l.get("relay_number") == prev_relay_num and l.get("lap_seconds") is not None
    ] if prev_relay_num else []

    # Trend par régression simple sur 10 derniers tours
    last10 = lap_secs[-10:]
    trend = _compute_trend(last10)

    # Dégradation : moyenne 3 premiers vs 3 derniers du relais en cours
    deg_first = safe_mean(current_relay_laps[:3]) if current_relay_laps else None
    deg_last = safe_mean(current_relay_laps[-3:]) if current_relay_laps else None
    degradation = (deg_last - deg_first) if (deg_first and deg_last) else None

    # Régularité = écart-type
    stdev = safe_stdev(lap_secs)
    # Indicateur 0-100 (plus c'est haut, plus c'est régulier)
    regularity_idx = None
    if stdev is not None and lap_secs:
        mean_v = safe_mean(lap_secs)
        if mean_v:
            cv = stdev / mean_v
            regularity_idx = max(0.0, min(100.0, 100.0 - cv * 1000))

    return {
        "pilot": pilot_name,
        "total_laps": len(pilot_laps),
        "total_relays": len(relay_numbers),
        "current_relay": current_relay_num,
        "current_relay_laps_count": len(current_relay_laps),
        "last_relay_laps_count": len(last_relay_laps),
        "avg_laps_per_relay": (
            sum(len([l for l in pilot_laps if l.get("relay_number") == rn]) for rn in relay_numbers)
            / len(relay_numbers)
        ) if relay_numbers else None,
        "longest_relay_laps": max(
            (len([l for l in pilot_laps if l.get("relay_number") == rn]) for rn in relay_numbers),
            default=0,
        ),
        "shortest_relay_laps": min(
            (len([l for l in pilot_laps if l.get("relay_number") == rn]) for rn in relay_numbers),
            default=0,
        ),
        "best_lap": safe_min(lap_secs),
        "mean_lap": safe_mean(lap_secs),
        "median_lap": safe_median(lap_secs),
        "stdev_lap": stdev,
        "best5_mean": safe_mean(sorted(lap_secs)[:5]) if lap_secs else None,
        "last10_mean": safe_mean(last10) if last10 else None,
        "current_relay_mean": safe_mean(current_relay_laps),
        "current_relay_best": safe_min(current_relay_laps),
        "last_relay_mean": safe_mean(last_relay_laps),
        "last_relay_best": safe_min(last_relay_laps),
        "degradation": degradation,
        "deg_first3_mean": deg_first,
        "deg_last3_mean": deg_last,
        "regularity_idx": regularity_idx,
        "trend": trend,
        "raw_lap_secs": lap_secs,
        "raw_current_relay_laps": current_relay_laps,
        "recommendation": _pilot_recommendation(trend, degradation, regularity_idx),
    }


def _compute_trend(values: List[float]) -> str:
    """Tendance simple par régression linéaire."""
    if len(values) < 3:
        return "indéterminé"
    n = len(values)
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(values) / n
    num = sum((xs[i] - mx) * (values[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    if den == 0:
        return "stable"
    slope = num / den
    # Seuils en secondes/tour
    if slope < -0.05:
        return "en progression"
    if slope > 0.10:
        return "en dégradation"
    return "stable"


def _pilot_recommendation(trend: str, degradation: Optional[float], regularity: Optional[float]) -> str:
    if trend == "en progression":
        return "Peut prolonger"
    if trend == "en dégradation" or (degradation is not None and degradation > 1.0):
        return "Rythme en baisse — préparer relève"
    if regularity is not None and regularity < 50:
        return "À surveiller (irrégulier)"
    return "Bon relais"


# ---------------------------------------------------------------------------
# Carburant & prédictions
# ---------------------------------------------------------------------------
def estimate_fuel_status(
    laps_done: int,
    last_pit_laps: int,
    fuel_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Estime carburant restant et pit window."""
    tank = float(fuel_config.get("tank_capacity_l", 24.0))
    conso = float(fuel_config.get("consumption_l_per_lap", 3.2))
    margin = int(fuel_config.get("safety_margin_laps", 1))

    if conso <= 0:
        return {"max_laps_per_stint": None, "laps_remaining": None,
                "fuel_remaining_l": None, "pit_window_open": False}

    max_laps = int(tank / conso)
    laps_remaining = max(0, max_laps - last_pit_laps - margin)
    fuel_remaining = max(0.0, tank - last_pit_laps * conso)
    pit_window_open = last_pit_laps >= (max_laps - margin - 2)

    return {
        "max_laps_per_stint": max_laps,
        "laps_remaining": laps_remaining,
        "fuel_remaining_l": round(fuel_remaining, 2),
        "pit_window_open": pit_window_open,
        "current_stint_laps": last_pit_laps,
    }


# ---------------------------------------------------------------------------
# Comparatif moto vs concurrent
# ---------------------------------------------------------------------------
def build_comparison(
    our_numero: str,
    competitor_numero: str,
) -> Dict[str, Any]:
    """Construit la comparaison relais-par-relais entre notre moto et un concurrent.

    Retourne :
      {
        "rows": [...],
        "totals": {...},
        "best_gain": {...},
        "worst_loss": {...},
      }
    """
    ours = [dict(r) for r in get_relay_events(our_numero)]
    them = [dict(r) for r in get_relay_events(competitor_numero)]

    # Laps détaillés pour calculer la moyenne par relais
    our_laps = [dict(l) for l in get_pilot_laps(numero=our_numero)]
    their_laps = [dict(l) for l in get_pilot_laps(numero=competitor_numero)]

    rows: List[Dict[str, Any]] = []
    cumul = 0.0

    max_relays = max(len(ours), len(them))
    for i in range(max_relays):
        r_ours = ours[i] if i < len(ours) else None
        r_them = them[i] if i < len(them) else None

        relay_num = (r_ours or r_them or {}).get("relais", i + 1)

        tours_o = (r_ours or {}).get("tours_relais") or 0
        tours_t = (r_them or {}).get("tours_relais") or 0

        avg_o = _avg_relay_lap(our_laps, relay_num)
        avg_t = _avg_relay_lap(their_laps, relay_num)

        track_o = (avg_o * tours_o) if (avg_o is not None and tours_o) else None
        track_t = (avg_t * tours_t) if (avg_t is not None and tours_t) else None
        gain_track = (track_t - track_o) if (track_o is not None and track_t is not None) else None

        pit_o = (r_ours or {}).get("last_pit_seconds")
        pit_t = (r_them or {}).get("last_pit_seconds")
        gain_pit = (pit_t - pit_o) if (pit_o is not None and pit_t is not None) else None

        bilan = None
        if gain_track is not None and gain_pit is not None:
            bilan = gain_track + gain_pit
        elif gain_track is not None:
            bilan = gain_track
        elif gain_pit is not None:
            bilan = gain_pit

        if bilan is not None:
            cumul += bilan

        rows.append({
            "relais": relay_num,
            "tours_96": tours_o,
            "tours_conc": tours_t,
            "moy_96": avg_o,
            "moy_conc": avg_t,
            "piste_96": track_o,
            "piste_conc": track_t,
            "gain_piste": gain_track,
            "pit_96": pit_o,
            "pit_conc": pit_t,
            "gain_pit": gain_pit,
            "bilan": bilan,
            "cumul": cumul if bilan is not None else None,
        })

    totals = {
        "gain_piste_total": sum((r["gain_piste"] or 0) for r in rows),
        "gain_pit_total": sum((r["gain_pit"] or 0) for r in rows),
        "bilan_total": cumul,
    }

    bilans_valid = [r for r in rows if r["bilan"] is not None]
    best_gain = max(bilans_valid, key=lambda r: r["bilan"]) if bilans_valid else None
    worst_loss = min(bilans_valid, key=lambda r: r["bilan"]) if bilans_valid else None

    pit_gains_valid = [r for r in rows if r["gain_pit"] is not None]
    best_pit_gain = max(pit_gains_valid, key=lambda r: r["gain_pit"]) if pit_gains_valid else None
    worst_pit = min(pit_gains_valid, key=lambda r: r["gain_pit"]) if pit_gains_valid else None

    return {
        "rows": rows,
        "totals": totals,
        "best_gain_relay": best_gain,
        "worst_loss_relay": worst_loss,
        "best_pit_relay": best_pit_gain,
        "worst_pit_relay": worst_pit,
    }


def _avg_relay_lap(laps: List[Dict[str, Any]], relay_num: int) -> Optional[float]:
    secs = [
        l["lap_seconds"] for l in laps
        if l.get("relay_number") == relay_num and l.get("lap_seconds") is not None
    ]
    return safe_mean(secs)

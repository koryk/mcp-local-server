import base64
from datetime import date, timedelta
from typing import Optional, Dict, Any

from .config import get_connection
from .utils import get_audio_bytes


async def get_bird_detections(
    start_date: str,
    end_date: str,
    species: Optional[str] = None,
) -> Dict[str, Any]:
    with get_connection() as conn:
        if species:
            rows = conn.execute(
                """SELECT Date, Time, Com_Name, Confidence, File_Name
                   FROM detections
                   WHERE Date BETWEEN ? AND ?
                     AND LOWER(Com_Name) LIKE ?
                   ORDER BY Date DESC, Time DESC""",
                (start_date, end_date, f'%{species.lower()}%'),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT Date, Time, Com_Name, Confidence, File_Name
                   FROM detections
                   WHERE Date BETWEEN ? AND ?
                   ORDER BY Date DESC, Time DESC""",
                (start_date, end_date),
            ).fetchall()

    detections = [dict(r) for r in rows]

    if detections:
        confidences = [d['Confidence'] for d in detections]
        stats = {
            "min": min(confidences),
            "max": max(confidences),
            "average": sum(confidences) / len(confidences),
        }
    else:
        stats = {"min": 0.0, "max": 0.0, "average": 0.0}

    return {"detections": detections, "stats": stats, "total": len(detections)}


async def get_detection_stats(
    period: str,
    min_confidence: float = 0.0,
) -> Dict[str, Any]:
    today = date.today()
    period_cutoffs = {
        "day": today - timedelta(days=1),
        "week": today - timedelta(weeks=1),
        "month": today - timedelta(days=30),
        "all": date(2000, 1, 1),
    }
    cutoff_date = period_cutoffs.get(period, date(2000, 1, 1)).isoformat()

    with get_connection() as conn:
        rows = conn.execute(
            """SELECT Com_Name, COUNT(*) as count,
                      MIN(Confidence) as min_conf,
                      MAX(Confidence) as max_conf,
                      AVG(Confidence) as avg_conf
               FROM detections
               WHERE Date >= ? AND Confidence >= ?
               GROUP BY Com_Name
               ORDER BY count DESC""",
            (cutoff_date, min_confidence),
        ).fetchall()

    rows = [dict(r) for r in rows]
    total = sum(r['count'] for r in rows)
    detections_by_species = {r['Com_Name']: r['count'] for r in rows}
    top_species = [{"species": r['Com_Name'], "count": r['count']} for r in rows[:10]]

    if total > 0:
        conf_stats = {
            "min": min(r['min_conf'] for r in rows),
            "max": max(r['max_conf'] for r in rows),
            "average": sum(r['avg_conf'] * r['count'] for r in rows) / total,
        }
    else:
        conf_stats = {"min": 0.0, "max": 0.0, "average": 0.0}

    return {
        "totalDetections": total,
        "uniqueSpecies": len(rows),
        "detectionsBySpecies": detections_by_species,
        "topSpecies": top_species,
        "confidenceStats": conf_stats,
        "periodCovered": period,
        "minConfidence": min_confidence,
    }


async def get_audio_recording(
    filename: str,
    format: str = 'base64',
) -> Dict[str, Any]:
    audio_buffer = get_audio_bytes(filename)
    if format == 'base64':
        return {
            "audio": base64.b64encode(audio_buffer).decode('utf-8'),
            "format": "base64",
        }
    return {"audio": audio_buffer, "format": "buffer"}


async def get_daily_activity(
    date_str: str,
    species: Optional[str] = None,
) -> Dict[str, Any]:
    with get_connection() as conn:
        if species:
            rows = conn.execute(
                """SELECT CAST(SUBSTR(Time, 1, 2) AS INT) as hour, Com_Name, COUNT(*) as count
                   FROM detections
                   WHERE Date = ? AND LOWER(Com_Name) LIKE ?
                   GROUP BY hour, Com_Name""",
                (date_str, f'%{species.lower()}%'),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT CAST(SUBSTR(Time, 1, 2) AS INT) as hour, Com_Name, COUNT(*) as count
                   FROM detections
                   WHERE Date = ?
                   GROUP BY hour, Com_Name""",
                (date_str,),
            ).fetchall()

    rows = [dict(r) for r in rows]
    hourly_activity = [0] * 24
    unique_species = set()
    for row in rows:
        hourly_activity[row['hour']] += row['count']
        unique_species.add(row['Com_Name'])

    total = sum(hourly_activity)
    peak_hour = hourly_activity.index(max(hourly_activity)) if total > 0 else 0

    return {
        "date": date_str,
        "species": species or "all",
        "totalDetections": total,
        "hourlyActivity": hourly_activity,
        "peakHour": peak_hour,
        "uniqueSpecies": len(unique_species),
    }


async def generate_detection_report(
    start_date: str,
    end_date: str,
    format: str = 'json',
) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT Date, Time, Com_Name, Confidence, File_Name
               FROM detections
               WHERE Date BETWEEN ? AND ?
               ORDER BY Date DESC, Time DESC""",
            (start_date, end_date),
        ).fetchall()

    detections = [dict(r) for r in rows]
    by_species: Dict[str, int] = {}
    for d in detections:
        by_species[d['Com_Name']] = by_species.get(d['Com_Name'], 0) + 1

    total = len(detections)
    unique = len(by_species)

    if format == 'html':
        table_rows = ''.join(
            f'<tr><td>{d["Date"]}</td><td>{d["Time"]}</td>'
            f'<td>{d["Com_Name"]}</td><td>{d["Confidence"]:.3f}</td></tr>'
            for d in detections
        )
        html = (
            f'<html><head><title>Bird Detection Report</title></head><body>'
            f'<h1>Bird Detection Report</h1>'
            f'<p>Period: {start_date} to {end_date}</p>'
            f'<h2>Summary</h2>'
            f'<ul><li>Total Detections: {total}</li><li>Unique Species: {unique}</li></ul>'
            f'<table border="1"><tr><th>Date</th><th>Time</th><th>Species</th><th>Confidence</th></tr>'
            f'{table_rows}</table>'
            f'</body></html>'
        )
        return {"report": html, "format": "html"}

    return {
        "report": {
            "period": {"start": start_date, "end": end_date},
            "summary": {"totalDetections": total, "uniqueSpecies": unique, "bySpecies": by_species},
            "detections": detections,
        },
        "format": "json",
    }

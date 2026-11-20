"""Use the first finite TEC measurement in each acquisition as a room reference."""

import csv
import io
import json
import math
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2]


def initial_tec_reference(rows):
    """Return the first finite TEC sample in file order, including passive rows."""
    for row in rows:
        if row.get("event") != "measurement":
            continue
        try:
            value = float(row.get("tec_C", ""))
        except (ValueError, TypeError):
            continue
        if math.isfinite(value):
            return {
                "room_reference_C": value,
                "room_reference_method": "first finite TEC (A0) reading in the acquisition",
                "sample_host_time": row.get("host_time"),
                "sample_device_time_s": float(row["time_s"]),
                "sample_state": row.get("run_state"),
                "sample_signed_pwm": row.get("signed_pwm"),
            }
    raise ValueError("The acquisition contains no finite TEC measurement")


def main():
    references = []
    for path in sorted((MODULE / "data/raw").glob("*.csv")):
        if path.is_symlink():
            continue
        content = path.read_bytes()
        lines = content[:content.rfind(b"\n") + 1].decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(lines)))
        if not any(row.get("run_state") == "RUNNING" for row in rows):
            continue
        references.append({"source": str(path.relative_to(MODULE.parent)), **initial_tec_reference(rows)})
    output = MODULE / "data/processed/m08_initial_tec_room_references.json"
    output.write_text(json.dumps({
        "method": "One reference per recorded acquisition with an active run. Use the first finite TEC reading, including IDLE samples.",
        "limitation": "The reference describes the initial TEC temperature. Independent air temperature and room drift remain unknown.",
        "channel_correction": "Use recorded readings directly. Six-channel common-bath calibration is outside the current analysis scope.",
        "records": references,
    }, indent=2) + "\n")
    print(f"Wrote {len(references)} acquisition references to {output}")


if __name__ == "__main__":
    main()

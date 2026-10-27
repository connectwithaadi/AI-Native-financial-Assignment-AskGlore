
import hashlib
import json
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    """Fingerprint the exact input file contents."""
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest()


def build_audit_metadata(
    input_paths: list[str | Path],
    period: str,
) -> dict:
    """Create reproducibility metadata for a validation run."""
    fingerprints = {
        Path(path).name: sha256_file(path)
        for path in input_paths
    }

    canonical = json.dumps(
        {"period": period, "inputs": fingerprints},
        sort_keys=True,
    ).encode("utf-8")

    run_fingerprint = hashlib.sha256(canonical).hexdigest()

    return {
        "period": period,
        "run_fingerprint": run_fingerprint,
        "input_fingerprints": fingerprints,
        "validation_version": "1.0.0",
    }

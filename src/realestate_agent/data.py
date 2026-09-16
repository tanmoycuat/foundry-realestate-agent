"""Evidence normalization for manual input and future Toolbox providers."""

from __future__ import annotations

from .models import EvidenceBundle, EvidenceItem, PropertyProfile


def manual_evidence(profile: PropertyProfile) -> EvidenceBundle:
    """Build an evidence bundle whose provenance is explicit user input."""
    values = profile.model_dump()
    evidence = [
        EvidenceItem(
            key=f"property.{key}",
            value=value,
            provider="user-input",
            source_tier="user",
            confidence=1.0,
        )
        for key, value in values.items()
        if value is not None
    ]
    return EvidenceBundle(
        property=profile,
        evidence=evidence,
        warnings=["Property facts were supplied by the user and were not independently verified."],
    )

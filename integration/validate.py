"""Validate any stage output against its JSON Schema in contracts/."""
from __future__ import annotations

import json
import pathlib

from jsonschema import Draft202012Validator

CONTRACTS = pathlib.Path(__file__).resolve().parent.parent / "contracts"
_validators: dict[str, Draft202012Validator] = {}


class ContractError(ValueError):
    """Raised when a stage output breaks its contract."""


def validate(instance: dict, name: str) -> dict:
    if name not in _validators:
        schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
        _validators[name] = Draft202012Validator(schema)
    errors = sorted(_validators[name].iter_errors(instance), key=lambda e: [str(p) for p in e.path])
    if errors:
        detail = "; ".join(f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in errors)
        raise ContractError(f"{name} contract broken -> {detail}")
    return instance

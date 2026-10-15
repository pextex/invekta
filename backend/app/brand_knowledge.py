"""Bundled public facts; an explicit admin override (even empty) takes precedence."""
import json
from functools import lru_cache
from pathlib import Path
from .models import AiBrandKnowledge, BusinessUnit


@lru_cache
def defaults() -> dict[str, str]:
    return json.loads(Path(__file__).with_name("brand_knowledge.json").read_text(encoding="utf-8"))


def content_for(unit: BusinessUnit | None, knowledge: AiBrandKnowledge | None) -> str:
    if knowledge is not None:
        return knowledge.content
    return defaults().get(unit.code.upper(), "") if unit else ""

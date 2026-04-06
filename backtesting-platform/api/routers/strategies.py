from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models.schemas import StrategyInfo
from strategies._registry import STRATEGY_REGISTRY

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyInfo])
def list_strategies():
    return [
        StrategyInfo(
            name=cls.metadata.name,
            display_name=cls.metadata.display_name,
            description=cls.metadata.description,
            param_schema=cls.metadata.param_schema,
            default_params=cls.metadata.default_params,
        )
        for cls in STRATEGY_REGISTRY.values()
    ]


@router.get("/{name}", response_model=StrategyInfo)
def get_strategy(name: str):
    cls = STRATEGY_REGISTRY.get(name)
    if not cls:
        raise HTTPException(404, f"Strategy '{name}' not found. Available: {list(STRATEGY_REGISTRY.keys())}")
    return StrategyInfo(
        name=cls.metadata.name,
        display_name=cls.metadata.display_name,
        description=cls.metadata.description,
        param_schema=cls.metadata.param_schema,
        default_params=cls.metadata.default_params,
    )

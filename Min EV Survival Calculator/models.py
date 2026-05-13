# models.py

from dataclasses import dataclass, field
from typing import Optional, Any, List


@dataclass(frozen=True)
class Pokemon:
    name: str
    type_1: str
    type_2: Optional[str]
    base_hp: int
    base_atk: int
    base_def: int
    base_spa: int
    base_spd: int
    abilities: List[str]


@dataclass(frozen=True)
class Move:
    name: str
    type: str
    base_power: int
    accuracy: Optional[int] = None
    hits: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class StatInvestment:
    ev: int = 252
    nature: float = 1.1


@dataclass(frozen=True)
class AttackConfig:
    attacker_name: str
    move_name: str
    stage: int
    ability: Optional[str]
    investment: StatInvestment
    ability_active: Optional[bool] = False
    hidden_power_iv: Optional[int] = None
    hits_per_attack: List[int] = field(default_factory=list)
    item: Optional[str] = None


@dataclass(frozen=True)
class DefenderConfig:
    defender_name: str
    ability: Optional[str] = None
    sandstorm: bool = False
    leftovers: bool = False
    spikes_layers: int = 0
    spikes_mode: str = "switch"
    item: Optional[str] = None
    hp_iv: int = 31
    def_iv: int = 31
    spd_iv: int = 31


@dataclass(frozen=True)
class SurvivalRequest:
    defender: DefenderConfig
    physical: Optional[AttackConfig] = None
    special: Optional[AttackConfig] = None
    physical_structure: Optional[List[List[int]]] = None
    special_structure: Optional[List[List[int]]] = None
    allow_nature: bool = False
    combine_mode: bool = False
    level: Optional[int] = None


@dataclass(frozen=True)
class EVSpread:
    hp_ev: int
    def_ev: int
    spd_ev: int
    nature: str
    total_ev: int

"""Schema snapshot module for capturing database structure at a point in time."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import json


@dataclass
class ColumnSchema:
    name: str
    data_type: str
    nullable: bool
    default: Optional[str] = None
    primary_key: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "nullable": self.nullable,
            "default": self.default,
            "primary_key": self.primary_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ColumnSchema":
        return cls(**data)


@dataclass
class TableSchema:
    name: str
    columns: List[ColumnSchema] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "columns": [col.to_dict() for col in self.columns],
            "indexes": self.indexes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TableSchema":
        columns = [ColumnSchema.from_dict(c) for c in data.get("columns", [])]
        return cls(name=data["name"], columns=columns, indexes=data.get("indexes", []))


@dataclass
class SchemaSnapshot:
    captured_at: datetime
    database: str
    tables: Dict[str, TableSchema] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "captured_at": self.captured_at.isoformat(),
            "database": self.database,
            "tables": {name: table.to_dict() for name, table in self.tables.items()},
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> "SchemaSnapshot":
        tables = {
            name: TableSchema.from_dict(t)
            for name, t in data.get("tables", {}).items()
        }
        return cls(
            captured_at=datetime.fromisoformat(data["captured_at"]),
            database=data["database"],
            tables=tables,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "SchemaSnapshot":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def capture_now(cls, database: str, tables: Dict[str, TableSchema]) -> "SchemaSnapshot":
        return cls(
            captured_at=datetime.now(timezone.utc),
            database=database,
            tables=tables,
        )

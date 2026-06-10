from dataclasses import dataclass, field


@dataclass
class TeamAliasMap:
    aliases: dict[str, str] = field(default_factory=dict)

    def normalize(self, raw_name: str) -> str:
        key = raw_name.strip().casefold()
        return self.aliases.get(key, raw_name.strip())

    def add_alias(self, alias: str, canonical_name: str) -> None:
        self.aliases[alias.strip().casefold()] = canonical_name.strip()

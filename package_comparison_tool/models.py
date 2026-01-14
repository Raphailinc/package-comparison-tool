from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PackageInfo:
    name: str
    epoch: int
    version: str
    release: str
    arch: str
    buildtime: int
    disttag: str

    def to_dict(self, *, branch: str) -> dict[str, Any]:
        return {
            "branch": branch,
            "name": self.name,
            "epoch": self.epoch,
            "version": self.version,
            "release": self.release,
            "arch": self.arch,
            "buildtime": self.buildtime,
            "disttag": self.disttag,
            "url": f"https://packages.altlinux.org/ru/{branch}/binary/{self.name}/{self.arch}/",
        }

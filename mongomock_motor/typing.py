from typing import TypedDict


class BuildInfo(TypedDict):
    ok: float
    version: str
    versionArray: list[int]

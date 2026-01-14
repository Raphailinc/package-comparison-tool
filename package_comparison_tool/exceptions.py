from __future__ import annotations


class AltApiError(RuntimeError):
    pass


class BranchNotFoundError(AltApiError):
    def __init__(self, branch: str):
        super().__init__(f'Branch "{branch}" not found in ALT RDB API.')
        self.branch = branch


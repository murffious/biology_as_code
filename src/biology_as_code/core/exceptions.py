"""Package exceptions."""


class BiologyAsCodeError(Exception):
    """Base error for biology_as_code."""


class PathwayError(BiologyAsCodeError):
    """Pathway graph / registry problems."""


class SimulationError(BiologyAsCodeError):
    """Meal dig / simulation problems."""


class FixtureError(BiologyAsCodeError):
    """Missing or invalid fixture data."""

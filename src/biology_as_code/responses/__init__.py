"""
Response objects — versioned, executable definitions of what a measurement is.

"Glycemic response" names a family of protocols, not a number. Two papers can
both report one and mean different windows, different baselines, different
integration rules and different classification cut-points. A model that
compares them without saying which protocol it used is comparing quantities
that do not share a definition.

A response object closes that gap. It fixes the protocol — sampling schedule,
baseline, integration rule, classification bounds — behind a version string, so
a result can be reported as ``GlycemicResponse/1.0`` and be reproducible from
the identifier alone. Changing any of those choices requires a new version;
they are never edited in place.

Currently executable:

- :class:`~biology_as_code.responses.glycemic.GlycemicResponse` (``1.0``) —
  incremental AUC by the trapezoidal rule, area below baseline discarded.

Declared but not executable (stubs, so that a caller asking for one gets a
directed error rather than a wrong number):

- :class:`~biology_as_code.responses.satiety.SatietyResponse`
- :class:`~biology_as_code.responses.lipemic.LipemicResponse`
"""

from biology_as_code.responses.base import (
    ResponseNotExecutable,
    ResponseProtocol,
    ResponseResult,
    Sample,
)
from biology_as_code.responses.glycemic import (
    GLYCEMIC_RESPONSE_V1,
    GlycemicResponse,
    incremental_auc,
)
from biology_as_code.responses.lipemic import LipemicResponse
from biology_as_code.responses.satiety import SatietyResponse

__all__ = [
    "GLYCEMIC_RESPONSE_V1",
    "GlycemicResponse",
    "LipemicResponse",
    "ResponseNotExecutable",
    "ResponseProtocol",
    "ResponseResult",
    "Sample",
    "SatietyResponse",
    "incremental_auc",
]

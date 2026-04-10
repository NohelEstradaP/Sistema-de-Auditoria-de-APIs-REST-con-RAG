from .unauthenticated_access import UnauthenticatedAccessProbe
from .bola import BOLAProbe
from .mass_assignment import MassAssignmentProbe
from .throttling import ThrottlingProbe
from .function_level_authz import FunctionLevelAuthzProbe

ALL_PROBES = [
    UnauthenticatedAccessProbe,
    BOLAProbe,
    MassAssignmentProbe,
    ThrottlingProbe,
    FunctionLevelAuthzProbe,
]

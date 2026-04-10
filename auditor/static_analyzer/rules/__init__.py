from .debug_enabled import DebugEnabledRule
from .missing_throttling import MissingThrottlingRule
from .missing_jwt_config import MissingJWTConfigRule
from .missing_permission_classes import MissingPermissionClassesRule
from .serializer_sensitive_fields import SerializerSensitiveFieldsRule
from .bola_url_params import BolaUrlParamsRule

ALL_RULES = [
    DebugEnabledRule(),
    MissingThrottlingRule(),
    MissingJWTConfigRule(),
    MissingPermissionClassesRule(),
    SerializerSensitiveFieldsRule(),
    BolaUrlParamsRule(),
]

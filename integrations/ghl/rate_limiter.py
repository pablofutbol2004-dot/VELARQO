"""Re-exported from lib.rate_limiter (moved so integrations/email/ can
share the same implementation). Kept here so existing imports/tests don't
need to change.
"""

from lib.rate_limiter import RateLimiter

__all__ = ["RateLimiter"]

from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponseForbidden, HttpRequest, HttpResponseNotFound
import logging
from django.utils import timezone
from ipaddress import ip_address as _validate_ip, AddressValueError


logger = logging.getLogger(__name__)

class RateLimitOtpRequestMiddleware:

    CACHE_TTL = 86400
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_request = getattr(settings, "OTP_RETRIES_PER_DAY", 3)
        self.restrict_path = set(path.strip("/").lower() 
                                for path in getattr(settings, "RESTRICTED_PATHS",  None))

        self.initial = getattr(settings, "INITIAL_REQUEST", 1)


    def  __call__(self, request, *args, **kwargs):
        if self._is_valid_path(request.path):
            retry_key, _ = self.create_cache_keys(request)

            if retry_key:
                retries = cache.get(retry_key, self.initial)
                if retries >= self.max_request:
                    logger.warning("Maximum request Exceeded for to day, come back tomorrow:")
                    raise HttpResponseForbidden("Maximum request for OTP request Exceeded for today")
            cache.incr(retry_key)
        
        response = self.get_response(request)
        return response
        

    def _is_valid_path(self, path: str) -> bool:
        """ Check if request path is in restricted path """
        return path.strip("/").lower() in self.restrict_path


    def get_remote_ip(self, request):

        """ Retrieve user ip address and return None if not found"""
        try:
            # Try on X_forworded_for
            X_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if X_forwarded_for:
                ip_address = X_forwarded_for.split(",")[0].strip()

            else:
                ip_address = request.META.get("REMOTE_ADDR")

            try:
                _validate_ip(ip_address)
            except AddressValueError as exc:
                logger.error("Error validating ip address %s", exc, exc_info=True)
                return None

            logger.info("Extracted remote address for user")
            return ip_address
        except Exception as exc:
            logger.exception("error occurred while extractin ip_address %s", exc, exc_info=True)
            raise HttpResponseNotFound(content="Ip_address not found")
    
    def create_cache_keys(self, request):
        """ Return user ip address iin cache and store them in cache if not found  """
        user_ip_address = self.get_remote_ip(request)

        if user_ip_address is None:
            return None
    
        max_request_key_in_cache = f"user_{user_ip_address}_retries"
        datetime_key_in_cache = f"user+{user_ip_address}_datetime"

        if not cache.has_key(max_request_key_in_cache):
            cache.set(max_request_key_in_cache, self.initial, timeout=self.CACHE_TTL) # cache data for 24 hours

        if not cache.has_key(datetime_key_in_cache):
            cache.set(datetime_key_in_cache, timezone.now(), timeout=self.CACHE_TTL)
        
        return max_request_key_in_cache, datetime_key_in_cache
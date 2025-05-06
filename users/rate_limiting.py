from functools import wraps
from django.core.cache import cache
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpRequest
import time

def rate_limit(max_requests, timeframe):
    """
    Custom rate limiting decorator for Django views.
    
    Args:
        max_requests (int): Maximum number of requests allowed in the timeframe
        timeframe (int): Time window in seconds
        
    Returns:
        Function: Decorated view function with rate limiting
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view_instance, request, *args, **kwargs):
            # Get client identifier (IP address or user ID if authenticated)
            if request.user.is_authenticated:
                client_id = f"user_{request.user.id}"
            else:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    client_ip = x_forwarded_for.split(',')[0].strip()
                else:
                    client_ip = request.META.get('REMOTE_ADDR')
                client_id = f"ip_{client_ip}"
            
            # Create a unique cache key for this view and client
            view_name = view_instance.__class__.__name__
            cache_key = f"ratelimit_{view_name}_{client_id}"
            
            # Get current request log from cache
            requests_log = cache.get(cache_key)
            current_time = time.time()
            
            if requests_log is None:
                # First request from this client for this view
                requests_log = [current_time]
                cache.set(cache_key, requests_log, timeout=timeframe)
                return view_func(view_instance, request, *args, **kwargs)
            
            # Filter out requests older than timeframe
            requests_log = [t for t in requests_log if current_time - t < timeframe]
            
            # Check if the limit has been exceeded
            if len(requests_log) >= max_requests:
                # Calculate time remaining until next allowed request
                oldest_request = min(requests_log)
                wait_time = int(timeframe - (current_time - oldest_request))
                return Response({
                    "detail": f"Rate limit exceeded. Try again in {wait_time} seconds."
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Add current request to log and update cache
            requests_log.append(current_time)
            cache.set(cache_key, requests_log, timeout=timeframe)
            
            # Call the view function
            return view_func(view_instance, request, *args, **kwargs)
            
        return _wrapped_view
    return decorator

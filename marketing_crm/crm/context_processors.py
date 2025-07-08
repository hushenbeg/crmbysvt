from django.core.cache import cache
from django.conf import settings

from .models import Visitor

def visitor_counter(request):
    # Initialize counter if it doesn't exist
    if not cache.get('total_visitors'):
        cache.set('total_visitors', 0)
    
    # Check if this session has already been counted
    if not request.session.get('has_been_counted'):
        # Increment the counter
        try:
            cache.incr('total_visitors')
        except ValueError:
            cache.set('total_visitors', 1)
        
        # Mark this session as counted
        request.session['has_been_counted'] = True
    
    return {
        'visitor_count': cache.get('total_visitors', 0)
    }

from .models import Visitor

def visitor_counter(request):
    if request.META.get('REMOTE_ADDR'):
        Visitor.add_visitor(request.META['REMOTE_ADDR'])
    return {
        'visitor_count': Visitor.count()
    }
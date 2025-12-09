"""
Backend Modules
API modules for interacting with McTime API
"""

# New snake_case modules (recommended)
from .employee_list import get_employee_list, create_employee_variables
from .mail import get_employee_emails
from .times import get_times
from .user_id import get_user_ids, get_user_id_list

# Legacy UPPERCASE modules (for backward compatibility)
# These will be deprecated in future versions
try:
    from .GET_EMPLOYEE_LIST import get_employee_list as legacy_get_employee_list
    from .GET_MAIL import get_employee_emails as legacy_get_employee_emails
except ImportError:
    pass

__all__ = [
    'get_employee_list',
    'create_employee_variables',
    'get_employee_emails',
    'get_times',
    'get_user_ids',
    'get_user_id_list',
]

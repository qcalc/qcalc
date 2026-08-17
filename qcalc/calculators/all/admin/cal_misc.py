from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from calc import Qty, QCals


def ucount__info():
    return {
        'title': 'Logged in User Count',
        'desc': 'Count and list of users logged in during a period of time',
    }

def ucount(time_period='1d'):
    User = get_user_model()

    # Set your time threshold
    hours = Qty(time_period, 'h').value
    time_threshold = timezone.now() - timedelta(hours=hours)

    # Count users who logged in recently
    users = User.objects.filter(last_login__gte=time_threshold)
    user_list = list(users.values_list('username', flat=True))
    return {
        'logged_in_count': users.count(),
        'list_of_users': ", ".join(user_list)
    }

def symlist__info():
    return {
        'title': 'Symbol List except calculators and units',
    }

def symlist():
    all_symbols = list(QCals.qfunc_dict.keys())
    have__ = [key.split('__')[0] for key in all_symbols if '__' in key]
    not_have__ = [key for key in all_symbols if '__' not in key]
    valid = sorted([key for key in not_have__ if key not in have__])
    return ', '.join(valid)


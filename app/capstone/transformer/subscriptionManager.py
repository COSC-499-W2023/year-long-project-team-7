from .models import Subscription
from datetime import date

def has_valid_subscription(user):
    if hasattr(user, 'subscription'):
        subscription = user.subscription
        return (
            subscription.has_subscription and
            subscription.start_date is not None and
            subscription.end_date is not None and
            subscription.start_date <= date.today() and
            subscription.end_date > date.today()
        )
    return False

def give_subscription_to_user(user, start_date, end_date):
    subscription, created = Subscription.objects.get_or_create(user=user)
    subscription.has_subscription = True
    subscription.start_date = start_date
    subscription.end_date = end_date
    subscription.save()
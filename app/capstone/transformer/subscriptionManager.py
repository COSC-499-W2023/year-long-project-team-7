from .models import Subscription
from datetime import date
from django.contrib.auth.models import User

def has_valid_subscription(user: User): 
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

def give_subscription_to_user(user: User, start_date, end_date): #type: ignore
    subscription, created = Subscription.objects.get_or_create(user=user)
    subscription.has_subscription = True
    subscription.start_date = start_date
    subscription.end_date = end_date
    subscription.save()

def delete_subscription(user: User):
    try:
        subscription = Subscription.objects.get(user=user)
        subscription.delete()
        print(f"Subscription deleted for user {user}")
    except Subscription.DoesNotExist:
        print(f"No subscription found for user {user}")
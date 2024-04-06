from .models import Subscription, Product
from datetime import date
from django.contrib.auth.models import User
from datetime import timedelta


def has_valid_subscription(user_id: int) -> bool:
    try:
        subscription = Subscription.objects.get(user=user_id)
        return (
            subscription.has_subscription
            and subscription.start_date is not None
            and subscription.end_date is not None
            and subscription.start_date <= date.today()
            and subscription.end_date >= date.today()
        )
    except Subscription.DoesNotExist:
        return False


def give_subscription_to_user(
    user: User, start_date: date, end_date: date, product: Product | None
) -> None:
    subscription, created = Subscription.objects.get_or_create(user=user)
    if created:
        subscription.has_subscription = True
        subscription.start_date = start_date
        subscription.end_date = end_date
        if product is not None:
            if product.name == "Premium Subscription":
                subscription.is_premium = True
        subscription.save()
    else:
        old_end = subscription.end_date
        subscription.end_date = old_end + timedelta(days=product.length_days)  # type: ignore
        subscription.save()


def delete_subscription(user: User) -> None:
    try:
        subscription = Subscription.objects.get(user=user)
        subscription.delete()
        print(f"Subscription deleted for user {user}")
    except Subscription.DoesNotExist:
        print(f"No subscription found for user {user}")


def has_premium_subscription(user_id: int) -> bool:
    try:
        subscription = Subscription.objects.get(user=user_id)
        return subscription.is_premium
    except Subscription.DoesNotExist:
        return False

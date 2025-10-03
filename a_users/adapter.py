from django.utils.translation import gettext_lazy as _
from allauth.account.adapter import DefaultAccountAdapter
from .models import Profile


class CustomAccountAdapter(DefaultAccountAdapter):
    def get_user_by_phone(self, phone: str):
        normalized = (phone or "").strip()
        if not normalized:
            return None
        try:
            profile = Profile.objects.get(phone_number=normalized)
        except Profile.DoesNotExist:
            return None
        return profile.user

    def set_phone(self, user, phone: str, verified: bool):
        normalized = (phone or "").strip()
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.phone_number = normalized or None
        profile.save(update_fields=['phone_number'])

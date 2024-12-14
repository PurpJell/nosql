from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import Vartotojas

class MongoEngineBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            vartotojas = Vartotojas.objects.get(django_user_id=str(user.id))
            if vartotojas and vartotojas.check_password(password):
                return user
        except (User.DoesNotExist, Vartotojas.DoesNotExist):
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
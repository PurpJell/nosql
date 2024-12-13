from django.urls import path
from .endpoints import user_view

urlpatterns = [
    path('user/', user_view, name='user_view'),
]

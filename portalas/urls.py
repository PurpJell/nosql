from django.urls import path
from .views import register_view, login_view, logout_view, profile_view, update_profile_view

urlpatterns = [
    path('user/register/', register_view, name='register_view'),
    path('user/login/', login_view, name='login_view'),
    path('user/logout/', logout_view, name='logout_view'),
    path('user/profile/', profile_view, name='profile_view'),
    path('user/profile/update/', update_profile_view, name='update_profile_view'),
]

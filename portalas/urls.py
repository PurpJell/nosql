from django.urls import path
from .views import index_view, register_view, login_view, logout_view, profile_view, update_profile_view, skelbimai_view, skelbimu_kategorijos_view, update_kategorija_view, skelbimai_view, update_skelbimas_view, konkretus_skelbimas_view, skelbimo_busena_view, vartotojo_skelbimai_view

urlpatterns = [
    path('', index_view, name='index_view'),
    path('user/register/', register_view, name='register_view'),
    path('user/login/', login_view, name='login_view'),
    path('user/logout/', logout_view, name='logout_view'),
    path('user/profile/', profile_view, name='profile_view'),
    path('user/profile/update/', update_profile_view, name='update_profile_view'),
    path('skelbimai/', skelbimai_view, name='skelbimai_view'),
    path('skelbimai/kategorijos/', skelbimu_kategorijos_view, name='skelbimu_kategorijos_view'),
    path('skelbimai/kategorijos/update/', update_kategorija_view, name='update_kategorija_view'),
    path('skelbimai/', skelbimai_view, name='skelbimai_view'),
    path('skelbimai/update/', update_skelbimas_view, name='update_skelbimas_view'),
    path('skelbimai/skelbimas/', konkretus_skelbimas_view, name='konkretus_skelbimas_view'),
    path('skelbimai/skelbimas/busena/', skelbimo_busena_view, name='skelbimo_busena_view'),
    path('user/skelbimai/', vartotojo_skelbimai_view, name='vartotojo_skelbimai_view'),
]

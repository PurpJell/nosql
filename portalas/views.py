from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('vartotojo_vardas', 'vardas', 'pavarde', 'el_pastas', 'telefono_numeris', 'vaidmuo')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('vartotojo_vardas', 'vardas', 'pavarde', 'el_pastas', 'telefono_numeris', 'vaidmuo')

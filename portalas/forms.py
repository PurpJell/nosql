from django import forms
from .models import Vartotojas
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User


class RegisterForm(forms.Form):
    vartotojo_vardas = forms.CharField(max_length=100, required=True, label='Vartotojo Vardas')
    vardas = forms.CharField(max_length=100, required=True, label='Vardas')
    pavarde = forms.CharField(max_length=100, required=True, label='Pavardė')
    slaptazodis = forms.CharField(widget=forms.PasswordInput(), required=True, label='Slaptažodis')
    patvirtinti_slaptazodi = forms.CharField(widget=forms.PasswordInput(), required=True, label='Patvirtinti Slaptažodį')
    el_pastas = forms.EmailField(required=True, label='El. Paštas')
    telefono_numeris = forms.CharField(max_length=15, required=True, label='Telefono Numeris')

    def clean(self):
        cleaned_data = super().clean()
        slaptazodis = cleaned_data.get("slaptazodis")
        patvirtinti_slaptazodi = cleaned_data.get("patvirtinti_slaptazodi")

        if slaptazodis and patvirtinti_slaptazodi and slaptazodis != patvirtinti_slaptazodi:
            self.add_error('patvirtinti_slaptazodi', "Slaptažodžiai nesutampa")

        return cleaned_data

    def save(self):
        data = self.cleaned_data
        hashed_password = make_password(data['slaptazodis'])

        user = User.objects.create_user(
            username=data['vartotojo_vardas'],
            password=hashed_password,
            email=data['el_pastas'],
            first_name=data['vardas'],
            last_name=data['pavarde']
        )

        print(user.id)

        vartotojas = Vartotojas(
            django_user_id=str(user.id),
            vartotojo_vardas=data['vartotojo_vardas'],
            vardas=data['vardas'],
            pavarde=data['pavarde'],
            slaptazodis=hashed_password,
            el_pastas=data['el_pastas'],
            telefono_numeris=data['telefono_numeris'],
            vaidmuo='vartotojas'
        )
        vartotojas.save()

        if not vartotojas:
            user.delete()

        return vartotojas
    

class LoginForm(forms.Form):
    vartotojo_vardas = forms.CharField(max_length=100, required=True, label='Vartotojo Vardas')
    slaptazodis = forms.CharField(widget=forms.PasswordInput(), required=True, label='Slaptažodis')
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    

class UpdateProfileForm(forms.Form):
    vartotojo_vardas = forms.CharField(max_length=100, required=False, label='Vartotojo Vardas')
    vardas = forms.CharField(max_length=100, required=False, label='Vardas')
    pavarde = forms.CharField(max_length=100, required=False, label='Pavarde')
    slaptazodis = forms.CharField(widget=forms.PasswordInput(), required=False, label='Naujas Slaptazodis')
    el_pastas = forms.EmailField(required=False, label='El. Pastas')
    telefono_numeris = forms.CharField(max_length=15, required=False, label='Telefono Numeris')

    def save(self, vartotojas):
        data = self.cleaned_data
        user = User.objects.get(id=vartotojas.django_user_id)

        if data.get('vartotojo_vardas'):
            user.username = data['vartotojo_vardas']
            vartotojas.vartotojo_vardas = data['vartotojo_vardas']

        if data.get('el_pastas'):
            user.email = data['el_pastas']
            vartotojas.el_pastas = data['el_pastas']

        if data.get('vardas'):
            user.first_name = data['vardas']
            vartotojas.vardas = data['vardas']

        if data.get('pavarde'):
            user.last_name = data['pavarde']
            vartotojas.pavarde = data['pavarde']

        if data.get('slaptazodis'):
            user.set_password(data['slaptazodis'])
            vartotojas.slaptazodis = make_password(data['slaptazodis'])

        if data.get('telefono_numeris'):
            vartotojas.telefono_numeris = data['telefono_numeris']

        user.save()
        vartotojas.save()
        return vartotojas
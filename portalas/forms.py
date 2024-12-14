from django import forms
from .models import Vartotojas, Skelbimas, Skelbimu_kategorija, Paveikslelis
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from datetime import datetime
import pytz


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
    

class SkelbimuKategorijaForm(forms.Form):
    pavadinimas = forms.CharField(max_length=100, required=True, label='Pavadinimas')
    lapas = forms.BooleanField(required=False, label='Lapas')
    
    def save(self, kurejas, kategorijos_id=None, motinine_kategorija=None):

        if kategorijos_id:
            kategorija = Skelbimu_kategorija.objects.get(id=kategorijos_id)
            if self.cleaned_data['pavadinimas']:
                kategorija.pavadinimas = self.cleaned_data['pavadinimas']
            kategorija.lapas = self.cleaned_data.get('lapas', False)
            kategorija.sukurimo_data = datetime.now(pytz.timezone('Europe/Vilnius'))
            kategorija.kurejas = kurejas
            kategorija.motinine_kategorija = motinine_kategorija
            kategorija.save()
            return kategorija
        else:
            kategorija = Skelbimu_kategorija(
                pavadinimas=self.cleaned_data['pavadinimas'],
                motinine_kategorija=motinine_kategorija,
                kurejas=kurejas,
                lapas=self.cleaned_data.get('lapas', False),
            )
            kategorija.save()
            return kategorija
    
    

class SkelbimasForm(forms.Form):
    pavadinimas = forms.CharField(max_length=100, required=True, label='Pavadinimas')
    aprasymas = forms.CharField(max_length=2000, required=True, label='Aprasymas')
    kaina = forms.DecimalField(min_value=0, required=True, label='Kaina')
    paveiksleliai = forms.FileField(required=False, label='Paveiksleliai')
    kategorija = forms.ChoiceField(choices=[], required=True, label='Kategorija')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kategorija'].choices = [(str(kategorija.id), kategorija.pavadinimas) for kategorija in Skelbimu_kategorija.objects.all()]
    
    def save(self, kurejas, skelbimo_id=None):
        data = self.cleaned_data
        paveiksleliai = data.get('paveiksleliai')
        kategorija = Skelbimu_kategorija.objects.get(id=data['kategorija'])

        if skelbimo_id:
            skelbimas = Skelbimas.objects.get(id=skelbimo_id)
            skelbimas.pavadinimas = data['pavadinimas']
            skelbimas.aprasymas = data['aprasymas']
            skelbimas.kaina = data['kaina']
            skelbimas.kategorija = kategorija
            skelbimas.atnaujinimo_data = datetime.now(pytz.timezone('Europe/Vilnius'))
        else:
            skelbimas = Skelbimas(
                pavadinimas=data['pavadinimas'],
                aprasymas=data['aprasymas'],
                kaina=data['kaina'],
                kategorija=kategorija,
                kurejas=kurejas
            )
        skelbimas.save()
        
        if paveiksleliai:
            for paveikslelis in paveiksleliai:
                paveikslelis_obj = Paveikslelis(paveikslelis=paveikslelis)
                paveikslelis_obj.save()
                skelbimas.paveiksleliai.append(paveikslelis_obj)
        
        skelbimas.save()
        return skelbimas
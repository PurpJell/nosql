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
    vartotojo_vardas = forms.CharField(max_length=100, required=True, label='Vartotojo Vardas')
    vardas = forms.CharField(max_length=100, required=True, label='Vardas')
    pavarde = forms.CharField(max_length=100, required=True, label='Pavardė')
    slaptazodis = forms.CharField(widget=forms.PasswordInput(), required=True, label='Naujas Slaptažodis')
    el_pastas = forms.EmailField(required=True, label='El. Paštas')
    telefono_numeris = forms.CharField(max_length=15, required=True, label='Telefono Numeris')

    def save(self, vartotojas):
        data = self.cleaned_data
        user = User.objects.get(id=vartotojas.django_user_id)

        user.username = data['vartotojo_vardas']
        vartotojas.vartotojo_vardas = data['vartotojo_vardas']

        user.email = data['el_pastas']
        vartotojas.el_pastas = data['el_pastas']

        user.first_name = data['vardas']
        vartotojas.vardas = data['vardas']

        user.last_name = data['pavarde']
        vartotojas.pavarde = data['pavarde']

        user.set_password(data['slaptazodis'])
        vartotojas.slaptazodis = make_password(data['slaptazodis'])

        vartotojas.telefono_numeris = data['telefono_numeris']

        user.save()
        vartotojas.save()
        return vartotojas
    

class SkelbimuKategorijaForm(forms.Form):
    pavadinimas = forms.CharField(max_length=100, required=True, label='Pavadinimas')
    aprasymas = forms.CharField(max_length=2000, required=False, label='Aprašymas')
    lapas = forms.ChoiceField(required=True, label='Lapas')
    motinine_kategorija = forms.ChoiceField(choices=[], required=False, label='Motininė Kategorija')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motinine_kategorija'].choices = [('', 'Pasirinkite Motininę Kategorija')] + [(str(kategorija.id), kategorija.pavadinimas) for kategorija in Skelbimu_kategorija.objects.filter(lapas=False)]
        self.fields['lapas'].choices = [(True, 'Taip'), (False, 'Ne')]
    
    def save(self, kurejas, kategorijos_id=None):

        motinine_kategorija_id = self.cleaned_data.get('motinine_kategorija')
        motinine_kategorija = Skelbimu_kategorija.objects.get(id=motinine_kategorija_id) if motinine_kategorija_id else None
        lapas = True if self.cleaned_data['lapas'] == 'True' else False

        if kategorijos_id: # jei kategorija jau egzistuoja
            kategorija = Skelbimu_kategorija.objects.get(id=kategorijos_id)
            kategorija.pavadinimas = self.cleaned_data['pavadinimas']
            kategorija.aprasymas = self.cleaned_data['aprasymas']
            kategorija.lapas = lapas
            kategorija.sukurimo_data = datetime.now(pytz.timezone('Europe/Vilnius'))
            kategorija.kurejas = kurejas
            kategorija.motinine_kategorija = motinine_kategorija
            kategorija.save()
            return kategorija
        else: # jei kategorija neegzistuoja
            kategorija = Skelbimu_kategorija(
                pavadinimas=self.cleaned_data['pavadinimas'],
                motinine_kategorija=motinine_kategorija,
                kurejas=kurejas,
                lapas=lapas,
            )
            kategorija.save()
            return kategorija
    
    

class SkelbimasForm(forms.Form):
    pavadinimas = forms.CharField(max_length=100, required=True, label='Pavadinimas')
    aprasymas = forms.CharField(max_length=2000, required=True, label='Aprašymas')
    kaina = forms.DecimalField(min_value=0, required=True, label='Kaina')
    paveiksleliai = forms.FileField(required=False, label='Paveikslėliai', widget=forms.ClearableFileInput(attrs={'multiple': True}))
    kategorija = forms.ChoiceField(choices=[], required=True, label='Kategorija')
    galiojimo_laikas = forms.DateTimeField(
        required=True,
        label='Galiojimo Laikas',
        widget=forms.DateTimeInput(attrs={'placeholder': '2024-01-25 14:30'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kategorija'].choices = [(str(kategorija.id), kategorija.pavadinimas) for kategorija in Skelbimu_kategorija.objects.filter(lapas=True)]
    
    def save(self, kurejas, skelbimo_id=None):
        data = self.cleaned_data
        paveiksleliai = self.files.getlist('paveiksleliai')
        kategorija = Skelbimu_kategorija.objects.get(id=data['kategorija'])

        if skelbimo_id:
            skelbimas = Skelbimas.objects.get(id=skelbimo_id)
            skelbimas.pavadinimas = data['pavadinimas']
            skelbimas.aprasymas = data['aprasymas']
            skelbimas.kaina = data['kaina']
            skelbimas.kategorija = kategorija
            skelbimas.atnaujinimo_data = datetime.now(pytz.timezone('Europe/Vilnius'))
            skelbimas.galiojimo_laikas = data['galiojimo_laikas']
        else:
            skelbimas = Skelbimas(
                pavadinimas=data['pavadinimas'],
                aprasymas=data['aprasymas'],
                kaina=data['kaina'],
                kategorija=kategorija,
                kurejas=kurejas,
                galiojimo_laikas=data['galiojimo_laikas']
            )
        skelbimas.save()
        
        if paveiksleliai:
            print("There are images")
            for paveikslelis in paveiksleliai:
                paveikslelis_obj = Paveikslelis(paveikslelis=paveikslelis, skelbimas=skelbimas)
                paveikslelis_obj.save()
                skelbimas.paveiksleliai.append(paveikslelis_obj)
        
        skelbimas.save()
        return skelbimas
    

class SkelbimuFiltrasForm(forms.Form):
    kategorija = forms.ChoiceField(choices=[], required=False, label='Kategorija')
    atnaujinimo_data_nuo = forms.DateTimeField(required=False, label='Atnaujinimo Data Nuo')
    kurejas = forms.CharField(max_length=100, required=False, label='Kurėjo vartotojo vardas')
    pavadinimas = forms.CharField(max_length=100, required=False, label='Pavadinimas')
    kaina_nuo = forms.DecimalField(min_value=0, required=False, label='Kaina Nuo')
    kaina_iki = forms.DecimalField(min_value=0, required=False, label='Kaina Iki')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kategorija'].choices = [('', 'Pasirinkite Kategorija')] + [(str(kategorija.id), kategorija.pavadinimas) for kategorija in Skelbimu_kategorija.objects.filter(lapas=True)]
    
    def get_query(self):
        query = {}
        data = self.cleaned_data
        
        if data.get('kategorija'):
            query['kategorija'] = data['kategorija']

        if data.get('atnaujinimo_data_nuo'):
            query['atnaujinimo_data__gte'] = data['atnaujinimo_data_nuo']

        if data.get('kurejas'):
            query['kurejas'] = data['kurejas']
        
        if data.get('pavadinimas'):
            query['pavadinimas__icontains'] = data['pavadinimas']
        
        if data.get('kaina_nuo'):
            query['kaina__gte'] = data['kaina_nuo']
        
        if data.get('kaina_iki'):
            query['kaina__lte'] = data['kaina_iki']
        
        return query
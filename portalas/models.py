from mongoengine import Document, StringField, DecimalField, DateTimeField, ReferenceField, ListField, FileField, EmailField, BooleanField
from datetime import datetime, timedelta
import pytz
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User


class Vartotojas(Document):
    django_user_id = StringField(index=True)
    vartotojo_vardas = StringField(max_length=100, unique=True, required=True)
    vardas = StringField(max_length=100, required=True)
    pavarde = StringField(max_length=100, required=True)
    slaptazodis = StringField(max_length=100, required=True)
    el_pastas = EmailField(max_length=100, unique=True, required=True)
    telefono_numeris = StringField(max_length=15, unique=True, required=True)
    vaidmuo = StringField(max_length=50, required=True, index=True)

    meta = {
        'collection': 'vartotojai'
    }

    def set_password(self, raw_password):
        self.slaptazodis = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.slaptazodis)

    def __str__(self):
        return self.vartotojo_vardas


class Paveikslelis(Document):
    paveikslelis = FileField()
    skelbimas = ReferenceField('Skelbimas', required=True, index=True)

    meta = {
        'collection': 'paveiksleliai'
    }

    def __str__(self):
        return str(self.id)
    

class Skelbimas(Document):
    pavadinimas = StringField(max_length=100, required=True, index=True)
    aprasymas = StringField(max_lengt=2000, required=True)
    kaina = DecimalField(min_value=0, precision=2, required=True, index=True)
    kategorija = ReferenceField('Skelbimu_kategorija', required=True, index=True)
    galiojimo_laikas = DateTimeField(required=True, index=True)
    busena = StringField(max_length=100, default='aktyvus', index=True)
    klientas = ReferenceField(Vartotojas, default=None, index=True)
    sukurimo_data = DateTimeField(default=lambda: datetime.now(pytz.timezone('Europe/Vilnius')), index=True)
    atnaujinimo_data = DateTimeField(default=lambda: datetime.now(pytz.timezone('Europe/Vilnius')), index=True)
    kurejas = ReferenceField(Vartotojas, required=True, index=True)

    meta = {
        'collection': 'skelbimai'
    }

    def cascade_delete(self):
        for paveikslelis in Paveikslelis.objects(skelbimas=self):
            paveikslelis.delete()
        self.delete()

    def __str__(self):
        return self.pavadinimas
    

class Skelbimu_kategorija(Document):
    pavadinimas = StringField(max_length=100, unique=True, required=True, index=True)
    kurejas = ReferenceField(Vartotojas, required=True, index=True)
    aprasymas = StringField(max_length=2000)
    sukurimo_data = DateTimeField(default=lambda: datetime.now(pytz.timezone('Europe/Vilnius')), index=True)
    motinine_kategorija = ReferenceField('self', default=None)
    lapas =  BooleanField(default=False)

    def cascade_delete(self):
        for skelbimas in Skelbimas.objects(kategorija=self):
            skelbimas.cascade_delete()
        for subcategory in Skelbimu_kategorija.objects(motinine_kategorija=self):
            subcategory.cascade_delete()
        self.delete()

    meta = {
        'collection': 'skelbimu_kategorijos'
    }

    def __str__(self):
        return self.pavadinimas
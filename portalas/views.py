from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, LoginForm, UpdateProfileForm, SkelbimuKategorijaForm, SkelbimasForm, SkelbimuFiltrasForm
from .models import Vartotojas, Skelbimu_kategorija, Skelbimas, Paveikslelis
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from bson import ObjectId
from mongoengine.errors import DoesNotExist
from datetime import datetime
import pytz

@require_http_methods(["GET"])
def index_view(request):
    return render(request, 'index.html')


@require_http_methods(["GET","POST"])
def register_view(request):
    # user/register/
    if request.method == "GET":
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})
    elif request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            vartotojas = form.save()
            user_id = vartotojas.django_user_id
            print(user_id)
            return render(request, 'index.html')
        else:
            return render(request, 'register.html', {'form': form})


@require_http_methods(["GET","POST"])
def login_view(request):
    # user/login/
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'login.html', {'form': form})
    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['vartotojo_vardas']
            password = form.cleaned_data['slaptazodis']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return render(request, 'index.html')
            else:
                form.add_error(None, "Invalid username or password")
        return HttpResponseRedirect(reverse('login_view'))
    

@require_http_methods(["GET"])
def logout_view(request):
    # user/logout/
    logout(request)
    return render(request, 'index.html')


@require_http_methods(["GET","DELETE"])
def profile_view(request):
    # user/profile/
    if not request.user.is_authenticated:
        form = LoginForm()
        return HttpResponseRedirect(reverse('login_view'))
    
    if request.method == "GET":
        vartotojas = Vartotojas.objects.get(django_user_id=str(request.user.id))
        return render(request, 'profile.html', {'user': request.user, 'vartotojas': vartotojas})
    
    elif request.method == "DELETE":
        user = request.user
        vartotojas = Vartotojas.objects.get(django_user_id=str(user.id))
        # delete all posts by user
        vartotojas.delete()
        user.delete()
        return render(request, 'index.html')
    
@require_http_methods(["GET", "POST"])
def update_profile_view(request):
    # user/profile/update/
    if not request.user.is_authenticated:
        form = LoginForm()
        return HttpResponseRedirect(reverse('login_view'))
    
    vartotojas = Vartotojas.objects.get(django_user_id=str(request.user.id))

    if request.method == "GET":
        form = UpdateProfileForm(initial={
            'vartotojo_vardas': vartotojas.vartotojo_vardas,
            'vardas': vartotojas.vardas,
            'pavarde': vartotojas.pavarde,
            'el_pastas': vartotojas.el_pastas,
            'telefono_numeris': vartotojas.telefono_numeris
            }
        )
        return render(request, 'update_profile.html', {'form': form})
    
    elif request.method == "POST":
        form = UpdateProfileForm(request.POST)
        if form.is_valid():
            vartotojas = form.save(vartotojas)
            return HttpResponseRedirect(reverse('login_view'))
        else:
            return render(request, 'update_profile.html', {'form': form})
        

@require_http_methods(["GET"])
def skelbimu_kategorijos_view(request):
    # skelbimai/kategorijos/?parent=x

    if request.method == "GET":
        print(request.GET)
        if request.GET.get('parent') and request.GET.get('parent') != 'None' and request.GET.get('parent') != '':
            parent = Skelbimu_kategorija.objects.get(id=request.GET.get('parent'))
        else:
            parent = None

        kategorijos = Skelbimu_kategorija.objects.filter(motinine_kategorija=parent)
        return render(request, 'skelbimu_kategorijos.html', {'kategorijos': kategorijos, 'parent': parent})
    
    
@require_http_methods(["GET", "POST", "DELETE"])
def update_kategorija_view(request):
    # skelbimai/kategorijos/update/?kategorija=x?parent=x
    if not request.user.is_authenticated:
        form = LoginForm()
        return HttpResponseRedirect(reverse('login_view')) 
    
    vartotojas = Vartotojas.objects.get(django_user_id=str(request.user.id))
    if vartotojas.vaidmuo != 'administratorius':
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == "GET":
        if request.GET.get('kategorija'): # update existing category
            kategorija = Skelbimu_kategorija.objects.get(id=request.GET.get('kategorija'))
            form = SkelbimuKategorijaForm(initial={
                'pavadinimas': kategorija.pavadinimas,
                'aprasymas': kategorija.aprasymas,
                'lapas': kategorija.lapas,
                'motinine_kategorija': str(kategorija.motinine_kategorija.id) if kategorija.motinine_kategorija else None
            })
        else : # create new category
            kategorija = None
            form = SkelbimuKategorijaForm()

        if request.GET.get('parent'):
            parent = Skelbimu_kategorija.objects.get(id=request.GET.get('parent'))
        else:
            parent = None
        
        return render(request, 'valdyti_skelbimu_kategorija.html', {'form': form, 'kategorija': kategorija, 'parent': parent})
    
    elif request.method == "POST":

        form = SkelbimuKategorijaForm(request.POST)
        if request.POST.get('kategorija'):
            kategorija = Skelbimu_kategorija.objects.get(id=request.POST.get('kategorija'))
            kategorijos_id = kategorija.id
        else: # create new category
            kategorija = None
            kategorijos_id = None
        if request.POST.get('parent'):
            parent = Skelbimu_kategorija.objects.get(id=request.POST.get('parent'))
            parent_id = parent.id
        else:
            parent = None
            parent_id = None

        if form.is_valid():
            kurejas = vartotojas

            kategorija = form.save(kurejas=kurejas, kategorijos_id=kategorijos_id)

            return HttpResponseRedirect(reverse('skelbimu_kategorijos_view') + f'?parent={parent_id}')
        else:
            return render(request, 'valdyti_skelbimu_kategorija.html', {'form': form, 'kategorija': kategorija, 'parent': parent})
        
    elif request.method == "DELETE":
        kategorija = Skelbimu_kategorija.objects.get(id=request.GET.get('kategorija'))
        
        def cascade_delete(kategorija):
            for k in Skelbimu_kategorija.objects.filter(motinine_kategorija=kategorija):
                cascade_delete(k)
                # delete all posts in category
                k.delete()
            kategorija.delete()

        cascade_delete(kategorija)
        return render(request, 'skelbimu_kategorijos.html', {'parent': request.GET.get('parent')})

    

@require_http_methods(["GET", "POST"])
def skelbimai_view(request):
    # skelbimai/kategorija=x?atnaujinimo_data=x?kurejas=x?kaina_max=x?kaina_min=x?busena=x
    if request.method == "GET":

        if request.GET.get('kategorija'):
            kategorija = Skelbimu_kategorija.objects.get(id=request.GET.get('kategorija'))
            skelbimai = Skelbimas.objects.filter(kategorija=kategorija)
            skelbimai = skelbimai.filter(busena='aktyvus')
            skelbimai = skelbimai.filter(galiojimo_laikas__gte=datetime.now(pytz.timezone('Europe/Vilnius')))
        else:
            kategorija = None
            skelbimai = Skelbimas.objects.filter(busena='aktyvus')
            skelbimai = skelbimai.filter(galiojimo_laikas__gte=datetime.now(pytz.timezone('Europe/Vilnius')))

        form = SkelbimuFiltrasForm(initial = {
            'kategorija': request.GET.get('kategorija'),
            'atnaujinimo_data_nuo': request.GET.get('atnaujinimo_data'),
            'kurejas': request.GET.get('kurejas'),
            'kaina_nuo': request.GET.get('kaina_min'),
            'kaina_iki': request.GET.get('kaina_max'),
        })
        return render(request, 'skelbimai.html', {'form': form, 'skelbimai': skelbimai, 'kategorija': kategorija})

    elif request.method == "POST":

        def get_filtered_skelbimai(params):
            query = {}
            
            kategorijos_id = params.get('kategorija')
            if kategorijos_id:
                query['kategorija'] = ObjectId(kategorijos_id)
            
            atnaujinimo_data = params.get('atnaujinimo_data__gte')
            if atnaujinimo_data:
                query['atnaujinimo_data__gte'] = atnaujinimo_data
            
            kurejo_vartotojo_vardas = params.get('kurejas')
            if kurejo_vartotojo_vardas:
                try:
                    kurejo_vartotojas = Vartotojas.objects.get(vartotojo_vardas=str(kurejo_vartotojo_vardas))
                    query['kurejas'] = kurejo_vartotojas.id
                except DoesNotExist:
                    return Skelbimas.objects.none()

            pavadinimas = params.get('pavadinimas__icontains')
            if pavadinimas:
                query['pavadinimas__icontains'] = pavadinimas
            
            kaina_max = params.get('kaina__lte')
            if kaina_max:
                query['kaina__lte'] = kaina_max
            
            kaina_min = params.get('kaina__gte')
            if kaina_min:
                query['kaina__gte'] = kaina_min
            
            query['busena'] = 'aktyvus'

            query['galiojimo_laikas__gte'] = datetime.now(pytz.timezone('Europe/Vilnius'))
            
            skelbimai = Skelbimas.objects.filter(**query)
            return skelbimai
        
        form = SkelbimuFiltrasForm(request.POST)
        
        if form.is_valid():
            query_params = form.get_query()
        
            skelbimai = get_filtered_skelbimai(query_params)

            if query_params.get('kategorija'):
                kategorija = Skelbimu_kategorija.objects.get(id=query_params.get('kategorija'))
            else:
                kategorija = None

            return render(request, 'skelbimai.html', {'form': form, 'skelbimai': skelbimai, 'kategorija': kategorija})
        else:
            return render(request, 'skelbimai.html', {'form': form})
    

@require_http_methods(["GET", "POST", "DELETE"])
def update_skelbimas_view(request):
    # skelbimai/update/?skelbimas=x
    if not request.user.is_authenticated:
        form = LoginForm()
        return HttpResponseRedirect(reverse('login_view'))
    
    if request.method == "GET":
        if request.GET.get('skelbimas'):
            skelbimas = Skelbimas.objects.get(id=request.GET.get('skelbimas'))
            form = SkelbimasForm(initial={
                'pavadinimas': skelbimas.pavadinimas,
                'aprasymas': skelbimas.aprasymas,
                'kaina': skelbimas.kaina,
                'kategorija': str(skelbimas.kategorija.id),
                'galiojimo_laikas': skelbimas.galiojimo_laikas,
            })
        else:
            skelbimas = None
            form = SkelbimasForm()

        return render(request, 'valdyti_skelbima.html', {'form': form, 'skelbimas': skelbimas})
    
    elif request.method == "POST":
        form = SkelbimasForm(request.POST, request.FILES)

        if request.POST.get('skelbimas'):
            skelbimas = Skelbimas.objects.get(id=request.POST.get('skelbimas'))
            skelbimo_id = skelbimas.id
        else:
            skelbimas = None
            skelbimo_id = None

        if form.is_valid():
            vartotojas = Vartotojas.objects.get(django_user_id=str(request.user.id))
            skelbimas = form.save(vartotojas, skelbimo_id)

            return HttpResponseRedirect(reverse('skelbimai_view') + f'?kategorija={skelbimas.kategorija.id}')
        else:
            return render(request, 'valdyti_skelbima.html', {'form': form, 'skelbimas': skelbimas})

    elif request.method == "DELETE":
        skelbimas_id = request.GET.get('skelbimas')
        if skelbimas_id:
            try:
                skelbimas = Skelbimas.objects.get(id=skelbimas_id)
                kategorija = skelbimas.kategorija

                def cascade_delete(skelbimas):
                    for p in Paveikslelis.objects.filter(skelbimas=skelbimas):
                        p.delete()
                    skelbimas.delete()

                cascade_delete(skelbimas)
                return JsonResponse({'success': True, 'redirect_url': reverse('skelbimai_view') + f'?kategorija={kategorija.id}'})
            except Skelbimas.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Skelbimas not found'}, status=404)
        else:
            return JsonResponse({'success': False, 'error': 'No skelbimas ID provided'}, status=400)
    

@require_http_methods(["GET"])
def konkretus_skelbimas_view(request):
    # skelbimai/skelbimas/?skelbimas=x
    skelbimas = Skelbimas.objects.get(id=request.GET.get('skelbimas'))
    lankytojas = Vartotojas.objects.get(django_user_id=str(request.user.id))
    return render(request, 'konkretus_skelbimas.html', {'skelbimas': skelbimas, 'lankytojas': lankytojas})


@require_http_methods(["GET"])
def skelbimo_busena_view(request):
    # skelbimai/skelbimas/busena/?skelbimas=x?busena=x

    if request.method == "GET":

        skelbimas = Skelbimas.objects.get(id=request.GET.get('skelbimas'))
        busena = request.GET.get('busena')

        klientas = Vartotojas.objects.get(django_user_id=str(request.user.id))

        if busena == 'aktyvus':
            skelbimas.busena = 'aktyvus'
            skelbimas.klientas = None
        elif busena == 'rezervuotas':
            skelbimas.busena = 'rezervuotas'
            skelbimas.klientas = klientas
        elif busena == 'parduotas':
            skelbimas.busena = 'parduotas'
            skelbimas.klientas = klientas
        else:
            return JsonResponse({'error': 'Invalid busena'}, status=400)

        skelbimas = skelbimas.save()
        return render(request, 'konkretus_skelbimas.html', {'skelbimas': skelbimas, 'lankytojas': klientas})
    

@require_http_methods(["GET"])
def vartotojo_skelbimai_view(request):
    # user/skelbimai/?transakcija=x
    vartotojas = Vartotojas.objects.get(django_user_id=str(request.user.id))

    transakcija = request.GET.get('transakcija')

    if transakcija == 'pardavimai':
        skelbimai = Skelbimas.objects.filter(kurejas=vartotojas)
    elif transakcija == 'pirkimai':
        skelbimai = Skelbimas.objects.filter(klientas=vartotojas)
    return render(request, 'vartotojo_skelbimai.html', {'skelbimai': skelbimai, 'vartotojas': vartotojas, 'transakcija': transakcija})

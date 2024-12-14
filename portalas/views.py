from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, LoginForm, UpdateProfileForm, SkelbimuKategorijaForm, SkelbimasForm
from .models import Vartotojas, Skelbimu_kategorija, Skelbimas
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse

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
        return render(request, 'login.html', {'form': form})
    

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
        return render(request, 'login.html', {'form': form})
    
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
        return render(request, 'login.html', {'form': form})
    
    if request.method == "GET":
        form = UpdateProfileForm()
        return render(request, 'update_profile.html', {'form': form})
    elif request.method == "POST":
        vartotojas = Vartotojas.objects.get(django_user_id=str(request.user.id))
        form = UpdateProfileForm(request.POST)
        if form.is_valid():
            vartotojas = form.save(vartotojas)
            return render(request, 'index.html')
        else:
            return render(request, 'update_profile.html', {'form': form})
        

@require_http_methods(["GET"])
def skelbimu_kategorijos_view(request):
    # skelbimai/kategorijos/?parent=x

    if request.method == "GET":
        if request.GET.get('parent') != 'None' and request.GET.get('parent') != '':
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
        return render(request, 'login.html', {'form': form}) 
    
    vartotojas = Vartotojas.objects.get(django_user_id=str(request.user.id))
    if vartotojas.vaidmuo != 'administratorius':
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == "GET":

        if request.GET.get('kategorija'): # update existing category
            kategorija = Skelbimu_kategorija.objects.get(id=request.GET.get('kategorija'))
        else : # create new category
            kategorija = None

        if request.GET.get('parent'):
            parent = Skelbimu_kategorija.objects.get(id=request.GET.get('parent'))
        else:
            parent = None
        
        form = SkelbimuKategorijaForm()
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

            kategorija = form.save(kurejas=kurejas, kategorijos_id=kategorijos_id, motinine_kategorija=parent_id)

            return HttpResponseRedirect(reverse('skelbimu_kategorijos_view') + f'?parent={parent_id}')
        else:
            return render(request, 'valdyti_skelbimu_kategorija.html', {'form': form, 'kategorija': kategorija, 'parent': parent})
        
    elif request.method == "DELETE":
        print(request.GET.get('kategorija'))
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
            skelbimai = Skelbimas.objects.filter(kategorija=kategorija.id)
        else:
            skelbimai = Skelbimas.objects.all()
            kategorija = None

        return render(request, 'skelbimai.html', {'skelbimai': skelbimai, 'kategorija': kategorija})
    elif request.method == "POST":
        form = SkelbimasForm(request.POST)
        return render(request, 'index.html')
    

@require_http_methods(["GET", "POST", "DELETE"])
def update_skelbimas_view(request):
    # skelbimai/update/?skelbimas=x
    if not request.user.is_authenticated:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})
    
    if request.method == "GET":
        form = SkelbimasForm()

        if request.GET.get('skelbimas'):
            skelbimas = Skelbimas.objects.get(id=request.GET.get('skelbimas'))
        else:
            skelbimas = None

        return render(request, 'valdyti_skelbima.html', {'form': form, 'skelbimas': skelbimas})
    
    elif request.method == "POST":
        form = SkelbimasForm(request.POST)

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

    elif request.method == "DELETE":
        return render(request, 'index.html')
    

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

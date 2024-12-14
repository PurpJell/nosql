from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .forms import RegisterForm, LoginForm, UpdateProfileForm
from .models import Vartotojas
from django.http import JsonResponse


@require_http_methods(["GET","POST"])
def register_view(request):
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
    logout(request)
    return render(request, 'index.html')


@require_http_methods(["GET","DELETE"])
def profile_view(request):
    if not request.user.is_authenticated:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})
    
    if request.method == "GET":
        return render(request, 'profile.html', {'user': request.user})
    
    elif request.method == "DELETE":
        user = request.user
        vartotojas = Vartotojas.objects.get(django_user_id=str(user.id))
        vartotojas.delete()
        user.delete()
        return render(request, 'index.html')
    
@require_http_methods(["GET", "POST"])
def update_profile_view(request):
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
    
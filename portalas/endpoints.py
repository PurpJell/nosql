from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from portalas.models import Vartotojas
import json

@require_http_methods(["GET","POST"])
def user_view(request):
    if request.method == "POST":
        return add_user(request)
    elif request.method == "GET":
        return get_users(request)

def add_user(request):
    try:
        data = json.loads(request.body)
        vartotojas = Vartotojas(
            vartotojo_vardas=data['vartotojo_vardas'],
            vardas=data['vardas'],
            pavarde=data['pavarde'],
            el_pastas=data['el_pastas'],
            telefono_numeris=data['telefono_numeris'],
            vaidmuo=data['vaidmuo']
        )
        vartotojas.save()
        return JsonResponse({'message': 'Vartotojas created successfully'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
def get_users(request):
    try:
        vartotojai = Vartotojas.objects.all()
        return JsonResponse({'vartotojai': json.loads(vartotojai.to_json())}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
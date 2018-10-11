from django.http import HttpResponse, JsonResponse
from legislators.legislators import Legislators


def index(request):
    return HttpResponse("Hello, world. You're at the legislators index testing.")


def geocode(request):
    legis = Legislators()
    return JsonResponse(legis.geocode('122 E Patrick St, Frederick, MD 21701'))


def google_civic_api(request):
    legis = Legislators()
    return JsonResponse({'data': legis.google_civic_api('122 E Patrick St, Frederick, MD 21701')})


def lookup_openstates(request):
    legis = Legislators()
    return JsonResponse({'data': legis.lookup_openstates(39.4137, -77.4079)})


def lookup_balt_data(request):
    legis = Legislators()
    return JsonResponse({'data': legis.lookup_balt_data(39.3096, -76.6402)})


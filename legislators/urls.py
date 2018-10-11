from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('geocode/', views.geocode, name='geocode'),
    path('google-civic/', views.google_civic_api, name='google_civic_api'),
    path('lookup-openstates/', views.lookup_openstates, name='lookup_openstates'),
    path('lookup-balt/', views.lookup_balt_data, name='lookup_balt_data')
]
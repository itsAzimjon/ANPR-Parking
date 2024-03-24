from django.urls import path

from cars.views import CarList, Detail, Latest, check_for_updates

urlpatterns = [
    path('', Latest.as_view(), name='latest'),
    path('all/', CarList.as_view(), name='list'),
    path('<uuid:pk>/', Detail.as_view(), name='detail'),
    path('check_for_updates/', check_for_updates, name='check_for_updates'),
]

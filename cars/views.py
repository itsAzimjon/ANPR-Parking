from datetime import timedelta

from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView
from cars.models import Car
from cars.forms import CheckForm
from cars.utils import ser_command, print_check
from django.http import JsonResponse


class Latest(View):
    def get(self, req):
        from cars.utils import start_video_processing_threads
        start_video_processing_threads()
        try:
            latest_car = Car.objects.latest('finish_time')

            return render(req, 'latest.html', {
                'car': latest_car,
                'edit': latest_car.active,
                'form': CheckForm(dynamic_value=latest_car.id)
            })
        except Exception as e:
            return render(req, 'latest.html', {
                'car': None,
                'edit': None,
                'form': None
            })

    def post(self, req):
        form = CheckForm(req.POST)
        if form.is_valid():
            if req.POST.get('action') == 'up':
                print('up')
                # ser_command('CHIQISH')
            if req.POST.get('action') == 'ok':
                hidden_value = req.POST.get('hidden_field')
                car = Car.objects.get(id=hidden_value)
                car.active = False
                car.save()
                print_check(car)
            elif req.POST.get('action') == 'cancel':
                hidden_value = req.POST.get('hidden_field')
                car = Car.objects.get(id=hidden_value)
                car.active = False
                car.price = 0.0
                car.save()
                # ser_command('CHIQISH')

        return redirect('latest')


class Detail(View):
    def get(self, req, pk):
        from cars.utils import start_video_processing_threads
        start_video_processing_threads()
        car = None if not Car.objects.exists() else Car.objects.get(pk=pk)
        return render(req, 'detail.html', {'car': car})


class CarList(ListView):
    model = Car
    context_object_name = 'cars'
    template_name = 'list.html'

    def get_queryset(self):
        from cars.utils import start_video_processing_threads
        start_video_processing_threads()
        one_day_ago = timezone.now() - timedelta(days=1)
        queryset = Car.objects.filter(create_time__gte=one_day_ago).order_by('-create_time')
        return queryset


def check_for_updates(request):
    try:
        latest_car = Car.objects.latest('finish_time')
        response_data = {
            'id': latest_car.id,
            'active': latest_car.active,
        }
    except Car.DoesNotExist:
        response_data = {
            'id': None,
            'active': None,
        }

    return JsonResponse(response_data)


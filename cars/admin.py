from django.contrib import admin

from cars.models import Car


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['number', 'create_time']
    list_filter = []
    date_hierarchy = 'create_time'
    search_fields = ['number']
    ordering = ['create_time']

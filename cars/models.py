import uuid
from datetime import timedelta

from django.db import models


class Car(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4(), editable=False)
    number = models.CharField(max_length=8)
    plate_image = models.ImageField(upload_to='plate_images')
    create_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(null=True, blank=True)
    price = models.FloatField(default=0)
    active = models.BooleanField(default=True)
    been = models.CharField(max_length=10)

    def duration(self):
        if self.finish_time:
            time_difference = self.finish_time - self.create_time
            if time_difference > timedelta(minutes=15):
                hours, remainder = divmod(time_difference.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.price = 4000 + hours * 2000
                self.been = "{}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))
                return self.been
        self.active = False
        return '_'

    def save(self, *args, **kwargs):
        if self.finish_time and self.active:
            self.duration()
        super().save(*args, **kwargs)

    @classmethod
    def get_latest_car(cls):
        latest_car = cls.objects.order_by('-finish_time', '-create_time').first()

        return latest_car



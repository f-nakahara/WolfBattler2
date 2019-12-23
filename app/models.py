from django.db import models

# Create your models here.


class Player(models.Model):
    name = models.CharField(max_length=20, unique=True)
    room_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=20, unique=True)
    game = models.BooleanField(default=False)
    num = models.IntegerField(default=0)

    def __str__(self):
        return self.name

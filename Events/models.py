import enum
from django.db import models
from django.db.models.aggregates import Count
from random import randint


# Create your models here.


class RandomItemManager(models.Manager):
    def random(self):
        count = self.aggregate(count=Count('id'))['count']
        random_index = randint(0, count - 1)
        return self.all()[random_index]


class Event(models.Model):
    date = models.DateTimeField(verbose_name='Дата')
    title = models.CharField(max_length=255, verbose_name='Название События')

    @enum.unique
    class EventType(models.TextChoices):
        PLANETARIUM = 'Планетарий', 'Планетарий',
        SPECTACLE = 'Спектакли', 'Спектакли',
        CONCERTS = 'Концерты', 'Концерты'
        FESTIVALS = 'Фестивали', 'Фестивали'
        SPORTS = 'Спорт', 'Спорт',
        CHILD = 'Детям', 'Детям',
        SHOW = 'Шоу', 'Шоу'
        HUMOR = 'Юмор', 'Юмор',
        CINEMA = 'Кино', 'Кино',
        OTHERS = 'Другое', 'Другое'

    event_type = models.CharField(max_length=255, verbose_name='Тип События', choices=EventType.choices)
    # Цена специально хранится в Char, для вывода строки по типу "от 100 грн"
    price = models.CharField(blank=True, max_length=255, verbose_name='Цена', null=True)
    location = models.CharField(blank=True, max_length=255, verbose_name='Адрес', null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='logo', verbose_name='Изображение')
    ticket_link = models.CharField(blank=True, null=True, max_length=255, verbose_name='Ссылка на покупку')
    event_link = models.CharField(blank=True, null=True, max_length=255, verbose_name='Ссылка на объявление')
    objects = models.Manager()
    rand_manager = RandomItemManager()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

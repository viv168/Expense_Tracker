from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User
# Create your models here.
class UserIncome(models.Model):
    amount = models.FloatField()
    date = models.DateField(default=now)
    description = models.TextField()
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)
    source = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.source

    class Meta:
        ordering = ['-date']

class Source(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class TotalIncome(models.Model):
    source = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='incomes')

    def __str__(self):
        return f'{self.source} - {self.amount} - {self.owner}'
# myapp/admin.py
from django.contrib import admin
from .models import UserTransaction, UserWallet

# Простейшая регистрация модели:
admin.site.register(UserTransaction)
admin.site.register(UserWallet)
from django.contrib import admin
from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='income'),
    path('add-income', views.add_income, name='add-income'),
    path('edit-income/<int:id>', views.edit_income, name='edit-income'),
    path('delete-income/<int:id>', views.delete_income, name='delete-income'),
    path('search-income', csrf_exempt(views.search_income), name='search_income'),
    path('income-source-summary', views.income_source_summary, name='income-source-summary'),
    path('stats', views.stats_view, name='income-stats'),
    path('export-csv', views.export_csv, name='income-export-csv'),
]
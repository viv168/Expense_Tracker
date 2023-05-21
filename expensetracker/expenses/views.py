from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Category, Expense, TotalExpense
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
from userpreferences.models import UserPreference
import datetime
import csv
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
# Create your views here.

@receiver(post_save, sender=Expense)
def update_total_expense(sender, instance, **kwargs):
    category = instance.category
    amount = int(instance.amount)
    owner = instance.owner
    try:
        total_expense = TotalExpense.objects.get(category=category, owner=owner)
        current_total = int(total_expense.amount)
        total_expense.amount = current_total + amount
        total_expense.save()
    except TotalExpense.DoesNotExist:
        TotalExpense.objects.create(category=category, amount=amount, owner=owner)

@receiver(pre_save, sender=Expense)
def check_expense_limit(sender, instance, **kwargs):
    today = datetime.datetime.now().date()
    count = Expense.objects.filter(owner=instance.owner, date=today).count()
    if count > 10:
        raise ValueError('Maximum number of expenses reached for today')

def search_expenses(request):
    if request.method == 'POST':
        search_str = json.loads(request.body).get('searchText')
        expenses = Expense.objects.filter(amount__istartswith=search_str, owner=request.user) | Expense.objects.filter(date__istartswith=search_str, owner=request.user) | Expense.objects.filter(description__icontains=search_str, owner=request.user) | Expense.objects.filter(category__icontains=search_str, owner=request.user)
        data = expenses.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    expenses = Expense.objects.filter(owner = request.user)
    paginator = Paginator(expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    if UserPreference.objects.filter(user= request.user).exists():
        currency = UserPreference.objects.get(user= request.user).currency
    else:
        currency = 'INR'
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency
    }
    return render(request, "expenses/index.html",context)

@login_required(login_url='/authentication/login')
def add_expense(request):
    
    categories = Category.objects.all()
    context = {
        'categories': categories
    }

    if request.method == 'GET':
        return render(request, "expenses/add_expense.html", context)
    
    if request.method == 'POST':
        amount = request.POST['amount']
        if float(amount) <= 0:
            messages.error(request, 'Expense amount must be greater than zero')
            return render(request, "expenses/add_expense.html", context)
        
        description = request.POST['description']
        category = request.POST['category']
        date = request.POST['expense_date']
        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "expenses/add_expense.html", context)
        
        if not description:
            messages.error(request, "Description is required")
            return render(request, "expenses/add_expense.html", context)

        Expense.objects.create(owner=request.user, amount=amount, category=category, description=description, date=date)
        messages.success(request, 'Expense saved successfully.')
        
        return redirect('expenses')

@login_required(login_url='/authentication/login')
def edit_expense(request, id):
    expense = Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'categories': categories
    }
    if request.method == 'GET':        
        return render(request, 'expenses/edit-expense.html', context)
    if request.method == 'POST':
        amount = request.POST['amount']
        description = request.POST['description']
        category = request.POST['category']
        date = request.POST['expense_date']
        if not amount:
            messages.error(request, "Amount is required")
            return render(request, "expenses/edit-expense.html", context)
        
        if not description:
            messages.error(request, "Description is required")
            return render(request, "expenses/edit-expense.htmll", context)

        expense.owner = request.user
        expense.amount = amount
        expense.description = description
        expense.category = category
        expense.date = date

        expense.save()
        messages.success(request, 'Expense updated successfully.')

        return redirect('expenses')


def delete_expense(request, id):
    expense = Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense removed.')
    return redirect('expenses')


def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago = todays_date - datetime.timedelta(days= 30*6)
    expenses = Expense.objects.filter(owner = request.user, date__gte = six_months_ago, date__lte = todays_date)
    
    finalrep = {}
    def get_category(expense):
        return expense.category

    def get_expense_category_amount(category):
        amount = 0
        filtered_by_category = expenses.filter(category = category)
        for item in filtered_by_category:
            amount += item.amount
        return amount

    category_list = list(set(map(get_category, expenses)))

    for expense in expenses:
        for category in category_list:
            finalrep[category] = get_expense_category_amount(category)

    return JsonResponse({'expense_category_data': finalrep}, safe= False)

def stats_view(request):
    total_expenses= TotalExpense.objects.filter(owner = request.user)
    paginator = Paginator(total_expenses, 5)
    page_number = request.GET.get('page')
    page_obj = Paginator.get_page(paginator, page_number)
    if UserPreference.objects.filter(user= request.user).exists():
        currency = UserPreference.objects.get(user= request.user).currency
    else:
        currency = 'INR'
    context = {
        'total_expenses': total_expenses,
        'page_obj': page_obj,
        'currency': currency
    }
    return render(request, 'expenses/stats.html', context)

def export_csv(request):
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=Expenses'+str(datetime.datetime.now())+'.csv'
    writer = csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])

    expenses = Expense.objects.filter(owner =request.user)
    for expense in expenses:
        writer.writerow([expense.amount, expense.description, expense.category, expense.date])

    return response
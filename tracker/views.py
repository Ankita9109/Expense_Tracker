from django.shortcuts import render, redirect, get_object_or_404
from .models import Expense, Category
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import date
import json


#  Login
def user_login(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user:
            login(request, user)
            return redirect('home')

    return render(request, 'login.html')


#  Logout
def user_logout(request):
    logout(request)
    return redirect('login')


#  Home (Dashboard)
@login_required
def home(request):
    expenses = Expense.objects.filter(user=request.user)

    # Date Filter
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')

    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])

    # Budget Alert
    total = sum(exp.amount for exp in expenses)
    budget = 2000
    alert = "⚠️ Budget Exceeded!" if total > budget else None

    # Pie Chart (Category-wise)
    category_data = expenses.values('category__name').annotate(total=Sum('amount'))

    labels = [item['category__name'] for item in category_data]
    values = [float(item['total']) for item in category_data]

    #  Bar Chart (Monthly)
    monthly_data = (
        expenses
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    months = [item['month'].strftime('%b') for item in monthly_data]
    totals = [float(item['total']) for item in monthly_data]

    context = {
        'expenses': expenses,
        'labels': json.dumps(labels),
        'values': json.dumps(values),
        'months': json.dumps(months),
        'totals': json.dumps(totals),
        'alert': alert,
    }

    return render(request, 'home.html', context)


#  Add Expense
@login_required
def add_expense(request):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=request.POST.get('category'))

        Expense.objects.create(
            user=request.user,
            category=category,
            amount=request.POST.get('amount'),
            description=request.POST.get('description'),
            date=date.today()
        )

        return redirect('home')

    return render(request, 'add_expense.html', {
        'categories': Category.objects.all()
    })


# Edit Expense
@login_required
def edit_expense(request, id):
    expense = get_object_or_404(Expense, id=id)

    if request.method == 'POST':
        expense.amount = request.POST.get('amount')
        expense.description = request.POST.get('description')
        expense.save()
        return redirect('home')

    return render(request, 'edit.html', {'expense': expense})


#  Delete Expense
@login_required
def delete_expense(request, id):
    expense = get_object_or_404(Expense, id=id)
    expense.delete()
    return redirect('home')
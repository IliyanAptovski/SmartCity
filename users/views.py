from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import View, UpdateView, DetailView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from .models import User, UserProfile, Notification
from .forms import (
    UserRegistrationForm, 
    UserLoginForm, 
    UserProfileForm,
    UserUpdateForm,
    PasswordChangeForm
)


class RegisterView(View):
    """View for user registration."""
    
    template_name = 'users/register.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                # Create user profile
                UserProfile.objects.create(user=user)
                # Create welcome notification
                Notification.objects.create(
                    user=user,
                    title=_('Добре дошли в Smart City!'),
                    message=_('Благодарим ви за регистрацията. Сега можете да подавате сигнали и да следите статуса им.'),
                    notification_type='success'
                )
            
            login(request, user)
            messages.success(request, _('Регистрацията е успешна! Добре дошли!'))
            return redirect('dashboard:index')
        
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    """View for user login."""
    
    template_name = 'users/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me', False)
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                
                # Set session expiry based on remember_me
                if not remember_me:
                    request.session.set_expiry(0)
                
                messages.success(request, _('Влязохте успешно!'))
                
                # Redirect to next URL if provided
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard:index')
            else:
                messages.error(request, _('Невалиден имейл или парола.'))
        
        return render(request, self.template_name, {'form': form})


@login_required
def logout_view(request):
    """View for user logout."""
    logout(request)
    messages.success(request, _('Излязохте успешно!'))
    return redirect('users:login')


@login_required
def profile_view(request):
    """View for user profile."""
    user = request.user
    notifications = user.notifications.all()[:10]
    reports_count = user.reports.count() if hasattr(user, 'reports') else 0
    
    context = {
        'user': user,
        'notifications': notifications,
        'reports_count': reports_count,
        'unread_notifications': user.notifications.filter(is_read=False).count(),
    }
    return render(request, 'users/profile.html', context)


@login_required
def profile_edit_view(request):
    """View for editing user profile."""
    user = request.user
    
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Профилът е обновен успешно!'))
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'users/profile_edit.html', context)


@login_required
def change_password_view(request):
    """View for changing password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            current_password = form.cleaned_data.get('current_password')
            new_password = form.cleaned_data.get('new_password')
            
            user = request.user
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                messages.success(request, _('Паролата е променена успешно! Моля, влезте отново.'))
                return redirect('users:login')
            else:
                messages.error(request, _('Текущата парола е грешна.'))
    else:
        form = PasswordChangeForm()
    
    return render(request, 'users/change_password.html', {'form': form})


@login_required
def notifications_view(request):
    """View for all notifications."""
    notifications = request.user.notifications.all()
    return render(request, 'users/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    return redirect('users:notifications')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, _('Всички известия са маркирани като прочетени.'))
    return redirect('users:notifications')


@login_required
def delete_notification(request, pk):
    """Delete a notification."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    messages.success(request, _('Известието е изтрито.'))
    return redirect('users:notifications')

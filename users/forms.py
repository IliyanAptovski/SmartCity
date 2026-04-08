from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Име'
        }),
        label=_('Име')
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Фамилия'
        }),
        label=_('Фамилия')
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        }),
        label=_('Имейл')
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Парола'
        }),
        label=_('Парола')
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Потвърдете паролата'
        }),
        label=_('Потвърдете паролата')
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+359 888 123 456'
        }),
        label=_('Телефон')
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Този имейл адрес вече е регистриран.'))
        return email


class UserLoginForm(AuthenticationForm):
    """Form for user login."""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        }),
        label=_('Имейл')
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Парола'
        }),
        label=_('Парола')
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('Запомни ме')
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile."""
    
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Име')
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Фамилия')
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Телефон')
    )
    email_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Имейл известия')
    )
    sms_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('SMS известия')
    )
    push_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Push известия')
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'phone',
            'address', 'city', 'postal_code', 'avatar', 'bio',
            'latitude', 'longitude'
        ]
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'address': _('Адрес'),
            'city': _('Град'),
            'postal_code': _('Пощенски код'),
            'avatar': _('Аватар'),
            'bio': _('Биография'),
            'latitude': _('Географска ширина'),
            'longitude': _('Географска дължина'),
        }


class UserUpdateForm(forms.ModelForm):
    """Form for updating user basic information."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'email_notifications', 'sms_notifications', 'push_notifications']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'first_name': _('Име'),
            'last_name': _('Фамилия'),
            'phone': _('Телефон'),
            'email_notifications': _('Имейл известия'),
            'sms_notifications': _('SMS известия'),
            'push_notifications': _('Push известия'),
        }


class PasswordChangeForm(forms.Form):
    """Form for changing password."""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Текуща парола'
        }),
        label=_('Текуща парола')
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Нова парола'
        }),
        label=_('Нова парола')
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Потвърдете новата парола'
        }),
        label=_('Потвърдете новата парола')
    )
    
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError(_('Паролите не съвпадат.'))
        
        return cleaned_data

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Report, ReportComment


class ReportForm(forms.ModelForm):
    """Form for submitting a new report."""
    
    # For anonymous users
    reporter_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Вашето име (незадължително)'
        }),
        label=_('Име')
    )
    reporter_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        }),
        label=_('Имейл за връзка')
    )
    reporter_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+359 888 123 456'
        }),
        label=_('Телефон за връзка')
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Кратко описание на проблема'
        }),
        label=_('Заглавие')
    )
    
    category = forms.ChoiceField(
        choices=Report.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Категория')
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Опишете подробно проблема...'
        }),
        label=_('Описание')
    )
    
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ул. Примерна 123, София'
        }),
        label=_('Адрес')
    )
    
    district = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Район'
        }),
        label=_('Район')
    )
    
    latitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(),
    )
    
    longitude = forms.DecimalField(
        required=False,
        widget=forms.HiddenInput(),
    )
    
    image = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label=_('Снимка')
    )
    
    class Meta:
        model = Report
        fields = [
            'reporter_name', 'reporter_email', 'reporter_phone',
            'title', 'category', 'description',
            'address', 'district', 'latitude', 'longitude',
            'image'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that at least one contact method is provided for anonymous users
        reporter_email = cleaned_data.get('reporter_email')
        reporter_phone = cleaned_data.get('reporter_phone')
        
        # This validation will be checked in the view based on user authentication
        return cleaned_data


class ReportUpdateForm(forms.ModelForm):
    """Form for updating report details (staff only)."""
    
    class Meta:
        model = Report
        fields = ['status', 'priority', 'assigned_to', 'notes', 'estimated_start', 'estimated_end']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'estimated_start': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'estimated_end': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
        }
        labels = {
            'status': _('Статус'),
            'priority': _('Приоритет'),
            'assigned_to': _('Възложен на'),
            'notes': _('Вътрешни бележки'),
            'estimated_start': _('Прогнозно начало'),
            'estimated_end': _('Прогнозен край'),
        }


class ReportCommentForm(forms.ModelForm):
    """Form for adding comments to reports."""
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Добавете коментар...'
        }),
        label=_('Коментар')
    )
    
    is_internal = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Вътрешен коментар')
    )
    
    class Meta:
        model = ReportComment
        fields = ['content', 'is_internal']


class ReportSearchForm(forms.Form):
    """Form for searching reports."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Търсене по ключова дума...'
        }),
        label=_('Търсене')
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', _('Всички'))] + list(Report.CATEGORY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Категория')
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', _('Всички'))] + list(Report.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Статус')
    )
    
    district = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Район'
        }),
        label=_('Район')
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('От дата')
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('До дата')
    )

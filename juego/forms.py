from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from .models import Personaje, Clase


class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class EditarAvatarForm(forms.ModelForm):
    class Meta:
        model = Personaje
        fields = ['avatar']
        labels = {
            'avatar': 'Avatar del personaje',
        }
        widgets = {
            'avatar': forms.Select(attrs={'class': 'form-select'}),
        }


class PerfilPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ProfesorEditarAlumnoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Nombre de usuario (acceso)',
            'first_name': 'Nombre',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ProfesorEditarPersonajeForm(forms.ModelForm):
    class Meta:
        model = Personaje
        fields = ['clase', 'avatar']
        labels = {
            'clase': 'Clase asignada',
            'avatar': 'Avatar',
        }
        widgets = {
            'clase': forms.Select(attrs={'class': 'form-select'}),
            'avatar': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, profesor=None, **kwargs):
        super().__init__(*args, **kwargs)
        if profesor and not profesor.is_superuser:
            self.fields['clase'].queryset = Clase.objects.filter(profesor=profesor)


class ProfesorResetPasswordForm(SetPasswordForm):
    """Permite al profesor fijar una nueva contraseña al alumno sin conocer la antigua."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
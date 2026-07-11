from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from .models import User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmação de senha', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'nome', 'tipo_usuario')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('As senhas não conferem.')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        label='Senha',
        help_text='O hash da senha não é exibido. Use o formulário de troca de '
                  'senha (link acima) para alterá-la.',
    )

    class Meta:
        model = User
        fields = (
            'email', 'password', 'nome', 'tipo_usuario', 'bio', 'avatar_url',
            'perfil_publico', 'steam_id',
        )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'nome', 'tipo_usuario', 'perfil_publico', 'created_at')
    list_filter = ('tipo_usuario', 'perfil_publico')
    search_fields = ('email', 'nome')
    ordering = ('id',)
    filter_horizontal = ()
    readonly_fields = ('last_login', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Perfil', {'fields': ('nome', 'bio', 'avatar_url', 'perfil_publico', 'steam_id')}),
        ('Acesso', {'fields': ('tipo_usuario',)}),
        ('Datas', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nome', 'tipo_usuario', 'password1', 'password2'),
        }),
    )

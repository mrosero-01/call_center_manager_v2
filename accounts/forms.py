from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from clients.models import Client


class ManagedUserCreateForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nombre",
        required=False,
    )
    last_name = forms.CharField(
        label="Apellido",
        required=False,
    )
    email = forms.EmailField(
        label="Email",
        required=False,
    )
    client = forms.ModelChoiceField(
        label="Cliente",
        queryset=Client.objects.none(),
        empty_label="Selecciona un cliente",
        error_messages={
            "required": "Selecciona un cliente para este usuario.",
            "invalid_choice": "Selecciona un cliente válido.",
        },
    )
    is_active = forms.BooleanField(
        label="Usuario activo",
        required=False,
        initial=True,
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "client",
            "is_active",
            "password1",
            "password2",
        )
        labels = {
            "username": "Usuario",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = Client.objects.filter(
            is_active=True,
        ).order_by("name")
        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
                "placeholder": "Ej: mgarcia",
            }
        )
        self.fields["first_name"].widget.attrs.update(
            {
                "autocomplete": "given-name",
                "placeholder": "Nombre",
            }
        )
        self.fields["last_name"].widget.attrs.update(
            {
                "autocomplete": "family-name",
                "placeholder": "Apellido",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "autocomplete": "email",
                "placeholder": "correo@empresa.com",
            }
        )
        self.fields["client"].widget.attrs.update(
            {
                "data-client-select": "",
            }
        )
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Confirmar contraseña"
        self.fields["password1"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "Mínimo 8 caracteres",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "Repite la contraseña",
            }
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(
            self.cleaned_data["password1"],
        )
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()

        return user


class ManagedUserUpdateForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        label="Cliente",
        queryset=Client.objects.none(),
        empty_label="Selecciona un cliente",
        error_messages={
            "required": "Selecciona un cliente para este usuario.",
            "invalid_choice": "Selecciona un cliente válido.",
        },
    )

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "client",
            "is_active",
        )
        labels = {
            "username": "Usuario",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Email",
            "is_active": "Usuario activo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = Client.objects.filter(
            is_active=True,
        ).order_by("name")
        self.fields["username"].widget.attrs.update(
            {
                "autocomplete": "username",
            }
        )
        self.fields["first_name"].widget.attrs.update(
            {
                "autocomplete": "given-name",
            }
        )
        self.fields["last_name"].widget.attrs.update(
            {
                "autocomplete": "family-name",
            }
        )
        self.fields["email"].widget.attrs.update(
            {
                "autocomplete": "email",
            }
        )
        self.fields["client"].widget.attrs.update(
            {
                "data-client-select": "",
            }
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()

        return user


class ManagedUserPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Nueva contraseña"
        self.fields["new_password2"].label = "Confirmar contraseña"
        self.fields["new_password1"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "Mínimo 8 caracteres",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "autocomplete": "new-password",
                "placeholder": "Repite la contraseña",
            }
        )

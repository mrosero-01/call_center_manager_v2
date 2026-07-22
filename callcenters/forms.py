from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django import forms

from clients.models import Client

from .models import CallCenter


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            "name",
            "description",
            "is_active",
        )
        labels = {
            "name": "Nombre del cliente",
            "description": "Descripción",
            "is_active": "Cliente activo",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Claro",
                    "autocomplete": "organization",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Información breve para identificar al cliente."
                    ),
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        existing = Client.objects.filter(
            name__iexact=name,
        )

        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError(
                "Ya existe un cliente con este nombre."
            )

        return name


class CallCenterBaseForm(forms.ModelForm):
    class Meta:
        model = CallCenter
        fields = (
            "client",
            "name",
            "timezone",
            "closed_audio_file",
            "is_active",
        )
        labels = {
            "client": "Cliente",
            "name": "Nombre del CallCenter",
            "timezone": "Zona horaria",
            "closed_audio_file": "Audio de cierre predeterminado",
            "is_active": "CallCenter activo",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Pasto Abasolo Claro",
                }
            ),
            "timezone": forms.TextInput(
                attrs={
                    "placeholder": "America/Bogota",
                    "list": "timezone-options",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = Client.objects.order_by(
            "name",
        )
        self.fields["client"].empty_label = "Selecciona un cliente"

    def clean_timezone(self):
        timezone_name = self.cleaned_data["timezone"].strip()

        try:
            ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise forms.ValidationError(
                "Escribe una zona horaria válida, por ejemplo America/Bogota."
            ) from exc

        return timezone_name

    def clean(self):
        cleaned_data = super().clean()
        client = cleaned_data.get("client")
        name = (cleaned_data.get("name") or "").strip()

        if client and name:
            duplicates = CallCenter.objects.filter(
                client=client,
                name__iexact=name,
            )

            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)

            if duplicates.exists():
                self.add_error(
                    "name",
                    "Este cliente ya tiene un CallCenter con ese nombre.",
                )

        cleaned_data["name"] = name
        return cleaned_data


class CallCenterCreateForm(CallCenterBaseForm):
    class Meta(CallCenterBaseForm.Meta):
        fields = (
            "client",
            "name",
            "codename",
            "timezone",
            "closed_audio_file",
            "is_active",
        )
        labels = {
            **CallCenterBaseForm.Meta.labels,
            "codename": "Código de integración",
        }
        widgets = {
            **CallCenterBaseForm.Meta.widgets,
            "codename": forms.TextInput(
                attrs={
                    "placeholder": "Ej: pas_aba_cla",
                    "autocomplete": "off",
                }
            ),
        }

    def clean_codename(self):
        return self.cleaned_data["codename"].strip().lower()


class CallCenterUpdateForm(CallCenterBaseForm):
    pass

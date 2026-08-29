import uuid

from django import forms

from .models import Transfer


class TransferForm(forms.ModelForm):
    request_key = forms.UUIDField(widget=forms.HiddenInput)

    class Meta:
        model = Transfer
        fields = ("recipient_name", "pix_key", "amount")
        labels = {
            "recipient_name": "Nome do destinatário",
            "pix_key": "Chave Pix",
            "amount": "Valor (R$)",
        }
        widgets = {
            "recipient_name": forms.TextInput(attrs={"autocomplete": "off"}),
            "pix_key": forms.TextInput(attrs={"autocomplete": "off", "autocapitalize": "none"}),
            "amount": forms.NumberInput(
                attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal", "autocomplete": "off"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["request_key"] = uuid.uuid4()

    def clean_pix_key(self):
        value = self.cleaned_data["pix_key"].strip()
        if len(value) < 3:
            raise forms.ValidationError("Informe uma chave Pix válida para a demonstração.")
        return value

    def clean_recipient_name(self):
        return self.cleaned_data["recipient_name"].strip()

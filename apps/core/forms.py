from django import forms


class AssistantForm(forms.Form):
    question = forms.CharField(
        label="Sua dúvida",
        max_length=1000,
        widget=forms.TextInput(attrs={"placeholder": "Ex.: Como conferir uma transferência Pix?"}),
    )

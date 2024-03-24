from django import forms


class CheckForm(forms.Form):
    def __init__(self, *args, **kwargs):
        dynamic_value = kwargs.pop('dynamic_value', None)
        super(CheckForm, self).__init__(*args, **kwargs)
        self.fields['hidden_field'] = forms.CharField(widget=forms.HiddenInput(attrs={'value': dynamic_value}))

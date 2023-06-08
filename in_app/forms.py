from django import forms
from django.contrib.auth.forms import UserCreationForm

from in_app.models import User


class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(
        label='Phone',
        required=True,
        widget=forms.TextInput(attrs={'type': 'tel'})
    )

    class Meta:
        model = User
        fields = ('phone',)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Phone number is already in use.')
        return phone
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "phone", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"phone": self.cleaned_data["phone"]},
            )
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileUpdateForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=20, required=True)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if self.user and not self.is_bound:
            profile = getattr(self.user, "profile", None)
            self.initial.update(
                {
                    "username": self.user.username,
                    "email": self.user.email,
                    "first_name": self.user.first_name,
                    "last_name": self.user.last_name,
                    "phone": profile.phone if profile else "",
                }
            )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if (
            User.objects.filter(username__iexact=username)
            .exclude(id=getattr(self.user, "id", None))
            .exists()
        ):
            raise forms.ValidationError("Этот логин уже занят.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if (
            User.objects.filter(email__iexact=email)
            .exclude(id=getattr(self.user, "id", None))
            .exists()
        ):
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self):
        if not self.user:
            return None

        self.user.username = self.cleaned_data["username"]
        self.user.email = self.cleaned_data["email"]
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.save(update_fields=["username", "email", "first_name", "last_name"])

        UserProfile.objects.update_or_create(
            user=self.user,
            defaults={"phone": self.cleaned_data["phone"]},
        )
        return self.user

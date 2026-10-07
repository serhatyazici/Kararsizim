from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User, username_format_validator, validate_username_not_reserved


class LowercaseCharField(forms.CharField):
    """Girilen metni doğrulamadan ÖNCE küçük harfe çevirir ("Ali" → "ali")."""

    def to_python(self, value):
        value = super().to_python(value)
        return value.lower() if value else value


class LowercaseEmailField(forms.EmailField):
    def to_python(self, value):
        value = super().to_python(value)
        return value.lower() if value else value


class StyledFormMixin:
    """Tüm alanlara tasarım sistemindeki .input sınıfını ekler."""

    def apply_input_style(self):
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class SignupForm(StyledFormMixin, UserCreationForm):
    """
    Form = HTML formunu ve gelen verinin doğrulamasını tek yerde tanımlayan sınıf.
    ModelForm türevi olduğu için doğrulanan veriden doğrudan bir User kaydı üretebilir.
    """

    email = LowercaseEmailField(
        label="E-posta",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        error_messages={
            "required": "E-posta zorunludur.",
            "invalid": "Geçerli bir e-posta adresi gir.",
        },
    )
    username = LowercaseCharField(
        label="Kullanıcı adı",
        max_length=20,
        validators=[username_format_validator, validate_username_not_reserved],
        help_text="3–20 karakter; küçük harf, rakam, _ ve . kullanabilirsin.",
        widget=forms.TextInput(attrs={"autocomplete": "username"}),
        error_messages={"required": "Kullanıcı adı zorunludur."},
    )

    class Meta:
        model = User
        fields = ("email", "username")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Parola"
        self.fields["password2"].label = "Parola (tekrar)"
        self.fields["password2"].help_text = ""
        self.apply_input_style()

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu e-posta adresiyle zaten bir hesap var.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Bu kullanıcı adı zaten alınmış.")
        return username


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = LowercaseEmailField(
        label="E-posta",
        widget=forms.EmailInput(attrs={"autofocus": True, "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Parola",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    # Hangisinin yanlış olduğunu söylemeyen genel mesaj
    error_messages = {
        "invalid_login": "E-posta veya parola hatalı.",
        "inactive": "Bu hesap aktif değil.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_input_style()

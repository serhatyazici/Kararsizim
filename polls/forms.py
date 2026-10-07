from django import forms

MIN_OPTIONS = 2
MAX_OPTIONS = 5
QUESTION_MIN_LENGTH = 5
QUESTION_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 500
OPTION_MAX_LENGTH = 80


class PollCreateForm(forms.Form):
    """
    Soru ve açıklama normal form alanlarıdır. Seçenekler sayıları değişebildiği için
    aynı isimli birden çok input (name="options") olarak gelir ve clean() içinde doğrulanır.
    """

    question = forms.CharField(
        label="Sorun ne?",
        max_length=QUESTION_MAX_LENGTH,
        widget=forms.TextInput(
            attrs={"class": "input", "data-counter": "", "placeholder": "Bu akşam sinemaya mı gitsem, restorana mı?"}
        ),
        error_messages={
            "required": "Soru boş olamaz.",
            "max_length": f"Soru en fazla {QUESTION_MAX_LENGTH} karakter olabilir.",
        },
    )
    description = forms.CharField(
        label="Açıklama (isteğe bağlı)",
        required=False,
        max_length=DESCRIPTION_MAX_LENGTH,
        widget=forms.Textarea(
            attrs={"class": "input", "data-counter": "", "rows": 3, "placeholder": "Bütçem 300 TL gibi bağlam ekleyebilirsin"}
        ),
        error_messages={
            "max_length": f"Açıklama en fazla {DESCRIPTION_MAX_LENGTH} karakter olabilir.",
        },
    )

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        # Hata olursa formu aynı seçeneklerle yeniden çizebilmek için ham değerleri sakla
        raw = data.getlist("options") if data is not None else []
        self.option_values = [value.strip() for value in raw]
        while len(self.option_values) < MIN_OPTIONS:
            self.option_values.append("")
        self.cleaned_options = []

    def clean_question(self):
        question = self.cleaned_data["question"]  # CharField varsayılan olarak baştaki/sondaki boşlukları kırpar
        if len(question) < QUESTION_MIN_LENGTH:
            raise forms.ValidationError(f"Soru en az {QUESTION_MIN_LENGTH} karakter olmalı.")
        return question

    def clean(self):
        cleaned = super().clean()

        # Boş bırakılan seçenek alanları yok sayılır
        options = [value for value in self.option_values if value]

        if len(options) < MIN_OPTIONS:
            self.add_error(None, f"En az {MIN_OPTIONS} seçenek girmelisin.")
        if len(options) > MAX_OPTIONS:
            self.add_error(None, f"En fazla {MAX_OPTIONS} seçenek ekleyebilirsin.")
        if any(len(option) > OPTION_MAX_LENGTH for option in options):
            self.add_error(None, f"Her seçenek en fazla {OPTION_MAX_LENGTH} karakter olabilir.")

        # Büyük/küçük harf duyarsız tekrar kontrolü ("Sinema" = "sinema")
        folded = [option.casefold() for option in options]
        if len(set(folded)) != len(folded):
            self.add_error(None, "Aynı seçeneği birden fazla kez ekleyemezsin.")

        self.cleaned_options = options
        return cleaned

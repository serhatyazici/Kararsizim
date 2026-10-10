# kararsızım — Proje Planı

> Bu dosya Claude Code için projenin **tek doğruluk kaynağıdır**: ürün tanımı, teknik kararlar, veri modeli, tasarım sistemi ve fazlara bölünmüş geliştirme planı burada.
> Kodda proje adı `kararsizim` (ASCII), arayüzde **kararsızım** olarak yazılır.

---

## 0. Claude Code için çalışma kuralları

1. **Faz faz ilerle.** Sadece kullanıcının istediği fazı uygula. Bir faz bitince sonrakine kendiliğinden geçme.
2. **Önce plan, sonra kod.** Her faza başlarken oluşturacağın/değiştireceğin dosyaları ve sırayı kısa bir liste halinde yaz, kullanıcının onayını bekle.
3. **Faz kapanışı.** Faz bitince:
   - o fazın "Kabul kriterleri"ni tek tek kontrol et ve sonucu yaz (✅ / ❌),
   - `python manage.py check` ve `python manage.py test` çalıştır,
   - Bölüm 12'deki **İlerleme durumu**nu güncelle (alınan önemli kararları da oraya not et),
   - kullanıcının tarayıcıda elle nasıl test edeceğini adım adım yaz,
   - bir commit mesajı öner (commit/push'u kullanıcı kendisi yapar).
4. **Öğretici ol.** Kullanıcı Django'yu bu projede öğrenen bir bilgisayar mühendisliği öğrencisi. Yeni bir kavram ilk kez kullanıldığında (model, migration, view, URL routing, template, form, CSRF, middleware, ORM sorgusu, transaction…) ne işe yaradığını 2–3 cümleyle açıkla. Uzun ders anlatma.
5. **Yığına sadık kal.** Bölüm 3'te olmayan bir paket, framework veya servis ekleme; gerçekten gerekiyorsa önce gerekçesiyle sor. Frontend'de React/Vue/Tailwind/npm/build adımı yok. CDN'den sadece Google Fonts yüklenir.
6. **Kod stili.** PEP 8. Değişken, fonksiyon, sınıf ve model adları İngilizce; kullanıcının gördüğü bütün metinler Türkçe; kod yorumları kısa ve Türkçe.
7. **Gizlilik.** Kullanıcının e-postası başka kullanıcılara hiçbir şablonda, JSON yanıtında veya HTML attribute'unda gösterilmez. Her yerde `@kullaniciadi` kullanılır.
8. **Sırlar koda girmez.** `SECRET_KEY`, veritabanı şifresi vb. sadece `.env` dosyasında / Vercel environment variables'ta durur. `.env` git'e eklenmez. Kullanıcıdan şifre isteme; değeri nereye yazacağını söyle.
9. **Komutlar.** Terminal komutu verirken, farklı oldukları yerde Windows (PowerShell) ve macOS/Linux karşılıklarını ayrı ver.
10. **Emin değilsen sor.** Bu dosyada tanımlı olmayan bir ürün kararını tahminle verme.

---

## 1. Ürün özeti

**kararsızım**, kararsız kalınan günlük konularda topluluğa danışılan bir anket platformu.

- Kullanıcı bir soru sorar: *"Bu akşam sinemaya mı gitsem, restorana mı?"*
- **En az 2, en fazla 5** seçenek ekler.
- Platformdaki **herkes** bu anketi görür ve oy verir. Takip/arkadaşlık sistemi **yok**; tek bir ortak akış var.
- Üye olmadan anketler görüntülenebilir ve oylanabilir. **Anket oluşturmak için üyelik şart.**
- Üyelik: **e-posta + parola + kullanıcı adı**. Anketlerde sadece kullanıcı adı görünür; e-posta asla görünmez.

**Slogan:** "Kararsız mısın? Sor, millet karar versin."

**İlk hedef:** çalışan, yayında ve şık bir **prototip**. Karmaşık altyapı yok; özellikler sonra adım adım eklenecek.

---

## 2. Roller ve yetkiler

| İşlem | Ziyaretçi (üye değil) | Üye | Anketin sahibi |
|---|---|---|---|
| Akışı ve anket detayını görme | ✅ | ✅ | ✅ |
| Oy verme (anket başına 1 oy) | ✅ (tarayıcı çereziyle) | ✅ | ✅ (kendi anketine de) |
| Sonuçları (yüzdeleri) görme | Oy verdikten sonra | Oy verdikten sonra | Her zaman |
| Toplam oy sayısını görme | ✅ | ✅ | ✅ |
| Anket oluşturma | ❌ → giriş/kayıt sayfasına yönlendirilir | ✅ | — |
| Anketi silme | ❌ | ❌ | ✅ |
| Anketi düzenleme | ❌ | ❌ | ❌ (prototipte yok; oyları bozar) |
| Oyu değiştirme / geri alma | ❌ | ❌ | ❌ (prototipte yok) |
| Admin paneli | ❌ | ❌ | Sadece superuser |

---

## 3. Teknoloji yığını ve kararlar

| Katman | Seçim | Not |
|---|---|---|
| Dil | Python 3.14 (yerel) | Yerelde PyCharm'ın oluşturduğu `.venv` (3.14) kullanılır; Vercel'de Python sürümü Faz 6'da ayrıca sabitlenir |
| Backend | Django 5.2 LTS | Server-side rendering, Django templates |
| Kimlik doğrulama | Django'nun yerleşik auth sistemi + custom `User` modeli | Supabase Auth **kullanılmıyor** |
| Veritabanı | Supabase Postgres (geliştirmede SQLite) | Supabase sadece Postgres sunucusu olarak kullanılır; `supabase-py`, Supabase Data API ve Supabase Auth yok |
| DB sürücüsü | `psycopg[binary]` (psycopg 3) | |
| Frontend | Django templates + düz HTML/CSS + vanilla JavaScript | Aynı repo içinde `templates/` ve `static/` |
| Deployment | Vercel (Django zero-config) | Vercel `manage.py`'yi bulur, giriş noktasını `WSGI_APPLICATION`'dan okur; `vercel.json` sadece bölge ayarı için |

**`requirements.txt` (tamamı bu kadar):**
```
Django>=5.2,<6.0
psycopg[binary]>=3.2
dj-database-url>=2.2
python-dotenv>=1.0
```

**Neden geliştirmede SQLite?** Faz 0–4 boyunca hızlı ve sıfır kurulumla çalışmak için. `DATABASE_URL` tanımlıysa Postgres'e, değilse SQLite'a bağlanan tek bir ayar yazılır; Faz 5'te sadece `.env`'ye URL eklenerek Supabase'e geçilir. Vercel'in dosya sistemi kalıcı olmadığı için **production'da SQLite kullanılamaz.**

---

## 4. Kapsam dışı (prototipte YAPMA)

Takip sistemi, yorumlar, beğeniler, bildirimler, görsel yükleme, kategoriler/etiketler, arama, e-posta doğrulama, şifre sıfırlama, sosyal giriş, süreli anketler, oy değiştirme, karanlık mod, REST API / DRF, WebSocket / gerçek zamanlı güncelleme, Celery, Docker, React/Vue/Tailwind, npm.
Bunlar Bölüm 13'teki yol haritasında.

---

## 5. Proje yapısı

```
kararsizim/
├── CLAUDE.md
├── manage.py
├── requirements.txt
├── vercel.json              # Faz 6
├── .env                     # git'e girmez
├── .env.example
├── .gitignore
├── config/                  # Django proje paketi
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                # kullanıcı sistemi
│   ├── models.py            # User
│   ├── forms.py             # SignupForm, LoginForm
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── polls/                   # anketler ve oylar
│   ├── models.py            # Poll, Option, Vote
│   ├── forms.py             # PollCreateForm
│   ├── services.py          # cast_vote, get_results gibi iş mantığı
│   ├── middleware.py        # VoterTokenMiddleware
│   ├── templatetags/
│   │   └── poll_extras.py   # avatar rengi, "2 saat önce" filtresi
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── templates/
│   ├── base.html
│   ├── partials/            # _header.html, _poll_card.html, _messages.html
│   ├── accounts/            # signup.html, login.html
│   ├── polls/               # feed.html, detail.html, create.html
│   ├── 404.html
│   └── 500.html
└── static/
    ├── css/main.css
    ├── js/main.js           # ortak: toast, küçük yardımcılar
    ├── js/create-poll.js    # seçenek ekle/çıkar
    ├── js/vote.js           # oy verme + sonuç animasyonu
    └── img/favicon.svg
```

> ⚠️ Vercel, settings'te `ASGI_APPLICATION` tanımlıysa ASGI'yi seçer. Bu projede sadece `WSGI_APPLICATION = "config.wsgi.application"` tanımlı olsun.

---

## 6. Veri modeli

### `accounts.User` (AbstractUser'dan türetilir)
| Alan | Tip | Kural |
|---|---|---|
| `email` | EmailField | `unique=True`, kaydederken küçük harfe çevrilir, **giriş kimliği** |
| `username` | CharField(20) | `unique=True`, küçük harf, regex `^[a-z0-9_.]{3,20}$`, büyük/küçük harf duyarsız benzersiz |
| diğerleri | AbstractUser'dan | `first_name` / `last_name` kullanılmaz |

- `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = ["username"]` (gerekirse custom `UserManager`).
- `AUTH_USER_MODEL = "accounts.User"` — **ilk `migrate`'ten ÖNCE** tanımlanmalı; sonradan değiştirmek çok zahmetli.
- Ayrılmış kullanıcı adları reddedilir: `admin, root, kararsizim, destek, support, anket, giris, kayit, cikis`.
- `__str__` → `@username`.

### `polls.Poll`
| Alan | Tip | Kural |
|---|---|---|
| `author` | FK → User | `on_delete=CASCADE`, `related_name="polls"` |
| `question` | CharField(200) | zorunlu, kırpılmış hali 5–200 karakter |
| `description` | TextField | opsiyonel, en fazla 500 karakter ("bütçem 300 TL" gibi bağlam için) |
| `created_at` | DateTimeField | `auto_now_add=True`, `db_index=True` |

`Meta.ordering = ["-created_at"]`

### `polls.Option`
| Alan | Tip | Kural |
|---|---|---|
| `poll` | FK → Poll | `CASCADE`, `related_name="options"` |
| `text` | CharField(80) | zorunlu, kırpılmış hali 1–80 karakter |
| `position` | PositiveSmallIntegerField | 0–4; sırayı ve **seçenek rengini** belirler |

`UniqueConstraint(fields=["poll", "position"])`, `Meta.ordering = ["position"]`

### `polls.Vote`
| Alan | Tip | Kural |
|---|---|---|
| `poll` | FK → Poll | `CASCADE`, `related_name="votes"` (benzersizlik kısıtı için tutulur) |
| `option` | FK → Option | `CASCADE`, `related_name="votes"` |
| `user` | FK → User | `null=True`, `blank=True`, `on_delete=SET_NULL` |
| `voter_token` | UUIDField | zorunlu; tarayıcı çerezinden gelir |
| `created_at` | DateTimeField | `auto_now_add=True` |

Kısıtlar:
- `UniqueConstraint(fields=["poll", "voter_token"], name="one_vote_per_browser")`
- `UniqueConstraint(fields=["poll", "user"], condition=Q(user__isnull=False), name="one_vote_per_user")`
- Kayıttan önce `option.poll_id == poll.id` kontrol edilir.

---

## 7. Sayfalar ve URL'ler

| URL | View | Erişim | Açıklama |
|---|---|---|---|
| `/` | `feed` | herkes | Tüm anketler, en yeni üstte, sayfa başına 10 (`?sayfa=2`) |
| `/anket/<int:pk>/` | `poll_detail` | herkes | Tek anket, paylaşılabilir link |
| `/anket/yeni/` | `poll_create` | giriş gerekli | Anket oluşturma formu |
| `/anket/<int:pk>/oy/` | `vote` | herkes, sadece POST | Oy verir; JSON veya redirect döner |
| `/anket/<int:pk>/sil/` | `poll_delete` | sahibi, sadece POST | Anketi siler |
| `/kayit/` | `signup` | herkes (girişliyse `/`'a yönlendir) | |
| `/giris/` | `login` | herkes | `?next=` destekli |
| `/cikis/` | `logout` | sadece POST | Django 5'te logout POST ister |
| `/admin/` | Django admin | superuser | Moderasyon |

`LOGIN_URL = "accounts:login"`, `LOGIN_REDIRECT_URL = "/"`, `LOGOUT_REDIRECT_URL = "/"`.

---

## 8. İş kuralları

### 8.1 Kayıt ve giriş
- Kayıt formu: e-posta, kullanıcı adı, parola, parola (tekrar). Django'nun parola validator'ları aktif; hata mesajları Türkçe (`LANGUAGE_CODE = "tr"`).
- Kullanıcı adı alanının altında ipucu: "3–20 karakter; küçük harf, rakam, _ ve . kullanabilirsin."
- Kayıt başarılıysa kullanıcı **otomatik giriş yapar**; `next` varsa oraya, yoksa `/`'a gider. Mesaj: "Hoş geldin @kullaniciadi! 🎉"
- Giriş: e-posta + parola. Hatalı girişte genel mesaj: "E-posta veya parola hatalı." (hangisinin yanlış olduğunu söyleme).
- Ziyaretçi "Anket oluştur"a tıklarsa `/giris/?next=/anket/yeni/` sayfasına gider ve "Anket oluşturmak için giriş yap ya da hemen üye ol." bilgi mesajını görür. (`login_required` mesaj eklemez; bunun için küçük bir kontrol/sarmalayıcı yaz.) Giriş sayfasındaki "Üye ol" linki de `next` değerini taşır.

### 8.2 Anket oluşturma
- Soru 5–200, açıklama ≤500, her seçenek 1–80 karakter; tüm metinler baştaki/sondaki boşluklardan arındırılır.
- **Seçenek sayısı 2–5.** Boş bırakılan seçenek alanları yok sayılır; kalan sayı 2'den azsa hata.
- Aynı ankette aynı seçenek iki kez olamaz (büyük/küçük harf duyarsız; `casefold()` ile karşılaştır).
- `Poll` ve `Option` kayıtları `transaction.atomic()` içinde oluşturulur.
- Asıl doğrulama **sunucuda** yapılır; JS sadece kolaylık sağlar.
- Başarılıysa anketin detay sayfasına yönlendir: "Anketin yayında! Linki paylaş, oylar gelsin."

### 8.3 Oy verme
- `VoterTokenMiddleware` her tarayıcıya bir `kz_voter` çerezi atar: UUID4, 1 yıl ömürlü, `HttpOnly`, `SameSite=Lax`, production'da `Secure`. Çerez yoksa veya geçerli bir UUID değilse yenisi üretilir. Middleware `request.voter_token` sağlar.
- Bir ankete daha önce **aynı `voter_token` ile VEYA (giriş yapılmışsa) aynı `user` ile** oy verilmişse yeni oy reddedilir. Oy kaydında her zaman `voter_token`, giriş yapılmışsa ayrıca `user` saklanır.
- Eşzamanlı isteklere karşı asıl güvence veritabanı kısıtlarıdır; `IntegrityError` yakalanıp "zaten oy verdin" olarak döndürülür.
- Oy kesindir, değiştirilemez (prototip).
- `POST /anket/<pk>/oy/` gövdesinde `option_id` gelir. İstek `fetch` ile geldiyse (`Accept: application/json`) JSON döner; normal form gönderimiyse detay sayfasına redirect + mesaj.

JSON yanıt şeması:
```json
{
  "ok": true,
  "total_votes": 24,
  "voted_option_id": 57,
  "results": [
    {"option_id": 56, "text": "Sinema", "votes": 15, "percent": 63},
    {"option_id": 57, "text": "Restoran", "votes": 9, "percent": 37}
  ]
}
```
- Hatalar: geçersiz/başka ankete ait seçenek → `400 {"ok": false, "error": "..."}`; zaten oy verilmiş → `409` (+ güncel sonuçlar ve önceki `voted_option_id`); anket yok → `404`.
- Yüzdeler tam sayıdır ve **toplamları her zaman 100'dür** (en büyük kalan yöntemi): her seçeneğin yüzdesi önce aşağı yuvarlanır, eksik kalan puanlar ondalık kalanı en büyük olan seçeneklere birer birer verilir. Eşitlikte önce oyu fazla olan, o da eşitse `position` değeri küçük olan kazanır. Toplam oy 0 ise hepsi 0. (Örnek: 15 ve 9 oy → 62,5 ve 37,5 → 63 ve 37.) Bu mantık `get_results` içinde yazılır ve ayrıca test edilir.

> Not: Çerez tabanlı kontrol kusursuz değildir (gizli sekme veya çerez silme ile tekrar oy verilebilir). Prototip için bilinçli olarak kabul edildi; sıkılaştırma yol haritasında.

### 8.4 Sonuçların görünürlüğü
- Oy vermemiş ziyaretçi/üye: seçenekleri tıklanabilir butonlar olarak görür + "24 oy" bilgisi. Yüzdeleri göremez (diğer oyların yönlendirme etkisini önlemek için).
- Oy vermiş kişi: renkli sonuç çubuklarını, yüzdeleri ve kendi seçtiği seçenekte ✓ işaretini görür. En çok oy alan seçenekte "önde 🔥" rozeti.
- Anketin sahibi: kendi anketinin sonuçlarını oy vermeden de görür; isterse oy da verebilir.

### 8.5 Silme
- Sadece sahibi silebilir; `POST` + JS `confirm("Bu anketi silmek istediğine emin misin?")`. Sahibi olmayan kullanıcının isteği → 404.

### 8.6 Performans (N+1'den kaçın)
Akışta: `select_related("author")`; seçenekler `Prefetch` + `annotate(vote_count=Count("votes"))`; anketler `annotate(total_votes=Count("votes", distinct=True))`. Ziyaretçinin o sayfadaki hangi anketlere oy verdiği **tek sorguda** bulunur (`poll_id → option_id` sözlüğü).

---

## 9. Arayüz ve tasarım sistemi

**Hedef his:** genç, enerjik ama temiz. Açık (neredeyse beyaz) arka plan, üzerinde canlı renklerin yumuşak tonları (tint), bol boşluk, yuvarlak köşeler, küçük ve eğlenceli mikro animasyonlar. Sosyal medya akışı gibi tek sütunlu ve mobil öncelikli.

### 9.1 Renkler (`static/css/main.css` içinde `:root` token'ları)
```css
:root {
  /* Zemin ve metin */
  --bg: #F7F6FF;            /* çok açık lavanta-beyaz */
  --surface: #FFFFFF;       /* kartlar */
  --surface-2: #F1EFFD;     /* input zemini, hover */
  --border: #E6E2F7;
  --text: #1B1630;
  --text-muted: #6B6585;

  /* Marka rengi: elektrik moru */
  --primary: #6C4CFF;
  --primary-ink: #4B2FD6;   /* koyu ton: metin, hover */
  --primary-tint: #EEEAFF;  /* açık ton: zemin */

  /* Seçenek renkleri — en fazla 5 seçenek = 5 renk */
  --opt-1: #FF4D8D; --opt-1-tint: #FFE8F0; --opt-1-ink: #B8185A;  /* pembe */
  --opt-2: #FF9F1C; --opt-2-tint: #FFF2DE; --opt-2-ink: #A85A00;  /* turuncu */
  --opt-3: #18C29C; --opt-3-tint: #DDF8F0; --opt-3-ink: #087A61;  /* nane */
  --opt-4: #3DA5FF; --opt-4-tint: #E2F1FF; --opt-4-ink: #0B62B3;  /* gök mavisi */
  --opt-5: #8BD13F; --opt-5-tint: #EEFADF; --opt-5-ink: #3F7A0C;  /* limon yeşili */

  --success: #18C29C;
  --danger: #FF4D6A;

  /* Şekil ve gölge */
  --radius-sm: 10px;
  --radius-md: 14px;
  --radius-lg: 22px;
  --radius-pill: 999px;
  --shadow-card: 0 1px 2px rgba(27, 22, 48, .04), 0 8px 24px rgba(108, 76, 255, .08);
  --shadow-pop: 0 12px 32px rgba(108, 76, 255, .18);

  /* Tipografi */
  --font-display: "Bricolage Grotesque", system-ui, sans-serif;
  --font-body: "Plus Jakarta Sans", system-ui, sans-serif;
}
```
Kurallar:
- Tint zemin üzerindeki metin her zaman ilgili `-ink` rengiyle yazılır (WCAG AA kontrast). Canlı renkler (`--opt-n`) beyaz zeminde metin rengi olarak kullanılmaz; çubuk, nokta, kenarlık ve ikonlar içindir.
- Seçeneğin `position` değeri 0–4 → `--opt-1` … `--opt-5`. Template'te `data-color="{{ option.position|add:1 }}"` gibi bir attribute ile bağlanır.
- `body` arka planına 2–3 adet çok düşük opaklıkta (~%15–25), bulanık renkli leke (radial-gradient: mor, pembe, nane) `background-attachment: fixed` ile eklenir → "tonlu" zemin hissi. Okunabilirliği bozmamalı.

### 9.2 Tipografi
- Google Fonts: **Bricolage Grotesque** (700/800; logo ve başlıklar) + **Plus Jakarta Sans** (400/500/600/700; gövde). Türkçe karakterleri (ğ ş ı İ ç ö ü) doğru gösterdiklerini kontrol et; sorun olursa başlıklarda da Plus Jakarta Sans kullan.
- Taban boyut 16px; anket sorusu ~1.25rem / 700; logo ~1.5rem / 800.

### 9.3 Bileşenler
- **Header:** sticky, yarı saydam beyaz + `backdrop-filter: blur`. Solda logo "kararsızım" (mor; sonunda pembe bir "?" vurgusu). Sağda: ziyaretçiyse "Giriş" (metin buton) + "Üye ol" (mor pill); üyeyse "Anket oluştur" + `@kullaniciadi` + "Çıkış".
- **Buton:** pill şekli. Primary: mor zemin, beyaz metin; hover'da 1–2px yukarı kalkma + `--shadow-pop`; active'de `scale(.97)`. Secondary: `--primary-tint` zemin, `--primary-ink` metin.
- **Input:** `--surface-2` zemin, `--radius-md`, focus'ta 3px mor tint halka. Alan hatası inputun altında küçük kırmızı metin.
- **Anket kartı (`partials/_poll_card.html`):**
  - Üst satır: avatar (kullanıcı adının baş harfi; rengi kullanıcı adından türetilen sabit bir `--opt-n`) + `@kullaniciadi` + "· 2 saat önce" (tek birimlik göreli zaman: `django.utils.timesince.timesince(value, depth=1)` kullanan küçük bir filtre + " önce").
  - Soru (display font) + varsa açıklama (muted renk).
  - Seçenekler: tam genişlikte, tint zeminli, solunda renkli nokta olan butonlar. Hover'da kenarlık seçeneğin rengine döner.
  - Oydan sonra her seçenek bir **sonuç çubuğuna** dönüşür: tint zemin üzerinde yüzdesi kadar genişlikte seçenek renginde dolgu (soldan sağa ~600ms animasyon), metin `-ink` renginde, yüzde sağda kalın. Seçilen seçenekte ✓, lider seçenekte "önde 🔥" rozeti.
  - Alt satır: "24 oy" · "Paylaş" · (sahibiyse) "Sil".
- **Akış:** ortada en fazla ~640px genişlikte tek sütun, kartlar arası 16px boşluk. Ziyaretçiye en üstte küçük bir karşılama kartı: slogan + "Hemen üye ol" butonu.
- **Mobil:** ≤640px'te header sadeleşir; üyeler için sağ altta yuvarlak "+" (anket oluştur) butonu.
- **Toast:** Django `messages` sağ üstte (mobilde altta) tint renkli küçük kartlar olarak çıkar, 4 sn sonra kaybolur, kapatma butonu vardır.
- **Boş durum:** "Henüz anket yok. İlk kararsızlığı sen paylaş! 🤔" + buton.

### 9.4 Erişilebilirlik ve hareket
- Tüm etkileşimli öğelerde görünür `:focus-visible` halkası.
- Sonuç alanında `aria-live="polite"`.
- `@media (prefers-reduced-motion: reduce)` ile animasyonlar kapatılır.
- Kontrast en az WCAG AA.

---

## 10. Ortam değişkenleri ve ayarlar

`.env.example`:
```
# Django
SECRET_KEY=degistir-beni
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://*.vercel.app

# Veritabanı — boş bırakılırsa SQLite kullanılır.
# Uygulama için Supabase "Transaction pooler" (port 6543) adresi:
DATABASE_URL=
```

`config/settings.py` kuralları:
- `.env` dosyası `python-dotenv` ile `settings.py`'nin başında yüklenir (Vercel'de dosya yoktur, sessizce geçer; terminalde tanımlı değişkenleri ezmez).
- `DEBUG = os.environ.get("DEBUG", "False") == "True"`
- `DEBUG` kapalıyken `SECRET_KEY` tanımlı değilse `ImproperlyConfigured` fırlat.
- `ALLOWED_HOSTS` ve `CSRF_TRUSTED_ORIGINS` virgülle ayrılmış env değerlerinden okunur.
- Veritabanı:
```python
import dj_database_url

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=0, ssl_require=True)
    }
    # Supabase transaction pooler server-side cursor desteklemez
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    }
```
- Production (`DEBUG=False`) iken: `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`.
- `LANGUAGE_CODE = "tr"`, `TIME_ZONE = "Europe/Istanbul"`, `USE_TZ = True`.
- `TEMPLATES[0]["DIRS"] = [BASE_DIR / "templates"]`.
- `STATIC_URL = "static/"`, `STATICFILES_DIRS = [BASE_DIR / "static"]`, `STATIC_ROOT = BASE_DIR / "staticfiles"`. Vercel `STATIC_ROOT`'u görünce `collectstatic`'i build sırasında kendisi çalıştırır ve dosyaları CDN'den sunar; WhiteNoise gerekmez.

---

## 11. Geliştirme fazları

### Faz 0 — Kurulum ve iskelet
**Amaç:** Doğru klasör yapısı, ortam değişkenleri, custom User modeli ve tasarım token'larıyla çalışan boş bir Django projesi.

**Yapılacaklar**
1. `.gitignore` (`.venv/`, `.env`, `db.sqlite3`, `__pycache__/`, `staticfiles/`, `.vercel/`, `.DS_Store`, `.idea/`, `.vscode/`), `requirements.txt`, `.env.example`, `.env`.
2. Sanal ortam ve kurulum (`.venv` PyCharm tarafından zaten oluşturuldu; yoksa aşağıdaki komutlarla oluşturulur):
   ```
   # Windows (PowerShell)
   py -3.14 -m venv .venv
   .venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # ikisinde de
   pip install -r requirements.txt
   django-admin startproject config .
   python manage.py startapp accounts
   python manage.py startapp polls
   ```
3. App'leri `INSTALLED_APPS`'e ekle.
4. `accounts.User` modelini (Bölüm 6) ve `AUTH_USER_MODEL`'i **ilk migrate'ten önce** yaz; admin'e kaydet.
5. `settings.py`'yi Bölüm 10'a göre düzenle.
6. `templates/base.html`: `<html lang="tr">`, viewport meta, Google Fonts, `main.css`, header/footer iskeleti, `{% block title %}`, `{% block content %}`, sayfa sonunda `main.js`.
7. `static/css/main.css`: Bölüm 9.1 token'ları, küçük bir reset, temel tipografi, buton/kart/input stilleri, renkli arka plan lekeleri.
8. Geçici ana sayfa (`/`): logo + slogan + "Yakında" kartı.
9. `makemigrations`, `migrate`, `createsuperuser`.

**Kabul kriterleri**
- `python manage.py runserver` → `http://127.0.0.1:8000/` açılıyor; fontlar, renkler ve arka plan tonları yüklü.
- `python manage.py check` hatasız.
- `createsuperuser` e-posta ve kullanıcı adı soruyor; `/admin/`'e e-posta + parola ile girilebiliyor.
- `git status` çıktısında `.env`, `.venv/`, `db.sqlite3` görünmüyor.

---

### Faz 1 — Kullanıcı sistemi
**Amaç:** Kayıt, giriş, çıkış; header'da kullanıcı adı.

**Yapılacaklar**
1. `SignupForm` (`UserCreationForm` tabanlı): email, username, password1, password2. E-posta ve kullanıcı adı küçük harfe çevrilir; büyük/küçük harf duyarsız benzersizlik ve 8.1 kuralları uygulanır.
2. `LoginForm` (`AuthenticationForm` tabanlı): alan etiketi "E-posta".
3. View'lar: `signup` (başarılıysa `login()` + `next`'e yönlendirme), `login` (`LoginView`), `logout` (`LogoutView`, POST).
4. Şablonlar: `accounts/signup.html`, `accounts/login.html` — ortada tek kart, alan hataları inputun altında, genel hata formun üstünde, sayfalar arası linkler `next`'i korur.
5. Header: giriş durumuna göre butonlar; `@username`; çıkış butonu küçük bir POST formu (`{% csrf_token %}` ile).
6. `messages` framework'ü + `partials/_messages.html` (şimdilik basit; Faz 4'te toast olacak).
7. `User` admin: liste kolonları email, username, date_joined, is_staff; arama email ve username.
8. Testler (`accounts/tests.py`): kayıt, tekrarlı e-posta/kullanıcı adı, geçersiz kullanıcı adları, giriş, GET ile çıkışın çalışmaması.

**Kabul kriterleri**
- Yeni kullanıcı kayıt olunca otomatik giriş yapıyor; header'da `@kullaniciadi` görünüyor.
- `Deneme@Mail.com` kayıtlıyken `deneme@mail.com` ile tekrar kayıt reddediliyor; `Ali` varken `ali` reddediliyor.
- `ab`, `ali veli`, `admin` gibi kullanıcı adları anlaşılır Türkçe hata mesajıyla reddediliyor.
- E-posta + parola ile giriş/çıkış çalışıyor; `/cikis/`'e GET isteği çıkış yapmıyor.
- Hiçbir sayfanın HTML kaynağında başka bir kullanıcının e-postası geçmiyor.
- Testler geçiyor.

---

### Faz 2 — Anket oluşturma ve akış
**Amaç:** Üyeler anket oluşturabilsin, herkes akışta görebilsin (oylama henüz yok).

**Yapılacaklar**
1. `Poll` ve `Option` modelleri + migration + admin (`Option` inline).
2. `PollCreateForm`: `question`, `description`; seçenekler `request.POST.getlist("options")` ile alınır ve formun `clean()` metodunda 8.2 kurallarıyla doğrulanır.
3. `poll_create` view: giriş gerekli; ziyaretçi için 8.1'deki bilgi mesajı. Başarılıysa detay sayfasına redirect.
4. `polls/create.html` + `static/js/create-poll.js`:
   - varsayılan 2 seçenek alanı; "+ Seçenek ekle" butonu (5'te pasif); her seçenekte "×" butonu (2 seçenek kalınca gizli),
   - soru ve seçeneklerde karakter sayaçları, her seçenek alanının solunda kendi renk noktası,
   - doğrulama hatasında form, girilen soru ve seçeneklerle yeniden çizilir (veri kaybolmaz),
   - JS kapalıyken 2 seçenek alanı görünür; bu kabul edilebilir.
5. `feed` view: tüm anketler, `Paginator` ile 10'ar, `?sayfa=` parametresi; kartlar şimdilik seçenekleri sadece listeler.
6. `poll_detail` view + şablon.
7. `partials/_poll_card.html` hem akışta hem detayda kullanılır; avatar rengi ve "x önce" filtresi `poll_extras.py`'de.
8. Testler: 1 seçenek, 6 seçenek, tekrarlı seçenek, boş/kısa soru, boşlukların kırpılması, ziyaretçinin yönlendirilmesi, başarılı oluşturma.

**Kabul kriterleri**
- Üye; soru + 2–5 seçenekle anket oluşturabiliyor, detay sayfasına yönleniyor; anket akışın en üstünde görünüyor.
- 1 seçenek, 6 seçenek, tekrarlı seçenek ("Sinema" / "sinema"), boş soru reddediliyor ve girilen veriler kaybolmuyor.
- Ziyaretçi `/anket/yeni/`'ye girince bilgi mesajıyla giriş sayfasına gidiyor; giriş veya kayıt sonrası tekrar oluşturma formuna dönüyor.
- Kartlarda yazarın `@kullaniciadi`'sı ve "x dakika/saat önce" görünüyor.
- 11 ve üzeri anket varken sayfalama çalışıyor.
- Testler geçiyor.

---

### Faz 3 — Oylama ve sonuçlar
**Amaç:** Herkes oy verebilsin; sonuçlar sayfa yenilenmeden, animasyonla gelsin.

**Yapılacaklar**
1. `Vote` modeli + kısıtlar (Bölüm 6) + migration + admin (salt okunur liste yeterli).
2. `polls/middleware.py` → `VoterTokenMiddleware` (8.3); `MIDDLEWARE` listesine ekle.
3. `polls/services.py`: `get_existing_vote(poll, voter_token, user)`, `cast_vote(poll, option_id, voter_token, user)` (`IntegrityError` → `AlreadyVoted`), `get_results(poll)` (oy sayıları ve toplamı 100 olan yüzdeler; 8.3).
4. `vote` view: `@require_POST`; JSON / redirect ayrımı; 400 / 404 / 409 yanıtları (8.3).
5. Kart şablonu iki durumlu:
   - oy verilmemiş → her seçenek `<form method="post">` içinde `<button name="option_id" value="...">` (JS kapalıyken de çalışır),
   - oy verilmiş veya anketin sahibi → sonuç çubukları (8.4).
6. `static/js/vote.js`:
   - event delegation ile oy formlarının submit'ini yakala; tıklanan butonu `event.submitter` ile al,
   - `fetch` + `FormData` + `Accept: application/json` ile gönder (CSRF token formdaki gizli input'tan gelir),
   - istek sırasında butonları pasifleştir,
   - başarıda kartı sonuç görünümüne çevir (çubuklar 0'dan yüzdeye animasyonla dolar), toplam oyu güncelle,
   - 409'da gelen sonuçları göster + "Bu ankete zaten oy verdin" toast'ı; diğer hatalarda hata toast'ı.
7. `poll_delete` view (8.5) + JS onayı.
8. Akış sorgusunu 8.6'ya göre optimize et.
9. Testler: ziyaretçi oyu, aynı çerezle ikinci oy (409, sayı değişmez), aynı üyenin farklı çerezle ikinci oyu, başka anketin seçeneği (400), JSON yanıtta e-posta olmaması, sahibi olmayanın silememesi, akışın sabit sayıda sorguyla yüklenmesi (`assertNumQueries`).

**Kabul kriterleri**
- Ziyaretçi oy verebiliyor; sayfa yenilenmeden sonuçlar animasyonla geliyor; sayfa yenilenince de sonuç görünümü kalıyor.
- Aynı tarayıcıdan ikinci oy reddediliyor, sayılar değişmiyor.
- Üye başka bir tarayıcıdan giriş yapınca aynı ankete tekrar oy veremiyor.
- Başka bir anketin seçenek id'si gönderilince 400 dönüyor.
- JS kapalıyken oy verme normal form POST ile çalışıyor.
- Anketin sahibi sonuçları oy vermeden görüyor; sadece sahibi silebiliyor.
- Akış sayfası anket sayısından bağımsız, sabit sayıda SQL sorgusuyla yükleniyor.
- Testler geçiyor.

---

### Faz 4 — Arayüz cilası
**Amaç:** Tasarım sistemini eksiksiz uygulamak; mobil, erişilebilirlik ve küçük keyif detayları.

**Yapılacaklar**
1. Bölüm 9'u tüm sayfalara uygula; anket kartının son hali (avatar, rozetler, sonuç çubukları).
2. Ziyaretçi karşılama kartı ve boş durumlar.
3. Mesajları toast'a çevir (otomatik kapanma + kapatma butonu).
4. "Paylaş" butonu: `navigator.share` varsa onu kullan; yoksa `navigator.clipboard` ile detay linkini kopyala → "Link kopyalandı!" toast'ı.
5. Mobil: sadeleşen header, üyeler için sağ altta "+" butonu.
6. `404.html` ve `500.html` (marka diliyle, "Ana sayfaya dön" butonu).
7. `static/img/favicon.svg` (orijinal ve basit: mor zemin üzerinde beyaz "?").
8. Mikro etkileşimler + `prefers-reduced-motion`; 9.4 erişilebilirlik maddeleri.
9. Sayfa başlıkları: anket detayında "Soru metni — kararsızım", diğerlerinde "Sayfa adı — kararsızım".

**Kabul kriterleri**
- 360px, 768px ve 1280px genişliklerde yatay kaydırma yok, düzen bozulmuyor.
- Sadece klavyeyle gezinilip oy verilebiliyor; odak halkaları görünüyor.
- Chrome Lighthouse "Accessibility" skoru ≥ 90.
- Paylaş butonu mobilde paylaşım menüsünü açıyor, masaüstünde linki kopyalıyor.
- Yerelde `DEBUG=False` yapılınca özel 404 sayfası görünüyor.

---

### Faz 5 — Supabase'e geçiş
**Amaç:** Uygulamayı Supabase Postgres'e bağlamak, tabloları oluşturmak, güvenliği ayarlamak.

**Kullanıcının Supabase panelinde yapacakları** (Claude Code adım adım anlatır, şifre istemez)
1. supabase.com'da yeni proje; bölge olarak Türkiye'ye yakın **Central EU (Frankfurt)**. Veritabanı şifresini sadece harf ve rakamlardan oluşan uzun bir şifre seç (URL'de özel karakter kodlama derdi olmaz) ve güvenli bir yere kaydet.
2. Proje panelindeki **Connect** ekranından iki bağlantı adresini al:
   - **Transaction pooler** (port **6543**) → uygulamanın `DATABASE_URL`'i,
   - **Session pooler** (port **5432**) → sadece `migrate` / `createsuperuser` için.
   - Doğrudan bağlantı (`db.<proje-ref>.supabase.co`) kullanılmaz: IPv6 gerektirir ve serverless ortama uygun değildir.
3. `.env` dosyasına Transaction pooler adresini `DATABASE_URL` olarak yaz.

**Claude Code'un yapacakları**
4. Bölüm 10'daki veritabanı ayarlarının (`ssl_require`, `conn_max_age=0`, `DISABLE_SERVER_SIDE_CURSORS`) yerinde olduğunu kontrol et.
5. Migration'ları Session pooler ile çalıştırma komutlarını ver:
   ```
   # Windows (PowerShell)
   $env:DATABASE_URL="<SESSION_POOLER_URL>"; python manage.py migrate; python manage.py createsuperuser; Remove-Item Env:DATABASE_URL

   # macOS / Linux
   DATABASE_URL="<SESSION_POOLER_URL>" python manage.py migrate
   DATABASE_URL="<SESSION_POOLER_URL>" python manage.py createsuperuser
   ```
6. **Güvenlik (RLS):** Supabase, `public` şemasındaki tabloları otomatik bir REST API (Data API) üzerinden erişilebilir kılabilir. Biz bu API'yi kullanmıyoruz; Django doğrudan Postgres'e bağlanıyor. Supabase **SQL Editor**'da tüm tablolarda RLS'i aç (politika eklemeden → API üzerinden erişim kapanır; tabloların sahibi olan `postgres` kullanıcısıyla bağlanan Django etkilenmez):
   ```sql
   do $$
   declare r record;
   begin
     for r in select tablename from pg_tables where schemaname = 'public' loop
       execute format('alter table public.%I enable row level security;', r.tablename);
     end loop;
   end $$;
   ```
   Her yeni migration'dan sonra tekrar çalıştırılır (zararsızdır). Ardından **Advisors → Security** ekranında kritik uyarı kalmadığını kontrol et.
7. `python manage.py runserver` ile kayıt → anket oluşturma → oy verme akışını Supabase üzerinde test et.

**Sorun giderme**
- `prepared statement ... already exists / does not exist`: `DATABASES["default"].setdefault("OPTIONS", {})["prepare_threshold"] = None` ekle (psycopg 3'ün otomatik prepared statement'larını kapatır; transaction pooler bunları desteklemez).
- `password authentication failed`: şifrede özel karakter varsa URL-encode et veya şifreyi sıfırla.
- `Tenant or user not found`: pooler adresindeki kullanıcı adının `postgres.<proje-ref>` biçiminde olduğunu kontrol et.

**Kabul kriterleri**
- Supabase Table Editor'da `accounts_user`, `polls_poll`, `polls_option`, `polls_vote` ve Django tabloları görünüyor.
- Yerelde oluşturulan anket ve oylar Supabase'de görünüyor.
- Security Advisor'da RLS ile ilgili kritik uyarı yok.
- `.env` git'te değil; şifre hiçbir commit'te yok.

---

### Faz 6 — Vercel'e deploy
**Amaç:** Prototipi internette yayınlamak.

**Yapılacaklar**
1. `vercel.json`:
   ```json
   {
     "$schema": "https://openapi.vercel.sh/vercel.json",
     "regions": ["fra1"]
   }
   ```
   (Vercel fonksiyonunu Supabase'e yakın Frankfurt'ta çalıştırır; her istekteki veritabanı gecikmesini azaltır.)
2. Production ayarlarını kontrol et (Bölüm 10: secure cookie'ler, proxy SSL header, `STATIC_ROOT`). Build'e `collectstatic` veya `migrate` ekleme.
3. Kullanıcı kodu GitHub'a push eder.
4. vercel.com → **Add New → Project** → repo'yu import et; framework olarak Django algılanmalı.
5. Environment Variables:

   | Değişken | Değer |
   |---|---|
   | `SECRET_KEY` | yeni, uzun ve rastgele (aşağıdaki komutla üret) |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `.vercel.app` |
   | `CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app` |
   | `DATABASE_URL` | Supabase **Transaction pooler** adresi (6543) |

   ```
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
6. Deploy et.
7. ⚠️ Vercel `migrate` çalıştırmaz. Model değiştiğinde deploy'dan **önce** yerelden Session pooler ile `migrate` çalıştırılır (Faz 5, adım 5) ve RLS SQL'i tekrar çalıştırılır.

**Kabul kriterleri**
- Vercel adresinde site açılıyor; CSS, JS ve fontlar yükleniyor.
- Production'da kayıt, giriş, anket oluşturma ve oy verme çalışıyor.
- Gizli pencerede (ziyaretçi olarak) oy verilebiliyor; aynı pencerede ikinci oy reddediliyor.
- Olmayan bir adreste özel 404 sayfası görünüyor (`DEBUG=False`).
- Production'dan gelen kayıtlar Supabase Table Editor'da görünüyor.
- `python manage.py check --deploy` çıktısında kritik sorun yok (HSTS uyarıları prototipte göz ardı edilebilir).

---

## 12. İlerleme durumu

- [x] Faz 0 — Kurulum ve iskelet
- [x] Faz 1 — Kullanıcı sistemi
- [x] Faz 2 — Anket oluşturma ve akış
- [x] Faz 3 — Oylama ve sonuçlar
- [x] Faz 4 — Arayüz cilası
- [x] Faz 5 — Supabase'e geçiş
- [ ] Faz 6 — Vercel'e deploy

**Notlar / alınan kararlar** (Claude Code her faz sonunda buraya ekler)
- Faz 0: Python 3.14 + Django 5.2.18 ile kuruldu (yerel `.venv`). `accounts.User` için ek olarak `Lower(email)` ve `Lower(username)` veritabanı kısıtları eklendi (büyük/küçük harf duyarsız benzersizlik DB düzeyinde de garanti). Kullanıcı adı doğrulayıcıları (`username_format_validator`, `validate_username_not_reserved`) `accounts/models.py` içinde; Faz 1 formları bunları yeniden kullanır. `LOGIN_URL` / `LOGIN_REDIRECT_URL` / `LOGOUT_REDIRECT_URL` ayarları Faz 1'de eklenecek. Geçici ana sayfa `templates/coming_soon.html` (Faz 2'de akışla değişecek). `accounts/tests.py` içinde 8 test var.
- Faz 1: Kayıt formunda e-posta ve kullanıcı adı, doğrulamadan ÖNCE küçük harfe çevrilir (`LowercaseCharField`/`LowercaseEmailField`), böylece `Ali` yazan kullanıcıya "geçersiz" yerine `ali` olarak kayıt yapılır; benzersizlik kontrolü `iexact` ile yapılır. `?next=` değeri sadece aynı siteye gidiyorsa kabul edilir (open redirect koruması). Ziyaretçiyi mesajla giriş sayfasına yönlendiren `accounts.decorators.login_required_with_message` hazır; Faz 2'de `poll_create` bunu kullanacak. Header'daki "Anket oluştur" linki `/anket/yeni/`'ye gider (Faz 2'ye kadar 404). Mesajlar şimdilik düz kutu (Faz 4'te toast). Toplam 25 test.
- Faz 2: `Poll`/`Option` modelleri ve `PollCreateForm` hazır. Seçenekler `name="options"` ile gelir; form, hata durumunda girilen seçenekleri `form.option_values` ile geri çizer. Soru/seçenek hataları kullanıcıya Türkçe ve alanın altında gösterilir (seçenek hataları "Seçenekler" bölümünün üstünde). Geçici `coming_soon.html` kaldırıldı; `/` artık `polls:feed`. Akış 3 sabit sorguyla yüklenir (COUNT + anketler/yazar JOIN + seçenekler `prefetch_related`). Kart alt satırı `{{ poll.total_votes|default:0 }} oy` gösterir; Faz 3'te `total_votes` annotation'ı eklenince kendiliğinden dolar. Anket detay sayfasında `<title>` zaten "Soru — kararsızım" biçiminde. Global `[hidden] { display: none !important; }` kuralı eklendi (`.btn` gibi `display` veren sınıflar `hidden` attribute'unu ezmesin diye). Toplam 52 test.
- Faz 3: `Vote` modeli, `VoterTokenMiddleware` (`kz_voter` çerezi: UUID4, 1 yıl, HttpOnly, SameSite=Lax, production'da Secure), `polls/services.py` (`cast_vote`, `get_existing_vote`, `build_results`, `compute_percents`) hazır. Yüzdeler en büyük kalan yöntemiyle toplamı 100'e tamamlanır (15 ve 9 oy → 63 / 37). "önde 🔥" rozeti sadece TEK lider varken verilir (eşitlikte kimseye verilmez). JSON yanıtına şemadaki alanlara ek olarak her sonuç satırında `position` ve `is_leader` alanları var (JS rengi ve rozeti buradan kuruyor). Sonuçlar oy vermeyene sunucu tarafında HTML'e hiç yazılmaz (sadece oy butonları + toplam oy). Anketin sahibi oy vermeden sonuçları görür; satırlar oy butonu olarak çalışır, oy verince ✓ çıkar. Feed 4 sabit sorguyla yüklenir (COUNT + anketler + seçenekler + ziyaretçinin oyları); sayfalama COUNT'u oy tablosuna JOIN atmaz. Annotate'li sorgularda `Meta.ordering` yok sayıldığı için sıralama (`-created_at, -pk` ve `position`) açıkça verildi. `main.js`'e `showToast()` ve `data-confirm` onay mekanizması eklendi (Faz 4'te Django mesajları da toast'a çevrilecek). Anket silme sahibi olmayana ve ziyaretçiye 404 döner. Toplam 89 test (`polls/tests.py` + `polls/test_voting.py`).
- Faz 4: Django mesajları toast'a çevrildi (sunucu `.toasts` içinde çizer; `main.js` kapatma butonunu ve 4 sn otomatik kapanmayı bağlar, üzerine gelince/odaklanınca durur; JS kapalıyken mesajlar sayfada kalır). "Paylaş" butonu: `navigator.share` → yoksa `navigator.clipboard` → yoksa `execCommand` yedeği; URL, `data-share-path` + `location.origin` ile kurulur. Mobilde (≤640px) header'daki "Anket oluştur" gizlenir, üyeler için sağ altta "+" butonu çıkar (anket oluşturma sayfasında yok). Özel `404.html` (base'i genişletir) ve `500.html` (bağımsız sayfa; sunucu hatasında kullanıcı/oturum bilgisi güvenilir olmadığı için base kullanmaz). Başlık hiyerarşisi: detayda soru `h1`, akışta `h2`; akışta üyeler için görünmez `h1`; "İçeriğe geç" bağlantısı eklendi. **Tasarım kararı:** Sonuç çubuğunun dolgusu, metnin arkasında değil ALTINDA (kartın alt kenarında ince bir çubuk) durur; çünkü canlı renk dolgusu üzerindeki `-ink` metin WCAG AA kontrastını (4.5:1) sağlamıyordu (turuncu ve nane ~3.6:1). Metin sadece tint zemin üzerinde kalır (≥4.6:1). Logo "?" rengi aynı nedenle `--opt-1-ink` oldu. Doğrulama: axe-core (WCAG 2.0/2.1 A-AA + best-practice) 6 sayfada ihlal bulmadı; 360/768/1280px'te yatay taşma yok. Lighthouse ölçümü kullanıcıda. Toplam 105 test (`polls/test_ui.py` eklendi).
- Faz 5: Proje Supabase'de ("Kararsızım uygulaması udemy", Frankfurt, `eu-central-1`, Postgres 17). `.env`'deki `DATABASE_URL` Transaction pooler (6543) adresi; `migrate` için Session pooler adresi (5432) aynı adresten port değiştirilerek türetildi (aynı sunucu ve kimlik bilgileri, adres sohbette/log'da gösterilmedi). 13 tablo oluştu; RLS tüm `public` tablolarında açıldı (politikasız; Django tabloların sahibi `postgres` ile bağlandığı için etkilenmez). Security Advisor'da "critical" yok, kalan tek bilgi (INFO) uyarısı `rls_enabled_no_policy`: bilinçli, Data API'yi kullanmıyoruz. Her yeni migration'dan sonra RLS SQL'i yeniden çalıştırılmalı (Faz 6'daki deploy öncesi adım). `prepared statement` hatası görülmedi, `prepare_threshold` ayarı eklenmedi (hata çıkarsa eklenecek). Uçtan uca duman testi (kayıt → anket → ziyaretçi/üye oyu → ikinci oy 409 → silme) Supabase'e karşı Django test istemcisiyle çalıştırıldı, tümü başarılı; test verisi silindi. Yerel SQLite verileri taşınmadı; Supabase boş başladı. `createsuperuser` kullanıcı tarafından çalıştırılacak (parola gizli kalır).

### Faz 6'ya devir notu (oturumlar arası; 2026-10-10)

Yeni oturum bu notu okuyup Faz 6'ya buradan devam eder. **Önce Faz 6 dosya planını yaz, onay bekle** (Bölüm 0, kural 2).

**Durum**
- Git: `master`, son commit `6271fba` ("Faz 5: Supabase'e geçiş notları"), `origin/master` ile aynı; çalışma dizini temizdi. Remote: `https://github.com/serhatyazici/Kararsizim.git`. Branch adı bilinçli olarak `master` (kullanıcı tercihi).
- Faz 0–5 tamam. Toplam 105 test (Python 3.14 + Django 5.2.18, yerel `.venv`). Faz 6'ya ait kod henüz YOK: `vercel.json` ve `.python-version` oluşturulmadı.
- Supabase: proje "Kararsızım uygulaması udemy", proje kodu (`project_id`) `vddqpkxwetvexwsmhjjc`, `eu-central-1`. 13 tablo, hepsinde RLS açık, 1 süper kullanıcı var, anket/oy yok (test verileri silindi). Supabase bağlayıcısı (MCP) bağlı: `list_tables`, `get_advisors` ile salt okunur doğrulama yapılabilir.
- `.env` (git'te değil): `DATABASE_URL` = Transaction pooler (6543) ve DOLU, `DEBUG=True`, `SECRET_KEY` yerel geliştirme anahtarı. Yani yerelde `runserver` ve `manage.py test` Supabase'e bağlanır (testler ayrı bir test veritabanı açıp siler). Yerel SQLite'a dönmek için `DATABASE_URL=` satırını boşalt. **Şifreyi/adresi sohbette ASLA gösterme**; okuman gerekirse maskeleyerek oku (Faz 5'te yapıldığı gibi).
- Session pooler adresi (migrate/createsuperuser için) ayrıca saklanmaz: Transaction pooler adresinde `:6543/` → `:5432/` yapılarak türetilir.

**Faz 6'da yapılacaklar (plan kullanıcıya sunuldu; kod henüz yazılmadı)**
1. `vercel.json` (`regions: ["fra1"]`) ve `.python-version` (öneri: `3.13`; Vercel örneklerinde 3.13 geçiyor, en az 3.12 isteniyor; yerel 3.14'ten bilinçli olarak farklı). Bölüm 3'teki Python notunu buna göre güncelle. İlk deploy günlüğünde Python sürümünü doğrula.
2. `DEBUG=False` + sahte `SECRET_KEY` ile `python manage.py check --deploy` çalıştır, uyarıları raporla (HSTS uyarıları prototipte göz ardı edilir). Build'e `collectstatic` ya da `migrate` EKLEME.
3. Vercel hesabı: 2026-10-08'de Vercel bağlayıcısında `list_teams` ve `list_projects` BOŞTU (hesapta team/proje yok). Kullanıcının vercel.com'a GitHub ile girip `serhatyazici/Kararsizim` reposuna erişim vermesi gerekir; sonra `create_git_project` (zorunlu `teamId`; kişisel hesap için önce `get_auth_user` / `list_teams` sonucuna bak) veya dashboard'dan import. Vercel MCP araçlarının çoğu "deferred": `ToolSearch` ile şemasını yükle.
4. Environment Variables (Bölüm 11, Faz 6, adım 5): `SECRET_KEY` (YENİ üret, yerel anahtardan farklı; gizli ekle), `DEBUG=False`, `ALLOWED_HOSTS=.vercel.app`, `CSRF_TRUSTED_ORIGINS=https://*.vercel.app`, `DATABASE_URL` (`.env`'deki Transaction pooler adresi, göstermeden). Gizli değerler Vercel'de "sensitive" tipinde olmalı.
5. Deploy sonrası kabul kriterleri: site açılıyor, CSS/JS/fontlar yükleniyor; production'da kayıt, giriş, anket, oy; gizli pencerede ziyaretçi oyu + ikinci oy reddi; özel 404 (`DEBUG=False`); veriler Supabase'de; `check --deploy`. Test verilerini temizle. Vercel "Authentication / deployment protection" yüzünden site herkese açık değilse kullanıcıya söyle.
6. Faz sonunda `CLAUDE.md` ilerleme durumunu güncelle, elle test adımlarını ve commit mesajını yaz.

**Öğrenilen kısıtlar (aynı hataları tekrarlama)**
- Claude Code izin denetimi, Supabase `apply_migration` (RLS açma) işlemini reddetti ("paylaşılan kaynağı değiştirme"); kullanıcı SQL'i SQL Editor'da kendisi çalıştırdı. Vercel'de proje/env oluşturma da reddedilebilir: reddedilirse aynı sonucu başka araçla DOLANMA, kullanıcıya dashboard adımını ver.
- Tarayıcı bölmesi bir ara `127.0.0.1:8000`'e gitmeyi reddetti; o durumda Django test istemcisiyle (`django.test.Client`) uçtan uca doğrulama yapıldı. Bölme ekran görüntüsü çizmiyor; `javascript_tool` ile ölçüm yapılabilir. Production URL'sini tarayıcı bölmesinde açmak ayrıca izin isteyebilir.
- Windows: heredoc içeren `python - <<'EOF'` bazen kabuk hatası veriyor, uzun dosyaları `Write` ile yaz. Konsol çıktısında Türkçe karakter için `PYTHONIOENCODING=utf-8` kullan. `.venv\Scripts\python.exe` ile çalış.
- Model değişirse: deploy'dan ÖNCE Session pooler ile `migrate` + RLS SQL'i (Faz 5, adım 5–6). Vercel `migrate` çalıştırmaz.
- Faz 4 notu: Lighthouse ölçümü kullanıcıda (benim çalıştıramadığım tek kabul kriteri).

**Kullanıcı tercihleri (bu oturumdan)**
- Türkçe, adım adım ve ayrıntılı anlat (kullanıcı Django ve panelleri öğreniyor); "burayı daha detaylı anlat" dediğinde ekranda ne göreceğini de yaz.
- Bağlı bir MCP aracı bir işi yapabiliyorsa kullanıcıya elle yaptırma, kendin yap; sadece parola gibi yalnızca kullanıcıda olan sırları ve izin denetiminin reddettiklerini ona bırak.
- Commit/push'u kullanıcı "yap/commitle/pushla" dediğinde ben yapıyorum (commit mesajı Türkçe, `Co-Authored-By` satırıyla). Dosya planını yazıp onay bekle; kullanıcı "başla/tamam" der.

---

## 13. Yol haritası (prototipten sonra)

- Oyu değiştirme / geri alma
- Süreli anketler (bitiş zamanı, "Sona erdi" rozeti)
- Akış sekmeleri: En yeni / Popüler / Bitmek üzere
- Profil sayfası `/u/<kullaniciadi>/` ve "Anketlerim"
- Şifre sıfırlama (e-posta gönderim servisi gerekir)
- Kötüye kullanım önlemleri: rate limiting, raporlama, kelime filtresi, daha sıkı tekrar oy kontrolü
- Kategoriler / etiketler ve arama
- Yorumlar
- Open Graph meta etiketleri (paylaşılan linkte önizleme kartı)
- Karanlık mod, PWA

---

## 14. Faz promptları (kullanıcının Claude Code'a yapıştıracağı metinler)

**Faz 0 (ilk oturum):**
```
CLAUDE.md dosyasını baştan sona oku. Bugün sadece Faz 0'ı yapacağız.
Önce oluşturacağın ve değiştireceğin dosyaları sırasıyla kısa bir liste halinde yaz ve onayımı bekle.
Onaydan sonra uygula. Bitince kabul kriterlerini tek tek kontrol et, İlerleme durumu bölümünü güncelle,
tarayıcıda nasıl test edeceğimi adım adım yaz ve bir commit mesajı öner. Faz 1'e geçme.
```

**Faz 1–4 (N yerine faz numarasını yaz):**
```
Faz N'e geçiyoruz. CLAUDE.md'de Faz N'i ve ilgili veri modeli, iş kuralları ve tasarım bölümlerini tekrar oku.
Önce dosya planını yaz ve onayımı bekle. Uygularken yeni bir Django kavramı kullandığında bana kısaca açıkla.
Bitince testleri çalıştır, kabul kriterlerini tek tek doğrula, İlerleme durumu'nu güncelle,
elle test adımlarını ve commit mesajını yaz. Sonraki faza geçme.
```

**Faz 5:**
```
Faz 5'e geçiyoruz: Supabase. Önce Supabase panelinde yapmam gerekenleri adım adım anlat.
Bağlantı adreslerini ve şifreyi .env dosyasına ben yazacağım, bana şifre sorma.
Sonra migrate, RLS ve test adımlarını birlikte yapalım. Bitince kabul kriterlerini doğrula ve İlerleme durumu'nu güncelle.
```

**Faz 6:**
```
Faz 6'ya geçiyoruz: Vercel deploy. Gerekli dosyaları hazırla ve production ayarlarını kontrol et.
Sonra Vercel panelinde yapmam gerekenleri ve girmem gereken environment variable'ları adım adım listele.
Deploy sonrası kabul kriterlerini birlikte kontrol edelim.
```

**Hata aldığında:**
```
Şu hatayı alıyorum: <hata mesajını ve o sırada ne yaptığımı buraya yapıştır>
Önce nedenini açıkla, sonra düzelt ve hangi dosyada neyi değiştirdiğini söyle.
```

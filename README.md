# django-sivuvahti

Django-laajennos avoinna olevien sivujen seuraamiseen


Asennus:
=======

Asenna paketti:

```bash
pip install django-sivuvahti
```

Tee ASGI-määritys ja tarvittavat muutokset Django-asetuksiin `django-pistoke`-
paketin asennusohjeiden mukaisesti.

Lisää `sivuvahti` asennettuihin sovelluksiin:
```python
# projektin_asetukset.py

INSTALLED_APPS = [
  ...
  'sivuvahti',
]
```

Lisää sivuvahti URL-osoitteistoon:
```python
# projektin_osoitteisto.py

from sivuvahti import Sivuvahti

urlpatterns = [
  ...
  path("sivuvahti", Sivuvahti.as_view(), name="sivuvahti")
]

Lisää Javascript-komentosarja:
```html
<!-- sivu.html -->

<head>
  ...
  <script
    type="text/javascript"
    src="{% static "sivuvahti/js/sivuvahti.js" %}"
    data-url="{{ request.websocket }}{% url "sivuvahti" %}"
    data-csrf="{{ csrf_token }}"
    ></script>
</head>
```


Käyttö:
======

Alusta sivuvahti sivun avaamisen yhteydessä:
```javascript
let sivuvahti = new Sivuvahti(location.pathname);
```

Kuuntele saapuvia ja poistuvia käyttäjiä:
```javascript
document.addEventListener(
  "sivuvahti.saapuvaKayttaja",
  function (e) {
    alert(`Saapuva käyttäjä: ${e.detail.nimi}`);
  }
);
document.addEventListener(
  "sivuvahti.poistuvaKayttaja",
  function (e) {
    alert(`Poistuva käyttäjä: ${e.detail.nimi}`);
  }
);
```

Reagoi tarvittaessa yhteyden avaamiseen tai katkaisuun:
```javascript
document.addEventListener(
  "sivuvahti.yhteysAvattu",
  function (e) {
    console.log("Sivuvahti avattu");
  }
);
document.addEventListener(
  "sivuvahti.yhteysKatkaistu",
  function (e) {
    console.log("Sivuvahti suljettu");
  }
);
```

Sulje yhteys tarvittaessa:
```javascript
sivuvahti.sulje();
```

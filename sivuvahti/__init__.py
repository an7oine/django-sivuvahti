import asyncio
from dataclasses import dataclass
import uuid

from django.utils.decorators import method_decorator

from pistoke.nakyma import WebsocketNakyma
from pistoke.protokolla import WebsocketProtokolla
from pistoke.tyokalut import CsrfKattely, JsonLiikenne

from viestikanava import Viestikanava


def _kayttajan_oletustiedot(request):
  return {
    'id': request.user.pk,
    'nimi': str(request.user),
  }
  # def _kayttajan_oletustiedot


@dataclass
class Sivuvahti(WebsocketNakyma):
  '''
  Luokkapohjainen näkymä, joka välittää Celery-viestikanavan kautta samalla
  sivulla (request.GET['sivu']) auki oleville istunnoille tiedon toisistaan
  ja näihin istuntoihin liittyvistä käyttäjistä.

  >>> from sivuvahti import Sivuvahti
  >>> urlpatterns = [
  ...    path('sivuvahti', Sivuvahti.as_view(
  ...      kayttajan_tiedot=lambda request: {
  ...        'id': request.user.pk,
  ...        'nimi': request.user.first_name,
  ...      }
  ...    ), name='sivuvahti'),
  ... ]
  '''

  kayttajan_tiedot: callable = _kayttajan_oletustiedot

  @method_decorator(WebsocketProtokolla)
  @method_decorator(JsonLiikenne)
  @method_decorator(
    CsrfKattely(csrf_avain='csrfmiddlewaretoken', virhe_avain='virhe')
  )
  async def websocket(self, request):

    itse = {
      'uuid': str(uuid.uuid4()),
      'kayttaja': self.kayttajan_tiedot(request),
    }
    muut = {}

    async with Viestikanava(
      kanava='sivuvahti',
      alikanava=request.GET['sivu'],
    ) as kanava:
      await kanava.kirjoita(itse)
      try:
        async for viesti in kanava:
          saapuva_uuid = viesti['uuid']
          if saapuva_uuid == itse['uuid']:
            pass
          elif viesti.get('tila') == 'poistuu':
            if kayttaja := muut.pop(saapuva_uuid, None):
              await request.send({'poistuva_kayttaja': kayttaja})
          elif saapuva_uuid not in muut:
            kayttaja = muut[saapuva_uuid] = viesti['kayttaja']
            await request.send({'saapuva_kayttaja': kayttaja})
            # Ilmoittaudutaan uudelle saapujalle.
            await kanava.kirjoita(itse)
            # elif saapuva_uuid not in muut
          # while True
        # try
      finally:
        await kanava.kirjoita(**itse, tila='poistuu')
      # async with Viestikanava

    # async def websocket

  # class Sivuvahti

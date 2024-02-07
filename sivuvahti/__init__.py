import asyncio
import uuid

from django.urls import path
from django.views.decorators.http import require_http_methods

from pistoke.protokolla import WebsocketProtokolla
from pistoke.tyokalut import CsrfKattely, JsonLiikenne

from viestikanava import Viestikanava


def kayttajan_tiedot(request):
  return {
    'id': request.user.pk,
    'nimi': str(request.user),
  }
  # def kayttajan_tiedot


@require_http_methods(('Websocket', ))
@WebsocketProtokolla
@JsonLiikenne
@CsrfKattely(csrf_avain='csrfmiddlewaretoken', virhe_avain='virhe')
async def sivuvahti(request):

  itse = {
    'uuid': str(uuid.uuid4()),
    'kayttaja': kayttajan_tiedot(request),
  }
  muut = {}

  async with Viestikanava(
    kanava='sivuvahti',
    alikanava=request.GET['sivu'],
  ) as kanava:
    await kanava.kirjoita(**itse)
    try:
      while True:
        viesti = await kanava.lue()
        saapuva_uuid = viesti['uuid']
        if saapuva_uuid == itse['uuid']:
          pass
        elif viesti.get('tila') == 'poistuu':
          try:
            kayttaja = muut.pop(saapuva_uuid)
          except KeyError:
            pass
          else:
            await request.send({'poistuva_kayttaja': kayttaja})
        elif saapuva_uuid not in muut:
          kayttaja = muut[saapuva_uuid] = viesti['kayttaja']
          await request.send({'saapuva_kayttaja': kayttaja})
          # Ilmoittaudutaan uudelle saapujalle.
          await kanava.kirjoita(**itse)
          # elif saapuva_uuid not in muut
        # while True
      # try
    finally:
      await kanava.kirjoita(**itse, tila='poistuu')
    # async with Viestikanava

  # async def sivuvahti


app_name = 'sivuvahti'
urlpatterns = [
  path('', sivuvahti, name='sivuvahti')
]

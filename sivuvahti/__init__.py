import asyncio
import uuid

from django.urls import path
from django.views.decorators.http import require_http_methods

from pistoke.protokolla import WebsocketProtokolla
from pistoke.tyokalut import CsrfKattely, JsonLiikenne

from .celery import CeleryViestikanava


celery_viestikanava = CeleryViestikanava('sivuvahti')


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

  loop = asyncio.get_running_loop()

  sivu = request.GET['sivu']
  kayttaja = kayttajan_tiedot(request)

  itse = str(uuid.uuid4())
  muut = {}

  def laheta_omat_tiedot(paattyy=False):
    celery_viestikanava.laheta_viesti(
      sivu,
      uuid=itse,
      kayttaja=kayttaja,
      **({'tila': 'poistuu'} if paattyy else {}),
    )
    # def laheta_omat_tiedot

  async def _saapuva_celery_viesti(viesti: dict):
    saapuva_uuid = viesti['uuid']
    if saapuva_uuid == itse:
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
      # Ilmoittaudu pienellä viiveellä, että tulokas ehtii
      # ottaa sanoman vastaan.
      await asyncio.sleep(0.01)
      laheta_omat_tiedot()
    # async def _saapuva_celery_viesti

  def saapuva_celery_viesti(viesti: dict):
    tulos = asyncio.run_coroutine_threadsafe(
      _saapuva_celery_viesti(viesti),
      loop
    )
    tulos.result(0.1)
    # def saapuva_celery_viesti

  celery_viestikanava.lisaa_vastaanottaja(
    sivu,
    saapuva_celery_viesti
  )

  with celery_viestikanava:
    # Lähetetään tieto istunnon alkamisesta.
    laheta_omat_tiedot()

    try:
      while True:
        await asyncio.sleep(3600)
    finally:
      celery_viestikanava.poista_vastaanottaja(
        sivu,
        saapuva_celery_viesti
      )
      laheta_omat_tiedot(paattyy=True)
      # finally
    # with celery_viestikanava

  # async def sivuvahti


app_name = 'sivuvahti'
urlpatterns = [
  path('', sivuvahti, name='sivuvahti')
]

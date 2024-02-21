# pylint: disable=invalid-name

import asyncio
from collections import defaultdict
import functools
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django import forms
from django.template import loader
from django.test import SimpleTestCase
from django.test.utils import override_settings
from django.urls import path

from pistoke.testaus import WebsocketPaate
from sivuvahti import Sivuvahti
from viestikanava import Viestikanava


urlpatterns = [
  path('oletusarvot', Sivuvahti.as_view(), name='oletusarvot'),
  path('mukautettu', Sivuvahti.as_view(
    kayttajan_tiedot=lambda request: {
      'kokonimi': f'Tohtori {request.user.username.capitalize()}'
    }
  ), name='mukautettu'),
]


@functools.wraps(Viestikanava, updated=())
class _Viestikanava(Viestikanava):
  '''
  Paikallinen Celery-vastine: kaiuta viestit saman kanava/alikanava-parin
  sisällä kaikille olioille.
  '''
  jonot = defaultdict(
    functools.partial(defaultdict, asyncio.Queue)
  )

  def __post_init__(self):
    ''' Ohitetaan super. '''
    # pylint: disable=attribute-defined-outside-init
    self.jono_avain = (self.kanava, self.alikanava)

  async def __aenter__(self):
    ''' Alustetaan käytetty jono. '''
    # pylint: disable=expression-not-assigned
    self.jonot[self.jono_avain][id(self)]
    return self

  async def __aexit__(self, *args):
    ''' Poistetaan tämä olio jonosta. '''
    self.jonot[self.jono_avain].pop(id(self))

  async def kirjoita(self, *args, **kwargs):
    ''' Välitetään viesti muille saman jonon olioille. '''
    for jono in self.jonot[self.jono_avain].values():
      await jono.put(dict(*args, **kwargs))

  async def lue(self):
    ''' Poimitaan viestit jonosta. '''
    return await self.jonot[self.jono_avain][id(self)].get()

  # class _Viestikanava


@patch('sivuvahti.Viestikanava', _Viestikanava)
@override_settings(
  ROOT_URLCONF=__name__,
)
class Testi(SimpleTestCase):

  async_client_class = WebsocketPaate

  # Kiinteät käyttäjät; ei käytetä tietokantataulua.
  kayttajat = {
    pk: get_user_model()(pk=pk, username=f'kayttaja_{pk}')
    for pk in range(1, 4)
  }

  @patch('django.contrib.auth.base_user.AbstractBaseUser.save')
  def setUp(self, __mock):
    ''' Luo asynkroninen pääte kullekin käyttäjälle. '''
    super().setUp()
    def luo_yhteydet():
      for pk, kayttaja in self.kayttajat.items():
        yhteys = self.async_client_class()
        yhteys.force_login(kayttaja)
        yield (pk, yhteys)
    self.yhteydet = dict(luo_yhteydet())
    # def setUp

  @patch('django.contrib.auth.backends.BaseBackend.get_user', kayttajat.get)
  async def testaa_oletusarvot(self):
    ''' Toimiiko oletusarvoinen sivuvahti virheittä? '''

    async def kayttaja_1():
      ''' Käyttäjä 1 saapuu heti ja poistuu heti 2:n poistuttua. '''
      async with self.yhteydet[1].websocket(
        '/oletusarvot?sivu=testi'
      ) as kayttaja_1:
        await kayttaja_1.send('{"csrfmiddlewaretoken": "csrf"}')
        self.assertEqual(
          await kayttaja_1.receive(),
          '{"saapuva_kayttaja": {"id": 2, "nimi": "kayttaja_2"}}'
        )
        self.assertEqual(
          await kayttaja_1.receive(),
          '{"saapuva_kayttaja": {"id": 3, "nimi": "kayttaja_3"}}'
        )
        self.assertEqual(
          await kayttaja_1.receive(),
          '{"poistuva_kayttaja": {"id": 2, "nimi": "kayttaja_2"}}'
        )
        # async with self.async_client.websocket

    async def kayttaja_2():
      ''' Käyttäjä 2 saapuu viiveellä ja poistuu hetken kuluttua. '''
      await asyncio.sleep(0.01)
      async with self.yhteydet[2].websocket(
        '/oletusarvot?sivu=testi'
      ) as kayttaja_2:
        await kayttaja_2.send('{"csrfmiddlewaretoken": "csrf"}')
        self.assertEqual(
          await kayttaja_2.receive(),
          '{"saapuva_kayttaja": {"id": 1, "nimi": "kayttaja_1"}}'
        )
        await asyncio.sleep(0.02)
        self.assertEqual(
          await kayttaja_2.receive(),
          '{"saapuva_kayttaja": {"id": 3, "nimi": "kayttaja_3"}}'
        )
        # async with self.async_client.websocket
      # async def kayttaja_2

    async def kayttaja_3():
      ''' Käyttäjä 3 saapuu viiveellä ja odottaa muiden poistumista. '''
      await asyncio.sleep(0.02)
      async with self.yhteydet[3].websocket(
        '/oletusarvot?sivu=testi'
      ) as kayttaja_3:
        await kayttaja_3.send('{"csrfmiddlewaretoken": "csrf"}')
        self.assertEqual(
          await kayttaja_3.receive(),
          '{"saapuva_kayttaja": {"id": 1, "nimi": "kayttaja_1"}}'
        )
        self.assertEqual(
          await kayttaja_3.receive(),
          '{"saapuva_kayttaja": {"id": 2, "nimi": "kayttaja_2"}}'
        )
        self.assertEqual(
          await kayttaja_3.receive(),
          '{"poistuva_kayttaja": {"id": 2, "nimi": "kayttaja_2"}}'
        )
        self.assertEqual(
          await kayttaja_3.receive(),
          '{"poistuva_kayttaja": {"id": 1, "nimi": "kayttaja_1"}}'
        )
        # async with self.async_client.websocket
      # async def kayttaja_3

    await asyncio.gather(
      asyncio.wait_for(kayttaja_1(), timeout=0.1),
      asyncio.wait_for(kayttaja_2(), timeout=0.1),
      asyncio.wait_for(kayttaja_3(), timeout=0.1),
    )
    # async def testaa_oletusarvot

  @patch('django.contrib.auth.backends.BaseBackend.get_user', kayttajat.get)
  async def testaa_mukautettu(self):
    ''' Toimiiko sivuvahti virheittä mukautetuin käyttäjätiedoin? '''

    async def kayttaja_1():
      ''' Käyttäjä 1 saapuu heti ja odottaa käyttäjää 2. '''
      async with self.yhteydet[1].websocket(
        '/mukautettu?sivu=testi'
      ) as kayttaja_1:
        await kayttaja_1.send('{"csrfmiddlewaretoken": "csrf"}')
        self.assertEqual(
          await kayttaja_1.receive(),
          '{"saapuva_kayttaja": {"kokonimi": "Tohtori Kayttaja_2"}}'
        )
        self.assertEqual(
          await kayttaja_1.receive(),
          '{"poistuva_kayttaja": {"kokonimi": "Tohtori Kayttaja_2"}}'
        )
        # async with self.async_client.websocket

    async def kayttaja_2():
      ''' Käyttäjä 2 saapuu ja poistuu heti. '''
      async with self.yhteydet[2].websocket(
        '/mukautettu?sivu=testi'
      ) as kayttaja_2:
        await kayttaja_2.send('{"csrfmiddlewaretoken": "csrf"}')
        self.assertEqual(
          await kayttaja_2.receive(),
          '{"saapuva_kayttaja": {"kokonimi": "Tohtori Kayttaja_1"}}'
        )
        # async with self.async_client.websocket
      # async def kayttaja_2

    await asyncio.gather(
      asyncio.wait_for(kayttaja_1(), timeout=0.1),
      asyncio.wait_for(kayttaja_2(), timeout=0.1),
    )
    # async def testaa_mukautettu

  # class Testi

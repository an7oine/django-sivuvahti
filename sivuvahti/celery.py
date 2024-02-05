import asyncio
import threading

from celery.app import app_or_default


class CeleryViestikanava:

  sovellus = app_or_default()

  def __init__(self, kanava):
    super().__init__()
    self.kanava = kanava
    channel = self.sovellus.broker_connection().channel()
    self.dispatcher = self.sovellus.events.Dispatcher(
      channel=channel
    )
    self._lukko = threading.Lock()
    self._vastaanottajat = {}

    self._receiver = self.sovellus.events.Receiver(
      channel=channel,
      handlers={
        self.kanava: self.saapuva_viesti
      }
    )
    self._kaynnissa = 0
    # def __init__

  def __enter__(self):
    if self._kaynnissa <= 0:
      loop = asyncio.get_running_loop()
      self._receiver.should_stop = False
      self._luku = loop.run_in_executor(
        None,
        self._receiver.capture
      )
    self._kaynnissa += 1
    # def __enter__

  def __exit__(self, *args):
    self._kaynnissa -= 1
    if self._kaynnissa <= 0:
      self._receiver.should_stop = True
    # def __exit__

  def saapuva_viesti(self, viesti):
    with self._lukko:
      vastaanottajat = set(self._vastaanottajat.get(
        viesti['alikanava'], set()
      ))
    for vastaanottaja in vastaanottajat:
      vastaanottaja(viesti)
      # for vastaanottaja in vastaanottajat
    # def saapuva_viesti

  def laheta_viesti(self, alikanava, **viesti):
    self.dispatcher.send(
      type=self.kanava,
      alikanava=alikanava,
      **viesti
    )
    # def laheta_viesti

  def lisaa_vastaanottaja(self, alikanava, vastaanottaja):
    with self._lukko:
      self._vastaanottajat.setdefault(
        alikanava, set()
      ).add(vastaanottaja)
    # def lisaa_vastaanottaja

  def poista_vastaanottaja(self, alikanava, vastaanottaja):
    with self._lukko:
      self._vastaanottajat.get(
        alikanava, set()
      ).remove(vastaanottaja)
    # def poista_vastaanottaja

  # class CeleryViestikanava

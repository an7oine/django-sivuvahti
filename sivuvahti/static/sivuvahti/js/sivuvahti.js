"use strict";

(function () {
  const {url, csrf} = document.currentScript.dataset;

  function Sivuvahti (sivu) {
    this.websocket = new WebSocket(url + `?sivu=${sivu}`);
    Object.assign(this.websocket, {
      onopen: function (e) {
        e.target.send(JSON.stringify({
          csrfmiddlewaretoken: csrf
        }));
        document.dispatchEvent(
          new Event("sivuvahti.yhteysAvattu")
        );
      },
      onmessage: function (e) {
        let data = JSON.parse(e.data);
        if (data.saapuva_kayttaja)
          document.dispatchEvent(
            new CustomEvent(
              "sivuvahti.saapuvaKayttaja",
              {detail: data.saapuva_kayttaja}
            )
          );
        else if (data.poistuva_kayttaja)
          document.dispatchEvent(
            new CustomEvent(
              "sivuvahti.poistuvaKayttaja",
              {detail: data.poistuva_kayttaja}
            )
          );
      },
      onclose: function (e) {
        document.dispatchEvent(
          new Event("sivuvahti.yhteysKatkaistu")
        );
      }
    });
  }
  Sivuvahti.prototype.sulje = function () {
    this.websocket.close();
  }

  window.Sivuvahti = Sivuvahti;
})();

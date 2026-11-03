import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import requests
from src.lab_outlook import BUZON, BASE, DESDE, HASTA, SesionDemo, respuesta
from src.outlook_lectura import informe_nuevo, recopilar, correo_resumen, rango, segmento, propuesta_cita
from src.outlook_acciones import validar_cita, validar_correo, ejecutar, adjunto_pequeno
from src.utils.outlook_client import ClienteOutlook
from src.utils.graph_client import ErrorGraph
from ejercicio_resuelto.preparar_tareas_outlook import cargar_responsables, enriquecer

ROOT = Path(__file__).resolve().parents[1]

def cliente():
    g = ClienteOutlook(SimpleNamespace(graph_api_url=BASE, timeout_seconds=15), lambda: "TOKEN_FICTICIO")
    g.sesion.close()
    g.sesion = SesionDemo()
    return g

def lectura(max_paginas=100):
    informe = informe_nuevo(BUZON, DESDE, HASTA)
    with cliente() as g:
        recopilar(g, informe, 2, max_paginas)
    return informe

class Pruebas(unittest.TestCase):
    def test_completa(self):
        i = lectura()
        self.assertEqual(i["resultado"], "ok")
        self.assertEqual([len(i["colecciones"][x]["elementos"]) for x in ["mensajes","eventos"]], [4,3])
        self.assertEqual(len(i["propuestas"]), 5)
        self.assertEqual(len({p["clave"] for p in i["propuestas"]}), 5)
        self.assertNotIn("EVT-3", [p["origen_id"] for p in i["propuestas"]])

    def test_incompleta(self):
        i = lectura(1)
        self.assertEqual(i["resultado"], "parcial")
        self.assertEqual(len(i["propuestas"]), 4)
        self.assertTrue(all(p["estado"] == "origen_incompleto" for p in i["propuestas"]))

    def test_preparacion(self):
        tabla = cargar_responsables(ROOT / "datos/responsables_tema6_demo.csv")
        filas = enriquecer(lectura()["propuestas"], tabla)
        self.assertEqual(sum(f["estado"] == "listo_para_revision" for f in filas), 3)
        self.assertEqual(sum(f["estado"] == "sin_responsable_verificado" for f in filas), 2)

    def test_incompleto_no_se_habilita(self):
        tabla = cargar_responsables(ROOT / "datos/responsables_tema6_demo.csv")
        filas = enriquecer(lectura(1)["propuestas"], tabla)
        self.assertTrue(all(f["estado"] == "origen_incompleto" for f in filas))

    def test_ambiguo(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "responsables.csv"
            p.write_text("caso;user_id;estado\nFIN-001;00000000-0000-4000-8000-000000000011;listo\nFIN-001;00000000-0000-4000-8000-000000000012;listo\n")
            with self.assertRaises(ValueError):
                cargar_responsables(p)

    def test_html(self):
        i = lectura()
        i["propuestas"][0]["titulo"] = "<revisar & confirmar>"
        correo = correo_resumen(i, "test@example.org")
        self.assertIn("&lt;revisar &amp; confirmar&gt;", correo["message"]["body"]["content"])

    def test_rango_y_segmento(self):
        self.assertEqual(rango("2026-10-06T00:00:00+02:00","2026-10-07T00:00:00+02:00"), (DESDE,HASTA))
        with self.assertRaises(ValueError):
            rango("2026-10-06T00:00:00","2026-10-07T00:00:00")
        self.assertEqual(segmento("AA/+=="), "AA%2F%2B%3D%3D")

    def test_cita(self):
        p = propuesta_cita(lectura())
        validar_cita(p, crear=True)
        p["end"] = p["start"]
        with self.assertRaises(ValueError):
            validar_cita(p, crear=True)

    def test_destinatario(self):
        p = correo_resumen(lectura(), "test@example.org")
        validar_correo(p, "test@example.org")
        with self.assertRaises(ValueError):
            validar_correo(p, "otro@example.org")

    def test_retry_after_conserva_primera_pagina(self):
        with cliente() as g:
            original = g.sesion.request
            def solicitar(m, url, **kwargs):
                if url.endswith("/demo/mensajes2"):
                    r = respuesta({"error":{"code":"TooManyRequests"}})
                    r.status_code = 429
                    r.headers["Retry-After"] = "120"
                    return r
                return original(m, url, **kwargs)
            g.sesion.request = solicitar
            r = g.listar(f"/users/{BUZON}/mailFolders/inbox/messages")
            self.assertFalse(r["completo"])
            self.assertEqual(len(r["elementos"]), 2)
            self.assertEqual(r["error"]["codigo"], "reintento_aplazado")

    def test_envio_timeout_no_reintenta(self):
        with cliente() as g:
            with patch.object(g.sesion, "request", side_effect=requests.Timeout) as request:
                with self.assertRaises(ErrorGraph) as ctx:
                    g.escribir("POST", f"/users/{BUZON}/sendMail", {}, (202,))
                self.assertTrue(ctx.exception.incierto)
                self.assertEqual(request.call_count, 1)

    def test_202_sin_cuerpo(self):
        with cliente() as g:
            r = requests.Response()
            r.status_code = 202
            r._content = b""
            with patch.object(g.sesion,"request",return_value=r):
                self.assertIsNone(g.escribir("POST",f"/users/{BUZON}/sendMail",{},(202,)))

    def test_url_externa_rechazada(self):
        with cliente() as g:
            with self.assertRaises(ErrorGraph):
                g.url_segura("https://example.org/v1.0/users")

    def test_adjunto(self):
        import base64
        p = ROOT / "datos/nota_tema6.txt"
        self.assertEqual(base64.b64decode(adjunto_pequeno(p)["contentBytes"]), p.read_bytes())

    def test_simulacion_no_escribe(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "correo.json"
            p.write_text(json.dumps(correo_resumen(lectura(), "test@example.org")))
            with cliente() as g:
                with patch.object(g, "escribir") as escribir:
                    r = ejecutar(g, BUZON, SimpleNamespace(operacion="enviar-correo", archivo=str(p), aplicar=False), Path(tmp), "test@example.org")
                    self.assertEqual(r["estado"], "simulado")
                    escribir.assert_not_called()

if __name__ == "__main__":
    unittest.main()

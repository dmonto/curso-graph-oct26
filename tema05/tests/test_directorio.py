import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import contextmanager
import requests
from src.utils.graph_client import ClienteGraph, ErrorGraph
from src.directorio import literal_odata, preparar_responsables, resolver_usuario
from v01_endpoints import main as endpoints

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("solucion", ROOT/"ejercicio_resuelto/main.py")
solucion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(solucion)

def respuesta(status, data, retry=None):
    r = Mock()
    r.status_code = status
    r.headers = {} if retry is None else {"Retry-After":str(retry)}
    r.json.return_value = data
    return r

class Pruebas(unittest.TestCase):
    def cliente(self):
        c = ClienteGraph(SimpleNamespace(graph_api_url="https://graph.microsoft.com/v1.0", timeout_seconds=15), lambda:"FICTICIO")
        self.addCleanup(c.sesion.close)
        return c

    def test_paginacion_y_parametros(self):
        g=self.cliente()
        g.sesion.request=Mock(side_effect=[
            respuesta(200, {"value":[{"id":"a"}],"@odata.nextLink":"https://graph.microsoft.com/v1.0/users?$skiptoken=x"}),
            respuesta(200, {"value":[{"id":"b"}]})])
        r=g.listar("/users",params={"$top":"1"})
        self.assertTrue(r["completo"])
        self.assertEqual(r["paginas"],2)
        self.assertEqual(
            g.sesion.request.call_args_list[0].kwargs["headers"]["Authorization"],
            "Bearer FICTICIO",
        )
        self.assertIsNone(g.sesion.request.call_args_list[1].kwargs["params"])

    def test_members_carga_group_id_desde_configuracion(self):
        group_id = "d1b8e029-df4f-4023-aa45-d0795fbf167b"
        graph = Mock()
        graph.listar.return_value = {"completo": True, "elementos": [], "error": None}

        @contextmanager
        def conectar():
            yield graph

        def leer_config(validar_identidad):
            self.assertFalse(validar_identidad)
            os.environ["GROUP_ID"] = group_id

        with patch.dict(os.environ, {"GROUP_ID": ""}), \
                patch("sys.argv", ["main.py", "--recurso", "members"]), \
                patch.object(endpoints, "leer_config", side_effect=leer_config), \
                patch.object(endpoints, "conectar", conectar), \
                patch.object(endpoints, "mostrar"):
            self.assertEqual(endpoints.main(), 0)

        graph.listar.assert_called_once_with(
            f"/groups/{group_id}/members",
            params={"$select": "id,displayName"},
        )

    def test_limite_conserva_pagina(self):
        g=self.cliente()
        g.peticion=Mock(return_value={"value":[{"id":"a"}],"@odata.nextLink":"https://graph.microsoft.com/v1.0/users?$skiptoken=x"})
        r=g.listar("/users",max_paginas=1)
        self.assertFalse(r["completo"])
        self.assertEqual(r["error"]["codigo"],"limite_paginas")
        self.assertEqual(len(r["elementos"]),1)

    def test_nextlink_no_envia_token_fuera(self):
        g=self.cliente()
        g.sesion.request=Mock(return_value=respuesta(200,{"value":[{"id":"a"}],"@odata.nextLink":"https://example.invalid/v1.0/users"}))
        r=g.listar("/users")
        self.assertEqual(r["error"]["codigo"],"enlace_no_permitido")
        self.assertEqual(g.sesion.request.call_count,1)

    def test_reintento_y_presupuesto(self):
        for status in (429,503):
            g=self.cliente()
            g.sesion.request=Mock(side_effect=[respuesta(status,{"error":{"code":"limit"}},1),respuesta(200,{"value":[]})])
            with patch("src.utils.graph_client.time.sleep") as wait:
                g.peticion("GET","/users")
                wait.assert_called_once_with(1.0)
        g=self.cliente()
        g.sesion.request=Mock(return_value=respuesta(429,{"error":{"code":"limit"}},120))
        with patch("src.utils.graph_client.time.sleep") as wait:
            with self.assertRaises(ErrorGraph) as ex:
                g.peticion("GET","/users")
            self.assertEqual(ex.exception.codigo,"reintento_aplazado")
            wait.assert_not_called()
            self.assertEqual(g.sesion.request.call_count,1)

    def test_escritura_incierta_sin_reintento(self):
        g=self.cliente()
        g.sesion.request=Mock(side_effect=requests.Timeout())
        with self.assertRaises(ErrorGraph) as ex:
            g.peticion("PATCH","/users/id",cuerpo={"department":"Financiero"})
        self.assertTrue(ex.exception.incierto)
        self.assertEqual(g.sesion.request.call_count,1)

    def test_odata_y_ambiguedad(self):
        self.assertEqual(literal_odata("O'Brien"),"'O''Brien'")
        g=Mock()
        g.listar.return_value={"elementos":[{"id":"a"},{"id":"b"}],"completo":True,"error":None}
        with self.assertRaises(ErrorGraph):
            resolver_usuario(g,"u@example.invalid")

    def test_resolver_grupo_por_email_exacto(self):
        grupo={"id":"g","mail":"oficina.getafe@cashdiplo.es"}
        graph=Mock()
        graph.listar.return_value={"elementos":[grupo],"completo":True,"error":None}

        self.assertEqual(
            solucion.resolver_grupo(graph," oficina.getafe@cashdiplo.es "),
            grupo,
        )
        graph.listar.assert_called_once_with(
            "/groups",
            params={
                "$filter":"mail eq 'oficina.getafe@cashdiplo.es'",
                "$select":solucion.CAMPOS_GRUPO,
                "$top":"2",
            },
            max_paginas=1,
        )

        graph.listar.return_value={"elementos":[],"completo":True,"error":None}
        with self.assertRaises(ErrorGraph) as ex:
            solucion.resolver_grupo(graph,"ausente@example.invalid")
        self.assertEqual(ex.exception.codigo,"grupo_no_encontrado")

        graph.listar.return_value={
            "elementos":[grupo,dict(grupo)],
            "completo":True,
            "error":None,
        }
        with self.assertRaises(ErrorGraph) as ex:
            solucion.resolver_grupo(graph,"oficina.getafe@cashdiplo.es")
        self.assertEqual(ex.exception.codigo,"grupo_ambiguo")

    def test_filtro_usuarios_por_miembros_directos(self):
        usuarios={
            "elementos":[{"id":"usuario-1"},{"id":"usuario-2"}],
            "completo":True,
            "error":None,
        }
        miembros={
            "elementos":[
                {"id":"usuario-1","@odata.type":"#microsoft.graph.user"},
                {"id":"grupo-1","@odata.type":"#microsoft.graph.group"},
            ],
            "completo":True,
            "error":None,
        }

        resultado=solucion.filtrar_usuarios_por_miembros(usuarios,miembros)

        self.assertEqual(resultado["elementos"],[{"id":"usuario-1"}])
        self.assertTrue(resultado["completo"])

        miembros["completo"]=False
        miembros["error"]={"codigo":"limite_paginas"}
        resultado=solucion.filtrar_usuarios_por_miembros(usuarios,miembros)
        self.assertFalse(resultado["completo"])
        self.assertEqual(resultado["error"],miembros["error"])

    def test_responsables_y_exportacion(self):
        users={"ana@example.invalid":{"id":"a","accountEnabled":True,"userType":"Member"},
               "luis@example.invalid":{"id":"b","accountEnabled":True,"userType":"Member"}}
        casos=[{"caso":"FIN-001","upn":"ana@example.invalid"},{"caso":"RRHH-001","upn":"luis@example.invalid"},{"caso":"MANT-001","upn":"ana@example.invalid"},{"caso":"FIN-002","upn":"nadie@example.invalid"}]
        miembros={"elementos":[{"id":"a"}],"completo":True,"error":None}
        with patch("src.directorio.resolver_usuario",side_effect=lambda g,u:users.get(u)) as resolve:
            filas=preparar_responsables(Mock(),casos,"g",miembros)
            self.assertEqual(resolve.call_count,3)
        self.assertEqual([f["estado"] for f in filas],["listo","pendiente_alta","listo","no_encontrado"])
        with tempfile.TemporaryDirectory() as tmp:
            informe={"responsables":filas,"colecciones":{}}
            solucion.guardar_resultados(Path(tmp),informe)
            import csv,json
            with (Path(tmp)/"responsables_listos.csv").open(encoding="utf-8-sig",newline="") as stream:
                self.assertEqual([r["caso"] for r in csv.DictReader(stream,delimiter=";")],["FIN-001","MANT-001"])
            self.assertEqual(len(json.loads((Path(tmp)/"auditoria.json").read_text(encoding="utf-8"))["responsables"]),4)
        miembros["completo"]=False
        with patch("src.directorio.resolver_usuario",side_effect=lambda g,u:users.get(u)):
            filas=preparar_responsables(Mock(),casos,"g",miembros)
        self.assertEqual(filas[1]["estado"],"pertenencia_no_verificada")
        self.assertEqual(filas[0]["estado"],"listo")

if __name__=="__main__":
    unittest.main()

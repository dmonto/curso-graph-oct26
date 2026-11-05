"""Runnable local and live harness for the chapter's isolated snippets."""
import argparse
from copy import deepcopy
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

from src.archivos_graph import abrir_archivos, comprobar_carpeta_curso, guardar_json, metadatos
from src.lab_archivos import ArchivosLocales, DRIVE_DEMO, ARCHIVO_DEMO
from src.utils.files_client import ruta_item
from src.utils.graph_client import ErrorGraph


class SimulacionSnippets(ArchivosLocales):
    def escribir(self, metodo, ruta, cuerpo=None, datos=None, params=None,
                 headers=None, esperados=(200, 201)):
        if ruta.endswith('/restoreVersion'):
            self.historial.append({'metodo': metodo, 'ruta': ruta, 'local': True})
            version = unquote(ruta.split('/versions/')[1].split('/')[0])
            if version not in {'1.0', '2.0'}:
                raise ErrorGraph('itemNotFound', 404)
            self.contenidos[ARCHIVO_DEMO] = b'categoria;pendientes\nproveedores;1\n'
            self.items[ARCHIVO_DEMO]['size'] = len(self.contenidos[ARCHIVO_DEMO])
            self.items[ARCHIVO_DEMO]['eTag'] = '"ARCHIVO-DEMO,3"'
            return None
        if ruta.endswith('/invite'):
            self.historial.append({'metodo': metodo, 'operacion': 'invite', 'local': True})
            permiso = {'id': 'PERM-NUEVO', 'roles': cuerpo['roles'],
                       'grantedToV2': {'user': {'displayName': 'Usuario ficticio'}}}
            self.permisos.append(permiso)
            return {'value': [deepcopy(permiso)]}
        if '/permissions/' in ruta:
            self.historial.append({'metodo': metodo, 'operacion': 'permiso', 'local': True})
            if headers.get('If-Match') != self.items[ARCHIVO_DEMO]['eTag']:
                raise ErrorGraph('preconditionFailed', 412)
            pid = unquote(ruta.rsplit('/', 1)[1])
            permiso = next((p for p in self.permisos if p['id'] == pid), None)
            if permiso is None:
                raise ErrorGraph('itemNotFound', 404)
            if metodo == 'DELETE':
                self.permisos.remove(permiso)
                return None
            permiso.update(cuerpo)
            return deepcopy(permiso)
        return super().escribir(metodo, ruta, cuerpo, datos, params, headers, esperados)


def ejecutar_snippet(accion, funciones):
    p = argparse.ArgumentParser()
    p.add_argument('--local', action='store_true')
    p.add_argument('--aplicar', action='store_true')
    p.add_argument('--item-id')
    p.add_argument('--version-id', default='1.0')
    p.add_argument('--destinatario')
    p.add_argument('--salida', type=Path, default=Path('output/snippet-' + accion))
    args = p.parse_args()
    if not args.local and (not args.aplicar or not args.item_id):
        p.error('La escritura real necesita --aplicar y --item-id.')
    if not args.local and accion == 'permisos' and not args.destinatario:
        p.error('Indica --destinatario con la identidad verificada.')
    informe = {'run_id': str(uuid4()), 'local': args.local, 'auth': [], 'completo': False}

    def operar(cliente, drive, item_id):
        try:
            if accion == 'restaurar':
                informe['item'] = metadatos(funciones['restaurar_version'](
                    cliente, drive, item_id, args.version_id))
            else:
                respuesta = funciones['conceder_lectura'](cliente, drive, item_id,
                    args.destinatario or 'persona@example.invalid')
                permisos = respuesta.get('value', [])
                if len(permisos) != 1 or permisos[0].get('inheritedFrom'):
                    raise ValueError('Revisa la respuesta antes de continuar.')
                permiso = permisos[0]
                informe['permiso_creado'] = permiso['id']
                item = cliente.peticion('GET', ruta_item(drive, item_id))
                informe['cambio_rol'] = funciones['cambiar_rol'](
                    cliente, drive, item_id, permiso, 'write', item['eTag'])
                item = cliente.peticion('GET', ruta_item(drive, item_id))
                funciones['revocar_permiso_creado'](cliente, drive, item_id,
                    permiso['id'], [permiso['id']], item['eTag'])
                informe['revocado'] = permiso['id']
            informe['completo'] = True
        finally:
            informe['http'] = cliente.historial

    try:
        if args.local:
            with SimulacionSnippets() as cliente:
                operar(cliente, DRIVE_DEMO, ARCHIVO_DEMO)
        else:
            with abrir_archivos(False, True, informe) as (cliente, drive, folder):
                comprobar_carpeta_curso(cliente, drive, folder)
                item = cliente.peticion('GET', ruta_item(drive, args.item_id))
                if item.get('parentReference', {}).get('id') != folder or 'file' not in item:
                    raise ValueError('El archivo debe pertenecer directamente a la carpeta de laboratorio.')
                operar(cliente, drive, args.item_id)
    except ErrorGraph as exc:
        informe['error'] = exc.como_dict()
    except (ValueError, RuntimeError, OSError) as exc:
        informe['error'] = {'codigo': type(exc).__name__}
    guardar_json(args.salida / 'resultado.json', informe)
    print(args.salida / 'resultado.json')
    return 0 if informe['completo'] else 2

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from uuid import uuid4
from src.archivos_graph import guardar_json
from src.utils.config import leer_config
from src.utils.files_client import cliente_archivos, segmento
from src.utils.graph_client import ErrorGraph


def main():
    p = argparse.ArgumentParser(description='Actualizar columnas existentes de un listItem.')
    p.add_argument('--local', action='store_true')
    p.add_argument('--aplicar', action='store_true')
    p.add_argument('--site-id')
    p.add_argument('--list-id')
    p.add_argument('--list-item-id')
    p.add_argument('--salida', type=Path, default=Path('output/v15_columnas_sharepoint'))
    args = p.parse_args()
    if not args.local and not all([args.aplicar, args.site_id, args.list_id, args.list_item_id]):
        p.error('Usa --aplicar --site-id ID --list-id ID --list-item-id ID.')
    informe = {'run_id': str(uuid4()), 'local': args.local, 'auth': [], 'completo': False}
    campos = {'EstadoProceso': 'PendienteRevision', 'RunId': informe['run_id']}
    try:
        if args.local:
            informe['campos_actualizados'] = campos
        else:
            with cliente_archivos(leer_config(), ['Sites.ReadWrite.All'], informe) as cliente:
                try:
                    ruta = f'/sites/{segmento(args.site_id)}/lists/{segmento(args.list_id)}/items/{segmento(args.list_item_id)}/fields'
                    informe['campos_actualizados'] = cliente.escribir('PATCH', ruta, cuerpo=campos, esperados=(200,))
                finally:
                    informe['http'] = cliente.historial
        informe['completo'] = True
    except ErrorGraph as exc:
        informe['error'] = exc.como_dict()
    except (ValueError, RuntimeError, OSError) as exc:
        informe['error'] = {'codigo': type(exc).__name__}
    guardar_json(args.salida / 'resultado.json', informe)
    print(args.salida / 'resultado.json')
    return 0 if informe['completo'] else 2

if __name__ == '__main__':
    raise SystemExit(main())

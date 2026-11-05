from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
import os
from uuid import uuid4
from src.archivos_graph import guardar_json
from src.utils.config import leer_config
from src.utils.files_client import cliente_archivos, segmento
from src.utils.graph_client import ErrorGraph


def main():
    p = argparse.ArgumentParser(description='Descubre OneDrive, sitio y bibliotecas.')
    p.add_argument('--local', action='store_true')
    p.add_argument('--salida', type=Path, default=Path('output/v01_descubrimiento'))
    args = p.parse_args()
    informe = {'run_id': str(uuid4()), 'local': args.local, 'auth': [], 'completo': False}
    try:
        if args.local:
            informe.update(onedrive={'id': 'DRIVE-PERSONAL-DEMO'},
                sitio={'id': 'SITIO-DEMO'},
                bibliotecas={'elementos': [{'id': 'DRIVE-DEMO', 'name': 'Documentos'}],
                             'completo': True, 'paginas': 1, 'error': None},
                raiz={'elementos': [{'id': 'CARPETA-DEMO', 'name': 'CURSO-Automatizaciones', 'folder': {}}],
                      'completo': True, 'paginas': 1, 'error': None}, completo=True)
        else:
            config = leer_config()
            host = os.getenv('SHAREPOINT_HOSTNAME', '')
            path = os.getenv('SHAREPOINT_SITE_PATH', '/sites/Curso')
            if not host.endswith('.sharepoint.com') or '/' in host:
                raise ValueError('Configura SHAREPOINT_HOSTNAME.')
            with cliente_archivos(config, ['Files.Read.All', 'Sites.Read.All'], informe) as cliente:
                try:
                    informe['onedrive'] = cliente.peticion('GET', '/me/drive')
                    informe['sitio'] = cliente.peticion('GET', '/sites/' + host + ':/' +
                        '/'.join(segmento(x) for x in path.strip('/').split('/')))
                    informe['bibliotecas'] = cliente.listar('/sites/' + segmento(informe['sitio']['id']) + '/drives')
                    drive = os.getenv('DRIVE_ID') or informe['onedrive']['id']
                    informe['drive_raiz_consultada'] = drive
                    informe['raiz'] = cliente.listar('/drives/' + segmento(drive) + '/root/children')
                    informe['completo'] = informe['bibliotecas']['completo'] and informe['raiz']['completo']
                finally:
                    informe['http'] = cliente.historial
    except ErrorGraph as exc:
        informe['error'] = exc.como_dict()
    except (ValueError, RuntimeError, OSError) as exc:
        informe['error'] = {'codigo': type(exc).__name__}
    guardar_json(args.salida / 'resultado.json', informe)
    print(args.salida / 'resultado.json')
    return 0 if informe['completo'] else 2

if __name__ == '__main__':
    raise SystemExit(main())

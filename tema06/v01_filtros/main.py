from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
parametros = {
    "$select": "id,subject,from,receivedDateTime,isRead,hasAttachments,webLink,internetMessageId",
    "$filter": "receivedDateTime ge 2026-10-05T22:00:00Z and receivedDateTime lt 2026-10-06T22:00:00Z",
    "$orderby": "receivedDateTime desc",
    "$top": "2",
}
print(json.dumps(parametros, ensure_ascii=False, indent=2))

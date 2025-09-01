import shutil
from datetime import datetime
from typing import List, Dict, Optional

# Nota: evitamos dependencias externas. Usamos solo stdlib.

SUFFIXES = ["B", "KB", "MB", "GB", "TB"]


def human_size(n: int) -> str:
    try:
        size = float(n or 0)
    except Exception:
        return str(n)
    idx = 0
    while size >= 1024 and idx < len(SUFFIXES) - 1:
        size /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(size)} {SUFFIXES[idx]}"
    return f"{size:.1f} {SUFFIXES[idx]}"


def truncate_with_ellipsis(text: str, width: int) -> str:
    if width <= 0:
        return ""
    if len(text) <= width:
        return text
    if width <= 1:
        return "…"
    return text[:max(0, width - 1)] + "…"


def parse_datetime_str(s: str) -> str:
    # Convierte "YYYY-MM-DD HH:MM:SS" a "YYYY-MM-DD HH:MM" si puede
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return s or ""


def parse_line_to_file_item(line: str) -> Optional[Dict[str, str]]:
    """
    Intenta parsear una línea del listado del servidor en un dict {name, size, modified}.
    Acepta variantes tipo:
      - "archivo.pdf (1.23 MB) - 2025-08-31 20:17:23"
      - "📄 archivo.pdf (1.23 MB) - 2025-08-31 20:17:23"
      - "archivo.pdf 9038849 2025-08-31 20:17:23" (en caso de tamaños numéricos)
      - "archivo_sin_meta"
    Devuelve None si la línea es vacía o irrelevante.
    """
    if not line:
        return None
    l = line.strip()
    if not l:
        return None
    # Quitar posibles prefijos emoji
    if l.startswith("📄"):
        l = l[1:].strip()

    # Caso formato "nombre (tamaño) - fecha"
    if " (" in l and ")" in l:
        try:
            name_part = l.split(" (")[0].strip()
            size_part = l.split(" (")[1].split(")")[0].strip()
            date_part = l.split(" - ")[1].strip() if " - " in l else ""
            return {"name": name_part, "size": size_part, "modified": date_part}
        except Exception:
            pass

    # Caso formato "nombre size date"
    parts = l.split()
    if len(parts) >= 1:
        name = parts[0]
        size = ""
        date = ""
        if len(parts) > 1:
            # Intentar convertir a int para humanizar
            try:
                size_int = int(parts[1])
                size = human_size(size_int)
            except Exception:
                size = parts[1]
        if len(parts) > 3:
            date = " ".join(parts[2:4])
        return {"name": name, "size": size, "modified": date}

    return None


def group_with_hashes(files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Agrupa registros .hash/.sha256 debajo de su archivo base, solo para visualización.
    No altera los nombres originales en la lista base.
    """
    by_base: Dict[str, List[Dict[str, str]]] = {}
    for f in files:
        name = f.get("name", "")
        if name.endswith((".hash", ".sha256")):
            base = name.rsplit(".", 1)[0]
        else:
            base = name
        by_base.setdefault(base, []).append(f)

    grouped: List[Dict[str, str]] = []
    for base in sorted(by_base.keys(), key=lambda x: x.lower()):
        items = by_base[base]
        mains = [x for x in items if x.get('name') == base]
        others = [x for x in items if x not in mains]
        if mains:
            grouped.extend(mains)
        for x in sorted(others, key=lambda f: f.get('name', '').lower()):
            x2 = dict(x)
            x2['name'] = "  └─ " + x2.get('name', '')
            grouped.append(x2)
    return grouped


def print_file_table(files: List[Dict[str, str]], title: str = "ARCHIVOS DISPONIBLES", group_hashes: bool = True):
    """
    Muestra una tabla bonita sin dependencias.
    Espera elementos con keys: name, size (string ya humanizada o vacía), modified (YYYY-MM-DD HH:MM:SS opcional).
    """
    # Calcular anchos dinámicos según ancho de terminal
    term_width = shutil.get_terminal_size((100, 20)).columns
    term_width = max(term_width, 60)

    col_name, col_size, col_date = "Nombre", "Tamaño", "Modificado"

    width_size = 12  # caben "9999.9 MB"
    width_date = 16  # "2025-09-01 14:33"
    pad = 2
    width_name = term_width - (width_size + width_date + pad * 2)
    width_name = max(width_name, 16)

    # Título y encabezado
    print(title)
    header = f"{col_name:<{width_name}}{' ' * pad}{col_size:>{width_size}}{' ' * pad}{col_date:>{width_date}}"
    sep = f"{'-' * width_name}{' ' * pad}{'-' * width_size}{' ' * pad}{'-' * width_date}"
    print(header)
    print(sep)

    # Opcionalmente agrupar .hash/.sha256
    rows = group_with_hashes(files) if group_hashes else sorted(files, key=lambda f: f.get('name', '').lower())

    total_bytes = 0
    for f in rows:
        name = f.get("name", "")
        size_str = f.get("size", "")
        modified = f.get("modified", "")

        # Intentar parsear tamaño si viene como número
        if isinstance(size_str, (int, float)):
            size_str = human_size(int(size_str))

        # No sumar al total los registros indentados (hashes)
        if not name.startswith("  └─ "):
            # Si tenemos tamaño en bytes en otra clave, no disponible aquí; asumimos size_str humanizado.
            # Por simplicidad, no sumamos si no tenemos base numérica.
            # El total de bytes exacto no es esencial para la tabla sin dependencias.
            pass

        display_name = truncate_with_ellipsis(name, width_name)
        date_str = parse_datetime_str(modified)

        print(f"{display_name:<{width_name}}{' ' * pad}{(size_str or ''):>{width_size}}{' ' * pad}{date_str:>{width_date}}")

# -*- coding: utf-8 -*-
"""S14 · 3.2 Revisión de la configuración con la lista de comprobación (solo lectura).

Se ejecuta en el HOST, desde la raíz del repositorio (lambda26), en PowerShell:

    python pyspark/sesiones/u3/s14-revision-hardening/revision_config.py

Lee los compose.yml, NO modifica nada y deja el resultado en
./artifacts/revision_config.json (junto a este script), que el notebook 14 lee.
Solo usa la biblioteca estándar.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]                      # .../lambda26
ARCHIVOS = ["kafka/compose.yml", "obs/compose.yml", "pyspark/compose.yml", "uso-heladas/compose.yml"]
# servicios que deben declarar healthcheck; los auxiliares (UI, exporter) no se exigen
CRITICOS = {"kafka", "prometheus", "pushgateway", "grafana", "pyspark", "uso-heladas"}
SECRETO = re.compile(r"(PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY)", re.I)


def servicios(texto):
    """Devuelve {nombre: [líneas del bloque]} para el bloque `services:` (sangría de 2 espacios)."""
    lineas = texto.splitlines()
    out, actual, dentro = {}, None, False
    for ln in lineas:
        if re.match(r"^services:\s*$", ln):
            dentro = True
            continue
        if dentro and re.match(r"^\S", ln):          # otro bloque de nivel 0 (networks:, volumes:)
            dentro = False
        if not dentro:
            continue
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", ln)
        if m:
            actual = m.group(1)
            out[actual] = []
        elif actual is not None:
            out[actual].append(ln)
    return out


def bloque(lineas, clave):
    """Líneas hijas de `    clave:` (sangría de 4) dentro de un servicio."""
    res, dentro = [], False
    for ln in lineas:
        if re.match(rf"^    {clave}:", ln):
            dentro = True
            resto = ln.split(":", 1)[1].strip()
            if resto:
                res.append(resto)
            continue
        if dentro and re.match(r"^    \S", ln):       # siguiente clave del servicio
            break
        if dentro:
            res.append(ln.strip())
    return res if dentro else None


def valor(lineas, clave):
    for ln in lineas:
        m = re.match(rf"^    {clave}:\s*(.+?)\s*$", ln)
        if m:
            return m.group(1).strip("\"'")
    return None


def revisar(nombre, lineas):
    r = {"servicio": nombre}

    imagen = valor(lineas, "image")
    if imagen is None:
        r["imagen"] = ("N/A", "build local (Dockerfile propio)")
    else:
        fijada = ":" in imagen.split("/")[-1] and not imagen.endswith(":latest")
        r["imagen"] = ("CUMPLE" if fijada else "FALLA", imagen)

    reinicio = valor(lineas, "restart")
    r["reinicio"] = ("CUMPLE", reinicio) if reinicio else ("FALLA", "sin `restart:`")

    tiene_hc = bloque(lineas, "healthcheck") is not None
    if tiene_hc:
        r["salud"] = ("CUMPLE", "healthcheck declarado")
    elif nombre in CRITICOS:
        r["salud"] = ("FALLA", "servicio critico sin `healthcheck:`")
    else:
        r["salud"] = ("N/A", "auxiliar: no se exige")

    dep = bloque(lineas, "depends_on")
    if dep is None:
        r["orden"] = ("N/A", "sin dependencias declaradas")
    else:
        con_condicion = any("service_healthy" in d for d in dep)
        r["orden"] = ("CUMPLE", "espera a servicio sano") if con_condicion else \
                     ("FALLA", "depends_on sin `condition: service_healthy` (espera solo a que arranque)")

    literales = []
    env = bloque(lineas, "environment") or []
    for e in env:
        e = e.lstrip("- ").strip()
        m = re.match(r"^([A-Za-z0-9_]+)\s*[:=]\s*(.*)$", e)
        if m and SECRETO.search(m.group(1)):
            v = m.group(2).strip().strip("\"'")
            if v and not v.startswith("${"):
                literales.append(m.group(1))
    r["secretos"] = ("FALLA", "valor escrito en el archivo: " + ", ".join(literales)) if literales \
        else ("CUMPLE", "sin credenciales literales")

    puertos = [p.lstrip("- ").strip("\"' ") for p in (bloque(lineas, "ports") or [])]
    r["puertos"] = ("REVISAR", ", ".join(puertos) if puertos else "ninguno publicado")
    return r


def main():
    resultado = {"fecha": datetime.now().isoformat(timespec="seconds"), "raiz": str(RAIZ), "archivos": {}}
    fallas = []
    for rel in ARCHIVOS:
        ruta = RAIZ / rel
        if not ruta.exists():
            print(f"[AVISO] no existe {rel}")
            continue
        svc = servicios(ruta.read_text(encoding="utf-8"))
        resultado["archivos"][rel] = [revisar(n, l) for n, l in svc.items()]

    print(f"{'ARCHIVO':22} {'SERVICIO':16} {'IMAGEN':8} {'REINICIO':9} {'SALUD':8} {'ORDEN':8} {'SECRETOS':9} PUERTOS")
    for rel, lista in resultado["archivos"].items():
        for r in lista:
            print(f"{rel:22} {r['servicio']:16} {r['imagen'][0]:8} {r['reinicio'][0]:9} {r['salud'][0]:8} "
                  f"{r['orden'][0]:8} {r['secretos'][0]:9} {r['puertos'][1]}")
            for punto in ("imagen", "reinicio", "salud", "orden", "secretos"):
                if r[punto][0] == "FALLA":
                    fallas.append({"archivo": rel, "servicio": r["servicio"], "punto": punto, "detalle": r[punto][1]})
    resultado["fallas"] = fallas
    print()
    print(f"Puntos que FALLAN: {len(fallas)}")
    for f in fallas:
        print(f"  - {f['archivo']} :: {f['servicio']} :: {f['punto']} -> {f['detalle']}")

    destino = AQUI / "artifacts"
    destino.mkdir(exist_ok=True)
    contenido = json.dumps(resultado, indent=2, ensure_ascii=False)
    marca = datetime.now().strftime("%Y%m%dT%H%M%S")
    (destino / "revision_config.json").write_text(contenido, encoding="utf-8")            # la mas reciente
    (destino / f"revision_config_{marca}.json").write_text(contenido, encoding="utf-8")   # historial: antes/despues
    print("\nGuardado:", destino / "revision_config.json", "y revision_config_" + marca + ".json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

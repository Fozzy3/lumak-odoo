"""Uso (desde estadistica/):
  uv run python -m secop_estadistica actualizar --desde 2018-01-01   carga completa del histórico
  uv run python -m secop_estadistica actualizar                      semanal: re-lee los últimos 120 días
  uv run python -m secop_estadistica completar                       reanuda: ofertas que faltan y contratos
  uv run python -m secop_estadistica reclasificar                    vuelve a marcar el nicho con el clasificador actual
  uv run python -m secop_estadistica monitor                         diario: procesos abiertos a Odoo y precio para ganar
  uv run python -m secop_estadistica reporte                         informe en reportes/AAAA-MM-DD.md
  uv run python -m secop_estadistica avisar respaldo "5,5 MB"        deja en el tablero de Odoo que algo corrió
"""
import argparse
from datetime import date, timedelta
from pathlib import Path

from .base import Base
from .cargar import actualizar, cargar_contratos, cargar_ofertas, reclasificar, sin_ofertas

RAIZ = Path(__file__).resolve().parent.parent
BASE = RAIZ / "datos" / "secop.duckdb"


def main():
    parser = argparse.ArgumentParser(prog="secop_estadistica")
    sub = parser.add_subparsers(dest="orden", required=True)
    act = sub.add_parser("actualizar")
    # 120 días: un proceso se publica, cierra y adjudica en semanas; así la carga semanal recoge los cambios de estado
    act.add_argument("--desde", default=str(date.today() - timedelta(days=120)))
    act.add_argument("--sin-contratos", action="store_true")
    comp = sub.add_parser("completar")
    comp.add_argument("--contratos-desde", default=None, help="también baja los contratos firmados desde esa fecha")
    sub.add_parser("reclasificar")
    mon = sub.add_parser("monitor")
    mon.add_argument("--desde", help="por defecto, los últimos DIAS_ATRAS días (monitor.py)")
    sub.add_parser("reporte")
    avi = sub.add_parser("avisar")
    avi.add_argument("clave", choices=["monitor", "historico", "respaldo"])
    avi.add_argument("detalle")
    args = parser.parse_args()
    if args.orden == "avisar":  # no abre la base: la usa el respaldo, que no tiene nada que ver con DuckDB
        from .monitor import Odoo
        Odoo.desde_entorno().avisar(args.clave, args.detalle)
        return
    base = Base.abrir(BASE)
    if args.orden == "actualizar":
        n = actualizar(base, args.desde, contratos=not args.sin_contratos)
        print(f"procesos {n[0]}, ofertas {n[1]}, contratos {n[2]} (desde {args.desde})")
        try:  # si Odoo no está arriba, la carga igual queda hecha
            from .monitor import Odoo
            Odoo.desde_entorno().avisar("historico", f"{n[0]:,} procesos · {n[1]:,} ofertas".replace(",", "."))
        except (Exception, SystemExit) as error:
            print(f"no pude avisar a Odoo: {error}")
    elif args.orden == "completar":
        faltan = sin_ofertas(base)
        n, fallidos = cargar_ofertas(base, faltan)
        c = cargar_contratos(base, args.contratos_desde) if args.contratos_desde else 0
        print(f"ofertas {n} de {len(faltan)} procesos pendientes; contratos {c}; sin respuesta de SECOP: {len(fallidos)}")
    elif args.orden == "monitor":
        from .monitor import Odoo, sincronizar
        odoo = Odoo.desde_entorno()
        r = sincronizar(base, odoo, args.desde)
        odoo.avisar("monitor", f"{r['creados']} nuevos · {r['analizados']} con precio")
        print(f"abiertos del nicho {r['abiertos']}, nuevos en Odoo {r['creados']}, analizados {r['analizados']}, en Mercado SECOP {r['publicados']}")
        for id_proceso, error in r["errores"]:
            print(f"  sin importar {id_proceso}: {error}")
    elif args.orden == "reclasificar":
        print(f"procesos que cambiaron de nicho: {reclasificar(base)}")
    else:
        from .reporte import escribir
        print(escribir(base, RAIZ / "reportes"))


if __name__ == "__main__":
    main()

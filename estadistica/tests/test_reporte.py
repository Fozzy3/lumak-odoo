from datetime import date

from secop_estadistica.reporte import informe
from tests.test_base import base  # noqa: F401  (fixture con tres procesos y tres rivales)


def test_weekly_report_has_market_competitors_and_news(base):  # noqa: F811
    texto = informe(base, hoy=date(2025, 6, 5))
    for seccion in ("# Mínima cuantía de software", "## La base", "## El mercado del nicho", "## Competidores",
                    "## Novedades de los últimos 7 días", "## Entidades que más compran"):
        assert seccion in texto
    assert "Rival Dos SAS" in texto            # competidor con más ofertas ganadas
    assert "50 %" in texto                     # gana el más barato en 1 de 2 procesos con datos confiables
    assert "Soporte C" in texto                # publicado dentro de la semana

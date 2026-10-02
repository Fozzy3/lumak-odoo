"""Genera docs/guia-de-uso-lumak.pdf desde guia.html (formato de celular, 90 × 160 mm).
Uso, desde la raíz del repo: uv run --with playwright python docs/guia/pdf.py"""
from pathlib import Path

from playwright.sync_api import sync_playwright

aqui = Path(__file__).resolve().parent
salida = aqui.parent / "guia-de-uso-lumak.pdf"
pie = ('<div style="font-family:Noto Sans,sans-serif;font-size:6pt;color:#8A90A0;width:100%;padding:0 5.5mm;display:flex;justify-content:space-between">'
       '<span>Lumak en Odoo · Guía de uso</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--headless=new"])
    page = b.new_page()
    page.goto((aqui / "guia.html").as_uri(), wait_until="load")
    page.pdf(path=str(salida), print_background=True, prefer_css_page_size=True, display_header_footer=True,
             header_template="<span></span>", footer_template=pie, margin={"top": "6mm", "bottom": "8mm", "left": "5.5mm", "right": "5.5mm"})
    b.close()
print(salida)

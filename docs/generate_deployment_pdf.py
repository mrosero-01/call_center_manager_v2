from pathlib import Path

import markdown
from weasyprint import CSS, HTML


DOCS_DIR = Path(__file__).resolve().parent
SOURCE = DOCS_DIR / "manual_despliegue_completo.md"
STYLE = DOCS_DIR / "pdf_style.css"
OUTPUT = DOCS_DIR / "Manual_Despliegue_Siptic_Manager.pdf"


def main():
    source = SOURCE.read_text(encoding="utf-8")
    source = source.replace("\\newpage", '<div class="page-break"></div>')
    body = markdown.markdown(
        source,
        extensions=(
            "extra",
            "toc",
            "sane_lists",
        ),
        extension_configs={
            "toc": {
                "permalink": False,
                "toc_depth": "1-3",
            },
        },
    )
    html = f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>Manual de despliegue Siptic Manager</title></head>
<body>{body}</body>
</html>"""
    HTML(string=html, base_url=str(DOCS_DIR)).write_pdf(
        OUTPUT,
        stylesheets=[CSS(filename=STYLE)],
        pdf_identifier=True,
        pdf_variant="pdf/a-3b",
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()

# import os
# from notion_zip_reader import leer_html_desde_zip
# from notion_parser import parsear_html_notion
# from smart_pdf_exporter_v2 import exportar_documento_pdf_v2
# from config import cargar_config


# RUTA_ZIP = os.path.join("Entrada_ZIP", "export_notion.zip")
# RUTA_SALIDA = os.path.join("Salida", "notion_zip_convertido_v2.pdf")

# resultado = leer_html_desde_zip(RUTA_ZIP)

# documento = parsear_html_notion(
#     resultado["contenido_html"],
#     resultado["html_principal"]
# )

# config = cargar_config()

# os.makedirs("Salida", exist_ok=True)

# exportar_documento_pdf_v2(documento, RUTA_SALIDA, config)

# print("PDF generado:")
# print(RUTA_SALIDA)

import os

from config import cargar_config
from zip_pipeline import convertir_zip_notion_a_pdf


RUTA_ZIP = os.path.join("Entrada_ZIP", "export_notion.zip")

config = cargar_config()

ruta_generada = convertir_zip_notion_a_pdf(
    ruta_zip=RUTA_ZIP,
    carpeta_salida=config.get("salida", "Salida"),
    config=config
)

print("PDF generado:")
print(ruta_generada)
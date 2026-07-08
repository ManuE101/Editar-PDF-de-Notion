## Backlog de mejoras

1. Pruebas automatizadas de los flujos PDF y ZIP.
2. Generar y validar una nueva versión ejecutable en una PC limpia.


## Futuras mejoras

* Conversión por carpeta de documentos Word, cuando se defina el motor de conversión.
* Modo "Generación rápida" usando el perfil actual, si más adelante aporta valor frente a los perfiles.

## Ya implementado

* Recordar la última configuración utilizada.
* Drag & Drop de archivos.
* Botón para abrir la carpeta donde se guardó el PDF.
* Opción para abrir automáticamente la carpeta de salida.
* Procesamiento de varios ZIP en una sola ejecución.
* Renombrado automático del PDF según el título principal, detectándolo al seleccionar el ZIP y permitiendo editarlo antes de generar el PDF.
* Confirmación antes de sobrescribir un PDF existente.
* Perfiles de estilos guardados: permitir guardar varias configuraciones completas, por ejemplo “Cliente A”, “Cliente B”, “Interno”, etc., con logos, colores, márgenes y opciones propias.
* Recordar las últimas carpetas utilizadas para PDFs, ZIPs, logos y archivos de salida.
* Validación previa de los ZIP antes de generar el PDF.
* Detectar automáticamente si el ZIP corresponde a una exportación válida de Notion.
* Lógica preparada para convertir documentos Word DOC/DOCX usando Microsoft Word. La interfaz permanece deshabilitada hasta disponer de un motor de conversión en los equipos de la empresa.
* Mensajes de error específicos con causa, archivo afectado y acción sugerida.
* Procesamiento por lotes tolerante a fallos, con resumen visual dentro de la aplicación.
* Barra de progreso real por etapas para PDFs, ZIPs y procesamiento por carpetas.
* Ventana modal de progreso que bloquea nuevas cargas mientras se procesa un archivo o una carpeta.
* Cancelación segura desde la ventana de progreso, conservando archivos anteriores y eliminando temporales incompletos.

## Para revisar más adelante

* Conversión de Word a PDF sin Microsoft Word instalado:
  * Opción recomendada: Microsoft Graph mediante las cuentas corporativas de Microsoft 365/OneDrive.
  * Consultar con TI si se permite registrar la aplicación en Azure, autorizar acceso a archivos y enviar documentos a Microsoft 365 para convertirlos.
  * Alternativas: una API externa como Aspose Words Cloud, o distribuir LibreOffice junto con la aplicación.
  * La interfaz de Word permanece oculta, pero la lógica local existente se conserva para una futura implementación.

## Consideraciones técnicas

* La estructura de los ZIP exportados por Notion puede cambiar en futuras versiones. Conviene diseñar el parser de forma que sea fácil de adaptar si Notion modifica el formato de exportación.

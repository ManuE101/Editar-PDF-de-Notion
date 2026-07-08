import base64
import os
import subprocess


class WordConversionError(RuntimeError):
    pass


POWERSHELL_CONVERSION_SCRIPT = r"""
$ErrorActionPreference = "Stop"
$word = $null
$document = $null

try {
    $inputPath = [System.IO.Path]::GetFullPath($env:PDF_NOTION_WORD_INPUT)
    $outputPath = [System.IO.Path]::GetFullPath($env:PDF_NOTION_WORD_OUTPUT)

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($inputPath, $false, $true)
    $document.ExportAsFixedFormat($outputPath, 17)
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
finally {
    if ($null -ne $document) {
        $document.Close($false)
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    }
    if ($null -ne $word) {
        $word.Quit()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
"""


def convertir_word_a_pdf(ruta_word, ruta_pdf, timeout=180):
    ruta_word = os.path.abspath(ruta_word)
    ruta_pdf = os.path.abspath(ruta_pdf)

    if not os.path.isfile(ruta_word):
        raise WordConversionError("No se encontró el documento de Word seleccionado.")

    if os.path.splitext(ruta_word)[1].lower() not in {".doc", ".docx"}:
        raise WordConversionError("El archivo debe tener extensión .doc o .docx.")

    os.makedirs(os.path.dirname(ruta_pdf), exist_ok=True)
    script_encoded = base64.b64encode(
        POWERSHELL_CONVERSION_SCRIPT.encode("utf-16-le")
    ).decode("ascii")
    env = os.environ.copy()
    env["PDF_NOTION_WORD_INPUT"] = ruta_word
    env["PDF_NOTION_WORD_OUTPUT"] = ruta_pdf

    try:
        resultado = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-EncodedCommand",
                script_encoded,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as error:
        raise WordConversionError(
            "Microsoft Word tardó demasiado en convertir el documento."
        ) from error
    except OSError as error:
        raise WordConversionError(
            "No se pudo iniciar el conversor de Microsoft Word."
        ) from error

    if resultado.returncode != 0 or not os.path.isfile(ruta_pdf):
        detalle = (resultado.stderr or resultado.stdout or "").strip()
        if "80040154" in detalle or "Word.Application" in detalle:
            detalle = (
                "Microsoft Word no está instalado o no está disponible "
                "para el usuario actual."
            )
        raise WordConversionError(
            detalle or "Microsoft Word no pudo convertir el documento."
        )

    return ruta_pdf

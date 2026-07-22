# Audios de horarios

El sistema usa dos audios asociados a cierres operativos:

| Clave | Web MP3 | Asterisk WAV |
| --- | --- | --- |
| `falla_tecnica` | `static/audio/schedules/falla_tecnica.mp3` | `asterisk/sounds/callcenter_manager/falla_tecnica.wav` |
| `reentrenamiento_personal` | `static/audio/schedules/reentrenamiento_personal.mp3` | `asterisk/sounds/callcenter_manager/reentrenamiento_personal.wav` |

## Flujo recomendado

1. Subir los MP3 finales a `static/audio/schedules/`.
2. Convertirlos a WAV mono 8000 Hz.
3. Guardar las versiones WAV en `asterisk/sounds/callcenter_manager/`.
4. Copiar los WAV al servidor Asterisk.
5. Probar reproducción con Asterisk antes de conectar el dialplan.

## Nota de producto

La plataforma ya puede guardar la clave del audio seleccionado en el historial.
La conexión efectiva con Asterisk debe verificarse contra el dialplan real antes
de prometer que el audio elegido se reproducirá en llamada.

## Integración activa

El audio vigente se guarda en `CallCenter.closed_audio_file`. La vista
`schedules_asterisk_callcenter_status` entrega en una sola consulta:

- Si cliente y CallCenter están habilitados.
- Si está abierto según su horario y zona horaria.
- La ruta del audio de cierre.
- La zona horaria aplicada.

El usuario PostgreSQL de Asterisk necesita este permiso después de aplicar la
migración que crea la vista:

```bash
.venv/bin/python manage.py grant_asterisk_access \
  --role asterisk_schedule_reader
```

La función `ODBC_SIPTIC_CALLCENTER_STATUS()` y la subrutina de ejemplo están en:

- `asterisk/func_odbc_callcenter.conf.example`
- `asterisk/validar_horario.conf.example`

Los archivos finales se instalan, sin extensión en la instrucción `Playback`,
bajo:

```text
/var/lib/asterisk/sounds/custom/callcenter_manager/
```

Si el archivo configurado no existe como WAV o GSM, el dialplan usa
`vm-goodbye` como respaldo.

# Audios de horarios

El sistema usa tres audios asociados a cambios/cierres operativos:

| Clave | Web MP3 | Asterisk WAV |
| --- | --- | --- |
| `schedule_changed` | `static/audio/schedules/schedule_changed.mp3` | `asterisk/sounds/callcenter_manager/schedule_changed.wav` |
| `temporarily_unavailable` | `static/audio/schedules/temporarily_unavailable.mp3` | `asterisk/sounds/callcenter_manager/temporarily_unavailable.wav` |
| `special_day` | `static/audio/schedules/special_day.mp3` | `asterisk/sounds/callcenter_manager/special_day.wav` |

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

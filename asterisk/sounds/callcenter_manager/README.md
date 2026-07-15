# Audios Asterisk del gestor de horarios

Esta carpeta contiene la versión preparada para Asterisk de los mismos audios
que se previsualizan en la plataforma.

Nombres lógicos:

- `schedule_changed`
- `temporarily_unavailable`
- `special_day`

Formato recomendado para compatibilidad:

- WAV mono
- 8000 Hz
- 16-bit PCM

Ejemplo de conversión desde MP3:

```bash
ffmpeg -i static/audio/schedules/schedule_changed.mp3 -ar 8000 -ac 1 -sample_fmt s16 asterisk/sounds/callcenter_manager/schedule_changed.wav
ffmpeg -i static/audio/schedules/temporarily_unavailable.mp3 -ar 8000 -ac 1 -sample_fmt s16 asterisk/sounds/callcenter_manager/temporarily_unavailable.wav
ffmpeg -i static/audio/schedules/special_day.mp3 -ar 8000 -ac 1 -sample_fmt s16 asterisk/sounds/callcenter_manager/special_day.wav
```

Para instalar en un servidor Asterisk, copiar los `.wav` al directorio de
sonidos que use la central, por ejemplo:

```bash
sudo mkdir -p /var/lib/asterisk/sounds/custom/callcenter_manager
sudo cp asterisk/sounds/callcenter_manager/*.wav /var/lib/asterisk/sounds/custom/callcenter_manager/
sudo chown -R asterisk:asterisk /var/lib/asterisk/sounds/custom/callcenter_manager
```

No se modifica el dialplan desde esta carpeta. La integración con `Playback`
o `Background` debe hacerse en una tarea separada y probada en Asterisk.

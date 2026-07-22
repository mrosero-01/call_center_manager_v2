# Audios Asterisk del gestor de horarios

Esta carpeta contiene la versión preparada para Asterisk de los mismos audios
que se previsualizan en la plataforma.

Nombres lógicos:

- `falla_tecnica`
- `reentrenamiento_personal`

Formato recomendado para compatibilidad:

- WAV mono
- 8000 Hz
- 16-bit PCM

Ejemplo de conversión desde MP3:

```bash
sox static/audio/schedules/falla_tecnica.mp3 -r 8000 -c 1 -e signed-integer -b 16 asterisk/sounds/callcenter_manager/falla_tecnica.wav
sox static/audio/schedules/reentrenamiento_personal.mp3 -r 8000 -c 1 -e signed-integer -b 16 asterisk/sounds/callcenter_manager/reentrenamiento_personal.wav
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

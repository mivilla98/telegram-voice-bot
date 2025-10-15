"""
Bot de Telegram que convierte audios de voz a tono femenino
Autor: v0
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import librosa
import soundfile as sf
import numpy as np
from pydub import AudioSegment

load_dotenv()

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Crear carpeta temporal para archivos de audio
os.makedirs('temp_audio', exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Mensaje de bienvenida"""
    welcome_message = (
        "¡Hola! 👋\n\n"
        "Soy un bot que convierte tu voz a tono femenino.\n\n"
        "📝 Instrucciones:\n"
        "1. Envíame un mensaje de voz\n"
        "2. Espera unos segundos mientras proceso el audio\n"
        "3. Recibirás tu audio con voz femenina\n\n"
        "¡Pruébalo ahora!"
    )
    await update.message.reply_text(welcome_message)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa los mensajes de voz recibidos"""
    try:
        # Informar al usuario que estamos procesando
        processing_msg = await update.message.reply_text("🎵 Procesando tu audio...")
        
        # Obtener el archivo de voz
        voice = await update.message.voice.get_file()
        user_id = update.message.from_user.id
        
        # Rutas de archivos temporales
        input_path = f'temp_audio/input_{user_id}.ogg'
        wav_path = f'temp_audio/input_{user_id}.wav'
        output_path = f'temp_audio/output_{user_id}.ogg'
        
        # Descargar el audio
        await voice.download_to_drive(input_path)
        logger.info(f"Audio descargado de usuario {user_id}")
        
        audio = AudioSegment.from_file(input_path, format="ogg")
        audio.export(wav_path, format="wav")
        
        # Cargar el audio con librosa desde WAV
        y, sr = librosa.load(wav_path, sr=None)
        
        # Cambiar el pitch (tono) para hacerlo más agudo (femenino)
        # n_steps=4 significa subir 4 semitonos (ajustable según preferencia)
        y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=4)
        
        # Opcional: Ajustar la velocidad ligeramente para un efecto más natural
        # y_shifted = librosa.effects.time_stretch(y_shifted, rate=0.95)
        
        # Guardar el audio procesado
        sf.write(output_path, y_shifted, sr)
        logger.info(f"Audio procesado para usuario {user_id}")
        
        # Enviar el audio de vuelta
        with open(output_path, 'rb') as audio_file:
            await update.message.reply_voice(
                voice=audio_file,
                caption="✨ Aquí está tu audio con voz femenina"
            )
        
        # Eliminar mensaje de procesamiento
        await processing_msg.delete()
        
        for temp_file in [input_path, wav_path, output_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
        logger.info(f"Proceso completado para usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error procesando audio: {e}")
        await update.message.reply_text(
            "❌ Hubo un error procesando tu audio. Por favor, intenta de nuevo."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - Muestra ayuda"""
    help_text = (
        "🤖 Bot de Conversión de Voz\n\n"
        "Comandos disponibles:\n"
        "/start - Iniciar el bot\n"
        "/help - Mostrar esta ayuda\n\n"
        "Simplemente envía un mensaje de voz y lo convertiré a tono femenino."
    )
    await update.message.reply_text(help_text)

def main():
    """Función principal para ejecutar el bot"""
    # Obtener el token del bot desde variable de entorno
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("ERROR: No se encontró TELEGRAM_BOT_TOKEN en las variables de entorno")
        print("\n❌ ERROR: Debes configurar la variable de entorno TELEGRAM_BOT_TOKEN")
        print("Consulta el archivo README.md para más información\n")
        return
    
    # Crear la aplicación
    application = Application.builder().token(token).build()
    
    # Agregar manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Agregar manejador para mensajes de voz
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    # Iniciar el bot
    logger.info("Bot iniciado correctamente")
    print("\n✅ Bot de Telegram iniciado correctamente")
    print("Presiona Ctrl+C para detener el bot\n")
    
    # Ejecutar el bot hasta que se presione Ctrl+C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

/**
 * NAYA Mobile — Voice Engine
 * STT (speech-to-text) + TTS (text-to-speech) with Capacitor
 */
import { SpeechRecognition } from '@capacitor-community/speech-recognition';
import { TextToSpeech } from '@capacitor-community/text-to-speech';

export interface VoiceResult {
  transcript: string;
  confidence: number;
}

/** Start listening and return transcript */
export async function listen(language: string = 'fr-FR'): Promise<VoiceResult> {
  const available = await SpeechRecognition.available();
  if (!available) throw new Error('Speech recognition not available on this device');

  const hasPermission = await SpeechRecognition.checkPermissions();
  if (hasPermission.speechRecognition !== 'granted') {
    await SpeechRecognition.requestPermissions();
  }

  return new Promise((resolve, reject) => {
    SpeechRecognition.start({
      language,
      maxResults: 1,
      popup: false,
      partialResults: false,
    });

    SpeechRecognition.addListener('partialResults', (data: any) => {
      if (data?.matches?.length) {
        SpeechRecognition.stop();
        resolve({ transcript: data.matches[0], confidence: 0.9 });
      }
    });

    setTimeout(() => { SpeechRecognition.stop(); reject(new Error('Timeout')); }, 10000);
  });
}

/** Stop listening */
export async function stopListening(): Promise<void> {
  await SpeechRecognition.stop();
}

/** Speak text aloud */
export async function speak(text: string, language: string = 'fr-FR', rate: number = 1.0): Promise<void> {
  await TextToSpeech.speak({
    text,
    lang: language,
    rate,
    pitch: 1.0,
    volume: 1.0,
    category: 'ambient',
  });
}

/** Stop current speech */
export async function stopSpeaking(): Promise<void> {
  await TextToSpeech.stop();
}

export async function isVoiceAvailable(): Promise<boolean> {
  const { speechRecognition } = await SpeechRecognition.available();
  return !!speechRecognition;
}

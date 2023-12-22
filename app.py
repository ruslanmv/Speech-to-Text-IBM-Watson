from flask import Flask, request, jsonify, render_template
from ibm_watson import SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
from dotenv import load_dotenv
import mimetypes
from pydub import AudioSegment

load_dotenv()

authenticator = IAMAuthenticator(os.getenv("API_KEY"))
speech_to_text = SpeechToTextV1(authenticator=authenticator)
speech_to_text.set_service_url(os.getenv("SERVICE_URL"))

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_audio_to_text():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    audio_file = request.files['file']
    file_name = audio_file.filename
    content_type, _ = mimetypes.guess_type(file_name)
    
    if content_type not in ['audio/mpeg', 'audio/mp3','audio/mp4', 'audio/x-m4a']:
        return jsonify({'error': 'Invalid file format'}), 400

    file_path = file_name
    audio_file.save(file_path)

    if content_type == 'audio/mpeg':
        audio = AudioSegment.from_file(file_path, "mp3")
    else:
        audio = AudioSegment.from_file(file_path, "mp4")
        audio.export("converted_audio.mp3", format="mp3")
        file_path = "converted_audio.mp3"
        content_type = "audio/mp3"

    with open(file_path, 'rb') as audio_file:
        response = speech_to_text.recognize(audio=audio_file,
                                            content_type=content_type,
                                            speaker_labels=True,
                                            inactivity_timeout=-1).get_result()

    transcripts = [result['alternatives'][0]['transcript'] for result in response['results']]
    transcript = " ".join(x for x in transcripts)
    
    return jsonify({'transcript': transcript})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
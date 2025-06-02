import os
import re
import requests
from dotenv import load_dotenv
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser

load_dotenv()

AZURE_KEY = os.getenv("AZURE_TTS_KEY")
AZURE_REGION = os.getenv("AZURE_TTS_REGION")
AZURE_VOICE = os.getenv("AZURE_TTS_VOICE", "en-US-JennyNeural")


# Remove emojis from text
def remove_emojis(text):
    return re.sub(r'[\U0001F600-\U0001F64F'
                          r'\U0001F300-\U0001F5FF'
                          r'\U0001F680-\U0001F6FF'
                          r'\U0001F1E0-\U0001F1FF'
                          r'\U00002702-\U000027B0'
                          r'\U000024C2-\U0001F251]+', '', text, flags=re.UNICODE)

# Remove Markdown formatting and clean text
def clean_text(text):
    text = remove_emojis(text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)                 # bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)                     # italic
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)                 # remove images
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)       # [text](url)
    text = re.sub(r'#+\s', '', text)                             # headers
    text = re.sub(r'```[\s\S]*?```', '', text)                   # code blocks
    text = re.sub(r'`(.*?)`', r'\1', text)                       # inline code
    text = re.sub(r'[\r\n]+', '. ', text)                        # newlines → sentence
    text = re.sub(r'[“”‘’]', '', text)                           # fancy quotes
    text = re.sub(r'\s{2,}', ' ', text)                          # multiple spaces
    return text.strip()

@api_view(['POST'])
def tts_generate(request):
    try:
        data = JSONParser().parse(request)
        raw_text = data.get("text", "").strip()
        print("[DEBUG] Original text:", raw_text)

        if not raw_text:
            return JsonResponse({"error": "No text provided"}, status=400)

        cleaned_text = clean_text(raw_text)
        print("[DEBUG] Cleaned text for TTS:", cleaned_text)

        # Azure TTS endpoint
        tts_url = f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-160kbitrate-mono-mp3",
        }

        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis'
               xmlns:mstts='https://www.w3.org/2001/mstts'
               xml:lang='en-US'>
          <voice name='{AZURE_VOICE}'>
            <mstts:express-as style='general'>
              {cleaned_text}
            </mstts:express-as>
          </voice>
        </speak>
        """

        response = requests.post(tts_url, headers=headers, data=ssml.encode("utf-8"))

        if response.status_code != 200:
            print("Azure TTS ERROR")
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            return JsonResponse({"error": "Azure TTS failed", "details": response.text}, status=500)

        return HttpResponse(response.content, content_type="audio/mpeg")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

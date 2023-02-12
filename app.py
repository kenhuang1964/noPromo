import re
import subprocess
import pytube
from pytube import YouTube
import whisperx
import openai
import selenium
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from flask import Flask, request
import config

app = Flask(__name__)

@app.route('/skip_promotions', methods=['POST'])
def skip_promotions():
    """
    Endpoint to skip promotions in a video.
    """
    url = request.args.get('url', '')
    promo_times = gpt_3(transcribe(extract_audio(url)))
    skip_video(promo_times, url)
    return "Promotions skipped successfully!"


def extract_audio(url) -> str:
    """
    Extract the audio from the video.

    :param url: the URL of the video
    :return: the filename of the extracted audio
    """
    selected_video = YouTube(url)
    audio = selected_video.streams.filter(only_audio=True, file_extension='mp4').first()
    audio.download()
    return audio.filename

def transcribe(path) -> list:
    """
    Transcribe the audio.

    :param path: the path to the audio file
    :return: the result of the transcription
    """
    device = "cuda"
    model = whisperx.load_model("large", device)
    result = model.transcribe("/content/WW2 - OverSimplified (Part 1).mp4")
    # load alignment model and metadata
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)

    video_file = path
    # align whisper output
    result_aligned = whisperx.align(result["segments"], model_a, metadata, video_file, device)
    return result_aligned

def gpt_3(result_aligned)->list:
    """
    Use GPT-3 to identify the promotions in the video.

    :param result_aligned: the result of the transcription
    :return: the timestamps of the promotions
    """
    openai.api_key = config.API_KEY
    # Prepare the text input for GPT-3
    promotion_detection_text = ""
    for segment, start, end in result_aligned["word_segments"]:
        promotion_detection_text += f"{segment} ({start} - {end})\n"

    # Split the text into chunks
    chunk_size = 512
    promotion_detection_text_chunks = [promotion_detection_text[i:i + chunk_size] for i in range(0, len(promotion_detection_text), chunk_size)]

    # Make the API requests
    promotion_detection_model = "text-davinci-003"
    promotion_timestamps = []
    for chunk in promotion_detection_text_chunks:
        promotion_detection_response = openai.Completion.create(
            engine=promotion_detection_model,
            prompt=f"Please identify the segments containing promotions (do not generate new text) in the following text:\n{chunk}",
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0.5,
        )

        # Process the API response
        if not promotion_detection_response["choices"]:
            continue
        
        promotion_detection_result = promotion_detection_response["choices"][0]["text"].strip()
        match = re.findall(r"\((\d+ - \d+)\)", promotion_detection_result)
        promotion_timestamps.extend(match)

    return promotion_timestamps

def skip_video(promo_times, video_url)->None:
    """
    This function skips the promotional parts of a video based on the given start and end times.

    Parameters:
    promo_times (List[Tuple[float, float]]): A list of start and end times for the promotional parts.
    video_url (str): The URL of the video.

    Returns:
    None
    """
    # Launch a headless chrome instance
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(video_url)
    
    # Wait for the video player to load
    video_player = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "movie_player"))
    )
    
    # Get the current time of the video
    current_time = driver.execute_script("return arguments[0].getCurrentTime()", video_player)
    
    # Loop through the list of start and end times
    for start_time, end_time in promo_times:
        # Check if the current time is between start_time and end_time
        if start_time <= current_time <= end_time:
            # Skip to end_time
            driver.execute_script("arguments[0].seekTo(arguments[1], true)", video_player, end_time)
            break
    driver.quit()

if __name__ == '__main__':
    app.run()

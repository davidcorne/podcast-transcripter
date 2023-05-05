import feedparser
import openai
import os
import re
import requests
import logging

from pydub import AudioSegment

openai.api_key = os.environ.get("OPEN_AI_API")

# Define the RSS feed URL
rss_feed_url = "https://feeds.blubrry.com/feeds/the_glass_cannon.xml"

# Parse the RSS feed
feed = feedparser.parse(rss_feed_url)

# Define the directory where you want to save the downloaded MP3 files
save_dir = "downloads"

# Create the save directory if it doesn't exist
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Set up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

def split_file(file_name):
    # Set the path where the split files will be saved
    output_dir = "downloads/split"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Set the duration of each chunk in milliseconds (10 minutes in this case)
    chunk_duration_ms = 10 * 60 * 1000

    # Load the MP3 file using Pydub
    audio = AudioSegment.from_file(file_name, format="mp3")

    # Get the duration of the MP3 file in seconds
    duration_s = audio.duration_seconds

    # Calculate the number of chunks needed to split the file into 10 minute intervals
    num_chunks = int(duration_s / (chunk_duration_ms / 1000))

    basename = os.path.splitext(os.path.basename(file_name))[0]
    output_files = []
    # Iterate over the number of chunks and slice the MP3 file into 10 minute chunks
    for i in range(num_chunks):
        logger.debug(f"Splitting {i+1}/{num_chunks}")
        # Calculate the start and end times for the current chunk
        start_time = i * chunk_duration_ms
        end_time = (i + 1) * chunk_duration_ms

        # Slice the MP3 file to extract the current chunk
        chunk = audio[start_time:end_time]

        # Set the output file name for the current chunk
        output_path = f"{output_dir}/{basename}_chunk_{i}.mp3"

        # Save the current chunk to a file in the output directory
        chunk.export(output_path, format="mp3")

        output_files.append(output_path)
    return output_files

def do_transcript_split_file(file_name):
    do_transcript_file(file_name)
    os.remove(file_name)

def do_transcript_file(file_name):
    logger.info(f"Processing {file_name} into {transcript_file_name(file_name)}")
    with open(file_name, "rb") as audio_file:
        ai_transcript = openai.Audio.translate("whisper-1", audio_file)
        transcript = ai_transcript.text
    with open(transcript_file_name(file_name), "w") as transcript_file:
        transcript_file.write(transcript)

def transcript_file_name(file_name):
    return os.path.splitext(file_name)[0] + ".transcript.txt"

def concatenate_files(output_file, input_files):
    with open(output_file, 'wb') as outfile:
        for fname in input_files:
            with open(fname, 'rb') as infile:
                outfile.write(infile.read())

def transcript_file(file_name):
    # Get the file size in bytes
    file_size = os.path.getsize(file_name)

    # Convert the file size to megabytes
    file_size_mb = file_size / (1024 * 1024)

    # Check if the file is over 25MB in size
    if file_size_mb > 25:
        files = split_file(file_name)
        for sub_file in files:
            do_transcript_split_file(sub_file)
        # Combine transcriptions
        transcript_files = [transcript_file_name(f) for f in files]
        concatenate_files(transcript_file_name(file_name), transcript_files)
        # for transcript_file in transcript_files:
            # Not yet
            # os.remove(transcript_file)
    else:
        do_transcript_file(file_name)
    logger.info(f"Transcripted {transcript_file_name(file_name)}")

def handle_podcast_item(item):
    file_name = download_podcast_item(item)
    logger.info(f"Downloaded {file_name}")
    transcript_file(file_name)

    os.remove(file_name)
    logger.info(f"Removed {file_name}")

def sanitize_filename(filename):
    # Replace / with -
    filename = filename.replace('/', '-')

    # Remove any characters that are not allowed in file names
    filename = re.sub(r'[^\w\s\-_.()]', '', filename)

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    return filename

def download_podcast_item(item):
    # Get the MP3 URL from the feed entry
    mp3_url = item.enclosures[0].href

    # Get the file name from the MP3 URL
    file_name = sanitize_filename(item.title + ".mp3")

    # Define the file path for saving the MP3 file
    file_path = os.path.join(save_dir, file_name)

    # Download the MP3 file
    response = requests.get(mp3_url)

    # Save the MP3 file to disk
    with open(file_path, "wb") as f:
        f.write(response.content)

    return file_path

# Iterate over each entry in the feed
for entry in feed.entries:
    handle_podcast_item(entry)

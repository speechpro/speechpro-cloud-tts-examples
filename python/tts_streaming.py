import wave
import asyncio
import argparse
import logging
import datetime
import concurrent.futures
import os

import websockets
import pyaudio

from cloud_client.models.auth_request_dto import AuthRequestDto
from cloud_client.api.session_api import SessionApi
from cloud_client.api.synthesize_api import Synthesize as SynthesizeApi
from cloud_client.models import WebSocketSynthesizeRequest, WebSocketTextParam


logger = logging.getLogger(__name__)


def login():
    session_api = SessionApi()
    credentials = AuthRequestDto(username, domain_id, api_key)
    session_id = session_api.login(credentials).session_id
    logger.info(f'Session id: {session_id}')
    return session_id


def open_websocket_connection(voice):
    session_id = login()
    synthesis_api = SynthesizeApi()
    stream_request = WebSocketSynthesizeRequest(
        WebSocketTextParam("text/plain"),
        voice,
        "audio/s16le")
    start = datetime.datetime.now()
    web_socket_configuration = synthesis_api.web_socket_stream(session_id, stream_request)
    logger.info(f'Received websocket config response: {web_socket_configuration}')
    return web_socket_configuration.url, start


def synthesize_stream(message, voice):
    url, start = open_websocket_connection(voice)

    samplerate = 8000 if '8000' in voice else 22050

    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(2),
                channels=1,
                rate=samplerate,
                output=True)
    stream.start_stream()

    async def send_data(websocket, message):
        logger.info('Sending data')
        await websocket.send(message)
        start = datetime.datetime.now()

    async def receive_data(websocket, stream, sound):
        try:
            first_sound = False
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                if not first_sound:
                    logger.info(f'Time to first sound: {datetime.datetime.now() - start}')
                    first_sound = True
                sound.extend(message)
                stream.write(message)
        except concurrent.futures.TimeoutError as e:
            logger.info('Websocket Timeout - exiting')
        except Exception:
            logger.exception('Error during streaming synthesis')
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

            with wave.open(output_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframesraw(sound)


    async def synthesize(uri, data):
        sound = bytearray()
        async with websockets.connect(uri, ssl=True) as websocket:
            send_task = asyncio.create_task(send_data(websocket, data))
            receive_task = asyncio.create_task(receive_data(websocket, stream, sound))

            await send_task
            await receive_task

    asyncio.get_event_loop().run_until_complete(synthesize(url, message))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(name)s : %(levelname)s : %(message)s')
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', type=str, help='Файл с текстом для синтеза')
    parser.add_argument('-o', type=str, help='Выходной WAV файл')
    parser.add_argument('-v', type=str, help='Голос')
    parser.add_argument('-t', type=int, default=5, help='Таймаут вебсокета в секундах')
    args = parser.parse_args()

    input_file = args.i
    output_file = args.o
    voice = args.v
    timeout = args.t
    username = os.environ['SPEECHPRO_USERNAME']
    api_key = os.environ['SPEECHPRO_PASSWORD']
    domain_id = os.environ['SPEECHPRO_DOMAIN_ID']

    with open(input_file) as f:
        message = f.read()
        logger.info(f'Text to synthesize: {message}')
    synthesize_stream(message, voice)

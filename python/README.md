# Потоковый синтез речи

Данный пример демонстрирует потоковый синтез речи ЦРТ Облака с записью полученного звука в файл и одновременного воспроизведения в режиме реального времени.

## Начало работы

Установите зависимости с помощью pip
```
pip install -r requirements.txt
```

Задайте данные вашей учетной записи [ЦРТ Облака](https://cp.speechpro.com) с помощью переменных среды
```
export SPEECHPRO_USERNAME=username
export SPEECHPRO_DOMAIN_ID=200
export SPEECHPRO_PASSWORD=password
```

Запустите синтез
```
python tts_streaming.py -v Julia_n -i //path_to_text_file -o output.wav
```

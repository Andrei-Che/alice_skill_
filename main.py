import json
import os
import boto3
from skyfield.api import load
from datetime import datetime
from botocore.exceptions import ClientError

def parse_date(date_str):
    from datetime import datetime, timedelta
    numbers = {
        'первое': 1, 'второе': 2, 'третье': 3, 'четвертое': 4,
        'пятое': 5, 'шестое': 6, 'седьмое': 7, 'восьмое': 8,
        'девятое': 9, 'десятое': 10, 'одиннадцатое': 11, 'двенадцатое': 12,
        'тринадцатое': 13, 'четырнадцатое': 14, 'пятнадцатое': 15,
        'шестнадцатое': 16, 'семнадцатое': 17, 'восемнадцатое': 18,
        'девятнадцатое': 19, 'двадцатое': 20, 'двадцать': 20, 'двадцать первое': 21,
        'двадцать второе': 22, 'двадцать третье': 23, 'двадцать четвертое': 24,
        'двадцать пятое': 25, 'двадцать шестое': 26, 'двадцать седьмое': 27,
        'двадцать восьмое': 28, 'двадцать девятое': 29, 'тридцатое': 30, 'тридцать': 30,
        'тридцать первое': 31, 'первого': 1, 'второго': 2, 'третьго': 3, 'четвертого': 4,
        'пятого': 5, 'шестого': 6, 'седьмого': 7, 'восьмого': 8,
        'девятого': 9, 'десятого': 10, 'одиннадцатого': 11, 'двенадцатого': 12,
        'тринадцатого': 13, 'четырнадцатого': 14, 'пятнадцатого': 15,
        'шестнадцатого': 16, 'семнадцатого': 17, 'восемнадцатого': 18,
        'девятнадцатого': 19, 'двадцатого': 20, 'тридцатого': 30}
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
        'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
        'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}
    user_input = date_str.lower().split()
    parsed_date = []
    parsed_month = []
    try:
        date_str = ' '.join(date_str.strip().split()).lower()
        if "на завтра" in date_str:
            tomorrow = datetime.now() + timedelta(days=1)
            return (tomorrow.month, tomorrow.day)
        else:
            for _ in user_input:
                if _ in numbers:
                    parsed_date.append(numbers.get(_))
                if _ in months:
                    parsed_month.append(months.get(_))
            return parsed_month[0], sum(parsed_date)

    except (ValueError, AttributeError, IndexError, KeyError) as e:
        print(f"Error in parse_date: {str(e)}")
        return None


def get_moon_sign(date=None):

    try:
        # Настройки Object Storage
        bucket_name = 'alice-skill-backet'
        object_key = 'de421.bsp'
        bsp_path = '/tmp/de421.bsp'

        # Проверяем, существует ли файл
        if not os.path.exists(bsp_path):
            print(f"Файл {bsp_path} не найден, загружаем из S3...")
            # Загружаем из Object Storage
            s3_client = boto3.client(
                's3',
                endpoint_url='https://storage.yandexcloud.net',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            try:
                s3_client.download_file(bucket_name, object_key, bsp_path)
                print(f"Файл {object_key} успешно загружен в {bsp_path}")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                return f"Ошибка S3: {error_code} - {error_message}"

        # Загружаем эфемериды
        print(f"Загружаем эфемериды из {bsp_path}")
        eph = load(bsp_path)
        ts = load.timescale()

        if date:
            months = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}
            month, day = date
            now = datetime.now()
            year = now.year
            t = ts.utc(year, month, day)
            print(month)
            date_prefix = f"На {day} {list(months.keys())[month-1]} "
        else:
            t = ts.now()
            date_prefix = "Сегодня "

        earth, moon = eph['earth'], eph['moon']
        moon_position = earth.at(t).observe(moon).apparent()
        longitude = moon_position.ecliptic_latlon()[1].degrees
        print(f"Эклиптическая долгота Луны: {longitude} градусов")

        # Определяем знак зодиака
        zodiac_signs = [
            "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
            "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
        ]
        sign_index = int(longitude // 30)
        current_sign = zodiac_signs[sign_index]

        # Определяем тип дня по биокалендарю
        if current_sign in ("Овен", "Лев", "Стрелец"):
            return date_prefix + f"по биокалендарю Фруктовый день. Луна в знаке {current_sign}. Это благоприятный день для вина! Хотите узнать про другую дату?"
        elif current_sign in ("Близнецы", "Весы", "Водолей"):
            return date_prefix + f"по биокалендарю Цветочный день. Луна в знаке {current_sign}. Это благоприятный день для вина! Хотите узнать про другую дату?"
        elif current_sign in ("Рак", "Скорпион", "Рыбы"):
            return date_prefix + f"по биокалендарю Лиственный день. Луна в знаке {current_sign}. Это неблагоприятный день для вина! Хотите узнать про другую дату?"
        else:
            return date_prefix + f"по биокалендарю Корневой день. Луна в знаке {current_sign}. Это неблагоприятный день для вина! Хотите узнать про другую дату?"
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        return f"Ошибка S3: {error_code} - {error_message}"
    except Exception as e:
        return f"Неизвестная ошибка: {str(e)}"

def handler(event, context):
    import json
    print(f"Event: {event}")

    try:
        # Парсим входящий запрос
        if isinstance(event, dict):
            request = event
        elif isinstance(event, str):
            request = json.loads(event)
        else:
            request = {}

        body = request.get('body', {})
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                print("Failed to parse body as JSON")
                body = {}

        session = body.get('session', {})
        new_session = session.get('new', False)
        user_input = body.get('request', {}).get('original_utterance', '').lower().strip()
        # Извлекаем состояние сессии из body['state']['session']
        session_state = body.get('state', {}).get('session', {})
        print(f'Session: {session}')
        print(f'New session: {new_session}')
        print(f'User_input: "{user_input}"')
        print(f'Session state: {session_state}')

        # Проверяем интент YANDEX.CONFIRM для обработки "да"
        intents = body.get('request', {}).get('nlu', {}).get('intents', {})
        is_confirm = 'YANDEX.CONFIRM' in intents

        # Обрабатываем ответ на вопрос "Хотите узнать другую дату?"
        if session_state.get('awaiting_date', False) or is_confirm:
            print("Processing awaiting_date state or YANDEX.CONFIRM")
            if any(word in user_input for word in ['да', 'ага', 'конечно', 'хочу']) or is_confirm:
                print("User said 'yes' or confirmed, requesting date")
                response_text = "На какую дату вы хотите узнать? Например, '25 августа' или 'На завтра'."
                session_state['awaiting_date'] = True
            elif any(word in user_input for word in ['нет', 'не надо', 'не хочу']):
                print("User said 'no', ending session")
                response_text = "Хорошо! Если передумаете, просто скажите 'Алиса, спроси у Винного календаря'."
                session_state = {}
            else:
                print(f"Attempting to parse date from input: {user_input}")
                date = parse_date(user_input)
                if date:
                    print(f"Parsed date: {date}")
                    response_text = get_moon_sign((date[0], date[1]))
                    session_state['awaiting_date'] = True
                else:
                    print("Failed to parse date")
                    response_text = "Не поняла дату. Скажите, например: '25 августа' или 'На завтра'."
                    session_state['awaiting_date'] = True
        else:
            print("Not in awaiting_date state")
            if new_session or not user_input or any(word in user_input for word in ['сегодня', 'сейчас', 'какой день']):
                print("Returning current day info")
                response_text = get_moon_sign()
                session_state['awaiting_date'] = True
            else:
                print(f"Attempting to parse date from input: {user_input}")
                date = parse_date(user_input)
                if date:
                    print(f"Parsed date: {date}")
                    response_text = get_moon_sign((date[0], date[1]))
                    session_state['awaiting_date'] = True
                else:
                    print("Failed to parse date")
                    response_text = "Не поняла дату. Скажите, например: '25 августа' или 'На завтра'."
                    session_state['awaiting_date'] = True

        response = {
            "response": {
                "text": response_text,
                "tts": response_text,
                "end_session": False,
                "buttons": [
                    {"title": "Да", "hide": True},
                    {"title": "Нет", "hide": True}
                ]
            },
            "version": "1.0",
            "session_state": session_state
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        response = {
            "response": {
                "text": "Ошибка обработки запроса. Попробуйте еще раз.",
                "tts": "Ошибка обработки запроса. Попробуйте еще раз.",
                "end_session": False
            },
            "version": "1.0",
            "session_state": {}
        }

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response, ensure_ascii=False)
    }

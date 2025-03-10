import telebot
import re

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
BOT_TOKEN = 'YOUR_BOT_TOKEN'

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения временных данных (тема и пары вопросов-ответов)
user_data = {}


def format_output(topic, qa_pairs):
    """Форматирует результаты в нужном формате."""
    output = f"**__{topic}__**\n"
    for question, answer in qa_pairs:
        output += "——————————————————\n"
        output += f"**ЗАДАНИЕ:** {question}\n\n"
        output += f"**ОТВЕТ:** {answer}\n"
    return output


def extract_topic(text):
    """Извлекает тему из текста."""
    lines = text.split('\n')
    if len(lines) > 0:
        return lines[0].split(',')[0].strip()  # Берем первую строку до запятой, считаем темой
    return None


def extract_qa_pairs(text):
    """Извлекает пары вопросов и ответов из текста."""
    qa_pairs = []
    questions = re.findall(r"ЗАДАНИЕ:\s(.*?)(?=\nОТВЕТ|\Z)", text, re.DOTALL)
    answers = re.findall(r"ОТВЕТ:\s(.*?)(?=\nЗАДАНИЕ|\Z)", text, re.DOTALL)

    # Ensure same number of questions and answers, pair them sequentially
    min_length = min(len(questions), len(answers))
    for i in range(min_length):
        question = questions[i].strip()
        answer = answers[i].strip()

        # Check if the answer consists only of numbers
        if re.match(r"^\d+$", answer):
            answer = f"`{answer}`"
            answer = f"__(можно скопировать по нажатию)__:**: {answer}"
        qa_pairs.append((question, answer))

    return qa_pairs


@bot.message_handler(func=lambda message: message.forward_from is not None)
def handle_forwarded_message(message):
    """Обрабатывает пересланные сообщения."""
    user_id = message.chat.id
    text = message.text

    topic = extract_topic(text)
    qa_pairs = extract_qa_pairs(text)

    if user_id not in user_data:
        user_data[user_id] = {'topic': None, 'qa_pairs': []}

    # Обновляем тему, если она есть в сообщении.
    if topic:
        user_data[user_id]['topic'] = topic

    # Добавляем новые пары вопрос-ответ.
    user_data[user_id]['qa_pairs'].extend(qa_pairs)

    if user_data[user_id]['topic'] and user_data[user_id]['qa_pairs']:
        formatted_output = format_output(user_data[user_id]['topic'], user_data[user_id]['qa_pairs'])
        try:
            bot.send_message(user_id, formatted_output, parse_mode='Markdown')

        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(user_id, f"Ошибка при отправке сообщения: {e}")


        # Очищаем данные после отправки сообщения
        user_data[user_id] = {'topic': None, 'qa_pairs': []}

    else:
        bot.reply_to(message, "Сообщение получено, ожидаю остальные части.")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Отправляет приветственное сообщение и инструкцию."""
    bot.reply_to(message, """
Привет! Я бот для форматирования пересланных сообщений из МЭШ.
Просто пересылайте мне сообщения в формате:
МЭШ ответы на ЦДЗ тесты + авторешение, [дата и время]
[Тема]
[Вопросы и ответы]

Я отформатирую их в удобный вид.
""")


if __name__ == '__main__':
    bot.infinity_polling()

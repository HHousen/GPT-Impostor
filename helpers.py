import requests


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def remove_non_ascii(s):
    return "".join(c for c in s if ord(c) < 128)


def get_gpt_first_message(gpt_response, user_name):
    if gpt_response is None:
        return gpt_response
    original_first_response_message = gpt_response.strip().split("\n")[0]
    first_response_message = remove_prefix(
        original_first_response_message, f"{user_name}:"
    )
    first_response_message = remove_prefix(first_response_message, f"{user_name}")
    if first_response_message != original_first_response_message:
        return first_response_message.strip()

    first_response_message = first_response_message.strip()
    try:
        username_section, message_section = first_response_message.split(":", 1)
    except ValueError:
        return first_response_message

    message_section = message_section.strip()
    if len(username_section) <= 32 and message_section:
        return message_section

    return first_response_message


def run_gpt_inference(context, token_max_length=512):
    payload = {
        "context": context,
        "token_max_length": token_max_length,
        "temperature": 1.0,
        "top_p": 0.9,
    }
    headers = {"User-Agent": "(GPT Impostor for Discord, gptimpostor.tech)"}
    response = requests.post(
        "http://api.vicgalle.net:5000/generate", params=payload, headers=headers,
    )
    if response.status_code == 200:
        response_json = response.json()
        return response_json["text"]
    else:
        return None

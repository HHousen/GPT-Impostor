import requests


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def get_gpt_first_message(gpt_response, user_name):
    first_response_message = gpt_response.strip().split("\n")[0]
    first_response_message = remove_prefix(first_response_message, f"{user_name}:")
    first_response_message = remove_prefix(first_response_message, f"{user_name}")
    first_response_message = first_response_message.strip()
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
    ).json()
    return response["text"]

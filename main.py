from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import re

def setup():
    # load .env
    load_dotenv()
    # init Azure client
    client = AzureOpenAI(
        azure_endpoint=os.environ.get("OPENAI_PROXY_URL"),
        api_key=os.environ.get("OPENAI_PROXY_API_KEY"),
        api_version="2024-02-01",
        azure_deployment="gpt-35-turbo",
    )
    return client

def get_previous_secrets(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = [line.strip() for line in file]
        return lines
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return []

def add_new_secret(file_path, new_secret):
    try:
        with open(file_path, 'a') as file:
            file.write(new_secret + '\n')
        print(f"Appended '{new_secret}' to {file_path} successfully.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found. Please check the path.")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_secret_concept(client):
    file = "secrets.txt"
    previous_secrets = get_previous_secrets(file)
    print(', '.join(previous_secrets))

    secret_finder_prompts = [
        {"role": "system", "content": "You are a helpful chatbot"},
        {"role": "user", "content": "For the purposes of a game of 'Who am I?', in which a user is trying to guess a secret object, we need you to choose the secret. The secret object should be tangible and simple to understand. The user should not need domain specific knowledge in order to geuess the object. Your response should only contain the secret object as a single word."},
        {"role": "user", "content": "The object should not be part of the following list: '{}'".format(', '.join(previous_secrets))}
    ]

    response = client.chat.completions.create(
        messages=secret_finder_prompts,
        model="gpt-35-turbo"
    )
    response_role = response.choices[0].message.role
    response_content = response.choices[0].message.content
    print(response_content)
    add_new_secret(file, response_content)
    return response_content

def answer_user_question(client: AzureOpenAI, prompt_history):
    max_retries = 3
    allowed_responses = ["yes", "no", "unclear", "irrelevant", "not a yes or no question"]

    for i in range(max_retries):
        response = client.chat.completions.create(
            messages=prompt_history,
            model="gpt-35-turbo"
        )
        response_role = response.choices[0].message.role
        response_content = response.choices[0].message.content

        # clean response
        response_content = response_content.lower()
        regex = re.compile('[^a-zA-Z]')
        response_content = regex.sub('', response_content)

        if response_content in allowed_responses:
            return response_role, response_content
        else:
            # TODO: log retry
            pass
    return "assistant", "unclear"


if __name__ == "__main__":
    client = setup()

    game_master_prompts = [
        {"role": "system",
         "content": "You are a game master. You are playing a game of 'What am I?'. The user is associated with a secret object. Their goal is to guess their object. The user may ask yes or no questions regarding their object in order to gather clues. Only answer yes or no questions. Do not let the user know the secret object directly. You may answer with 'yes', 'no', 'unclear', 'irrelevant' or 'not a yes or no question'. The user's secret object is an apple"}
    ]

    secret = get_secret_concept(client)

    prompt_history = game_master_prompts.copy()
    while True:
        question = input("Enter Question:")
        if question == "exit":
            break

        # add user question to prompt
        prompt_history.append({"role": "user", "content": question})
        # get game master response
        response_role, response_content = answer_user_question(client, prompt_history)
        # add response to prompt history
        prompt_history.append({"role": response_role, "content": response_content})
        # show response to user
        print(response_content)


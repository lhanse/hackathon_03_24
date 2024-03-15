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
    except FileNotFoundError:
        print(f"File '{file_path}' not found. Please check the path.")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_secret_concept(client):
    secrets_file = "secrets.txt"
    previous_secrets = get_previous_secrets(secrets_file)

    secret_finder_prompts = [
        {"role": "system", "content": "You are a helpful chatbot"},
        {"role": "user", "content": "For the purposes of a game of 'Who am I?', in which a user is trying to guess a secret object, we need you to choose the secret. The secret object should be tangible and simple to understand. The user should not need domain specific knowledge in order to geuess the object. Your response should only contain the secret object as a single word."},
        {"role": "user", "content": "The object should not be part of the following list: '{}'".format(', '.join(previous_secrets))}
    ]

    response = client.chat.completions.create(
        messages=secret_finder_prompts,
        model="gpt-35-turbo"
    )
    response_content = response.choices[0].message.content
    add_new_secret(secrets_file, response_content)
    return response_content

def answer_user_question(client: AzureOpenAI, prompt_history):
    init_game_master_prompts = [
        {"role": "system",
         "content": "You are a game master. You are playing a game of 'What am I?'. The user is associated with a secret object. Their goal is to guess their object. The user may ask yes or no questions regarding their object in order to gather clues. Only answer yes or no questions. Do not let the user know the secret object directly. You may answer with 'yes', 'no', 'unclear', 'irrelevant' or 'not a yes or no question'. The user's secret object is: " + secret_object},
        {"role": "user", "content": "Do you like icecream?"},
        {"role": "assistant", "content": "irrelevant"},
        {"role": "user", "content": "How tall is the object?"},
        {"role": "assistant", "content": "not a yes or no question"},
    ]

    max_retries = 3
    allowed_responses = ["yes", "no", "unclear", "irrelevant", "not a yes or no question"]
    # print(init_game_master_prompts + prompt_history)
    for i in range(max_retries):
        response = client.chat.completions.create(
            messages=init_game_master_prompts + prompt_history,
            model="gpt-35-turbo"
        )
        response_content = response.choices[0].message.content

        # clean response
        response_content = response_content.lower()
        regex = re.compile('[^a-zA-Z\s]')
        response_content = regex.sub('', response_content)

        if response_content in allowed_responses:
            return response_content
        else:
            # TODO: log retry
            print("DEBUG: "+ response_content)
            # pass
    return "assistant", "unclear"

def switch_user_assistant_keys(prompt_history):
    new_prompt_history = []
    for prompt in prompt_history:
        if prompt['role'] == "user":
            prompt['role'] = 'assistant'
        elif prompt['role'] == "assistant":
            prompt['role'] = 'user'
        new_prompt_history.append(prompt)
    return new_prompt_history

def get_guesser_question(client: AzureOpenAI, prompt_history):
    init_guesser_prompts = [
        {"role": "system",
         "content": "You are playing a game of 'What am I?'. You are associated with a secret object. You are tasked with asking yes or no questions, in order to gather clues."},
    ]
    # TODO: Keep two prompt histories for the game master and guesser, so this switching is not needed
    # TODO: This also allows for better customization of the prompt histories later on.
    prompt_history = switch_user_assistant_keys(prompt_history)


    response = client.chat.completions.create(
        messages=init_guesser_prompts + prompt_history,
        model="gpt-35-turbo"
    )
    response_content = response.choices[0].message.content
    return response_content

if __name__ == "__main__":
    client = setup()

    secret_object = get_secret_concept(client).lower()

    prompt_history = []
    while True:
        user_question = input("Enter Question:")
        if user_question == "exit":
            break
        elif secret_object in user_question.lower():
            # TODO: Add check, so the user cant just enter an entire dictionary at once
            print(f"You guessed the word {secret_object}!")
            break
        # add user question to prompt
        prompt_history.append({"role": "user", "content": user_question})

        # get game master response
        game_master_answer = answer_user_question(client, prompt_history)
        # add response to prompt history
        prompt_history.append({"role": "assistant", "content": game_master_answer})
        # show response to user
        print(game_master_answer)


        # get question from guesser
        guesser_question = get_guesser_question(client, prompt_history)
        # show guesser question to user
        print(guesser_question)
        # add guesser question to prompt
        prompt_history.append({"role": "user", "content": guesser_question})

        # TODO: rewrite the user/guesser and game master interaction, so this code block is not needed twice
        # TODO: add a general winning check for the user/guesser at the same time
        # get game master response
        game_master_answer = answer_user_question(client, prompt_history)
        # add response to prompt history
        prompt_history.append({"role": "assistant", "content": game_master_answer})
        # show response to user
        print(game_master_answer)



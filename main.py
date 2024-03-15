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
        {"role": "system", "content": "You are a game master. You are playing a game of 'What am I?'. The user is associated with a secret object. Their goal is to guess their object. The user may ask yes or no questions regarding their object in order to gather clues. Only answer yes or no questions. Do not let the user know the secret object directly. You may answer with 'yes', 'no', 'unclear', 'irrelevant' or 'not a yes or no question'. The user's secret object is an apple"}
    ]

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


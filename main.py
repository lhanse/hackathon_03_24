from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import re
from flask import Flask,render_template,request

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

def setup_web_app(prompt_history):
    app = Flask(__name__)
    @app.route('/', methods = ['POST', 'GET'])
    def index():
        if request.method == 'GET':
            return render_template('page.html', form_data= {})
        if request.method == 'POST':
            form_data = request.form
            prompt_history.append(form_data)
            return render_template('page.html', prompt_history = prompt_history)
        
    return app

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


class LLMAgent:
    init_prompts = []
    prompt_history = []

    def __init__(self, name, client):
        self.name = name
        self.client = client
        self.prompt_history.extend(self.init_prompts)

    def append_prompt_history(self, prompt):
        self.prompt_history.append(prompt)

    def get_responses(self):
        response = self.client.chat.completions.create(
            messages=self.prompt_history,
            model="gpt-35-turbo"
        )
        response_content = response.choices[0].message.content
        self.append_prompt_history({"role": "assistant", "content": response_content})
        return response_content


class GameMaster(LLMAgent):
    max_retries = 3
    allowed_responses = ["yes", "no", "unclear", "irrelevant", "not a yes or no question"]

    init_prompts = [
        {"role": "system",
         "content": "You are a game master. You are playing a game of 'What am I?'. The user is associated with a secret object. Their goal is to guess their object. The user may ask yes or no questions regarding their object in order to gather clues. Only answer yes or no questions. Do not let the user know the secret object directly. You may answer with 'yes', 'no', 'unclear', 'irrelevant' or 'not a yes or no question'. The user's secret object is: {}"},
        {"role": "user", "content": "Do you like icecream?"},
        {"role": "assistant", "content": "irrelevant"},
        {"role": "user", "content": "How tall is the object?"},
        {"role": "assistant", "content": "not a yes or no question"},
    ]

    def __init__(self, name, client, secret):
        self.init_prompts[0]["content"] = self.init_prompts[0]["content"].format(secret)
        super().__init__(name, client)

    def get_responses(self):
        for i in range(self.max_retries):
            response = self.client.chat.completions.create(
                messages=self.prompt_history,
                model="gpt-35-turbo"
            )
            response_content = response.choices[0].message.content

            # clean response
            response_content = response_content.lower()
            regex = re.compile('[^a-zA-Z\s]')
            response_content = regex.sub('', response_content)

            if response_content in self.allowed_responses:
                self.append_prompt_history({"role": "assistant", "content": response_content})
                return response_content
            else:
                # TODO: log retry
                print("DEBUG: " + response_content)
        response_content = "unclear"
        self.append_prompt_history({"role": "assistant", "content": response_content})
        return response_content


class Guesser(LLMAgent):

    init_prompts = [
        {"role": "system",
         "content": "You are playing a game of 'What am I?'. You are associated with a secret object. You are tasked with asking yes or no questions, in order to gather clues."},
    ]

class Game:
    def __init__(self):
        self.running = True
        self.client = setup()
        self.secret_object = get_secret_concept(self.client).lower()
        self.game_master = GameMaster('Game Master', self.client, self.secret_object)
        self.guesser = Guesser('Guesser', self.client)
        self.app = setup_web_app(self.game_master.prompt_history)

    def handle_user_input(self, user_question):
        if user_question == "exit":
            self.running = False
            return
        elif self.secret_object in user_question.lower():
            # TODO: Add check, so the user cant just enter an entire dictionary at once
            print(f"You guessed the word {self.secret_object}!")
            self.running = False
            return

        # Game Master Turn
        self.game_master.append_prompt_history({"role": "user", "content": user_question})
        game_master_response = self.game_master.get_responses()

        # Display game master response
        print(game_master_response)

        # Guesser Turn
        self.guesser.append_prompt_history({"role": "assistant", "content": user_question})
        self.guesser.append_prompt_history({"role": "user", "content": game_master_response})
        guesser_question = self.guesser.get_responses()
        # TODO: Add winning check for the guesser

        # Display guesser question
        print(guesser_question)

        # Game Master Turn
        self.game_master.append_prompt_history({"role": "user", "content": guesser_question})
        game_master_response = self.game_master.get_responses()

        # Display game master response
        print(game_master_response)

if __name__ == "__main__":
    game = Game()

    app = setup_web_app(game.game_master.prompt_history)
    # app.run(host='localhost', port=5000, debug=True)
    while game.running:
        # Player Turn
        user_question = input("Enter Question: ")
        game.handle_user_input(user_question=user_question)
        
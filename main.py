from openai import AzureOpenAI
import os


def setup():
    client = AzureOpenAI(
        azure_endpoint=os.environ.get("OPENAI_BASE_URL"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        api_version="2024-02-01",
        azure_deployment="gpt-35-turbo",
    )

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are my assistent"},
            {"role": "user", "content": "What is the best tagline for an ice cream shop?"},
        ],
        model="gpt-35-turbo",
    )

    print(response.choices[0].message)




if __name__ == "__main__":
    setup()
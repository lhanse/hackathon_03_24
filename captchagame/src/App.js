import './App.css';

import {AzureKeyCredential, OpenAIClient} from '@azure/openai';
import {useState} from "react";

function App() {
    const endpoint = process.env["REACT_APP_OPENAI_PROXY_URL"];
    const azureApiKey = process.env["REACT_APP_OPENAI_PROXY_API_KEY"];
    const client = new OpenAIClient(
        endpoint,
        new AzureKeyCredential(azureApiKey),
        {apiVersion: "2024-02-01"},
    );
    const deploymentId = "gpt-4";
    const prompt = [
        {"role": "system", "content": "Ask the user a quiz question about food"}
    ];

    const [varText, setVarText] = useState("Loading...");
    function updateQuestion() {
        client.getChatCompletions(deploymentId, prompt).then(completion => {
            setVarText(completion.choices[0].message.content)
        })
    }
    
    return (
        <div className="App">
            <header className="App-header">
                <h1 className="App-question">{varText}</h1>
                <input className="App-answer" onSubmit={updateQuestion}/>
                <button className="App-submit" value={"Submit"} onClick={updateQuestion}/>
            </header>
        </div>
    );
}

export default App;

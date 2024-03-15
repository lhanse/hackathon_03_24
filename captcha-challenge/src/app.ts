async function main() {
  const { OpenAIClient, AzureKeyCredential } = require("@azure/openai");
  const dotenv = require("dotenv");
  dotenv.config();
  const endpoint = process.env["OPENAI_BASE_URL"];
  const azureApiKey = process.env["OPENAI_API_KEY"];
  const client = new OpenAIClient(
    endpoint,
    new AzureKeyCredential(azureApiKey)
  );
  const deploymentId = "gpt-35-turbo-instruct";
  const prompt = ["Generate a captcha question"];

  // Example to set a question, in a real scenario this should be dynamic or fetched from a server
  const questionInput = document.getElementById(
    "captchaQuestion"
  ) as HTMLInputElement;
  questionInput.value = "What color is the second object?";
  const result = await client.getCompletions(deploymentId, prompt);
  questionInput.value = result.choices[0].text;

  const submitButton = document.getElementById("submitAnswer");
  submitButton?.addEventListener("click", () => {
    const answerInput = document.getElementById(
      "captchaAnswer"
    ) as HTMLInputElement;
    const userAnswer = answerInput.value.trim().toLowerCase();
    // Check the answer - example logic, in a real scenario this should be more complex and secure
    if (userAnswer === "expected answer") {
      alert("Correct answer!");
    } else {
      alert("Incorrect answer, please try again.");
    }
  });
}

main().catch((err) => {
  console.error("The sample encountered an error:", err);
});

module.exports = { main };

window.onload = () => {
    // Example to set a question, in a real scenario this should be dynamic or fetched from a server
    const questionInput = document.getElementById("captchaQuestion") as HTMLInputElement;
    questionInput.value = "What color is the second object?";

    const submitButton = document.getElementById("submitAnswer");
    submitButton?.addEventListener("click", () => {
        const answerInput = document.getElementById("captchaAnswer") as HTMLInputElement;
        const userAnswer = answerInput.value.trim().toLowerCase();

        // Check the answer - example logic, in a real scenario this should be more complex and secure
        if (userAnswer === "expected answer") {
            alert("Correct answer!");
        } else {
            alert("Incorrect answer, please try again.");
        }
    });
}

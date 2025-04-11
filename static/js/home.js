function analyzeText() {
    const userInput = document.getElementById('userInput').value;

    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: userInput })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response:', data);
        alert('Server Response: ' + data.message + '\nYour Text: ' + data.input_text);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

let isApiKeyVerified = false;

window.addEventListener('DOMContentLoaded', function () {
	const savedKey = sessionStorage.getItem('apiKey');
	if (savedKey) {
		document.getElementById("apiInput").value = savedKey;
		verifyApiKey(false);
	}
});

function verifyApiKey(showAlert = true) {
	const enteredKey = document.getElementById("apiInput").value;

	sessionStorage.setItem('apiKey', enteredKey);

	fetch('/verify_api_key', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ api_key: enteredKey })
	})
	.then(response => response.json())
	.then(data => {
		const resultEl = document.getElementById("apiResult");
		resultEl.innerText = data.message;
		resultEl.style.color = data.valid ? "green" : "red";

		const analyzeBtn = document.getElementById("analyzeBtn");
		if (data.valid) {
			isApiKeyVerified = true;
			sessionStorage.setItem('apiVerified', 'true');
			analyzeBtn.disabled = false;
			analyzeBtn.style.opacity = "1";
			analyzeBtn.style.cursor = "pointer";
		} else {
			isApiKeyVerified = false;
			sessionStorage.setItem('apiVerified', 'false');
			analyzeBtn.disabled = true;
			analyzeBtn.style.opacity = "0.5";
			analyzeBtn.style.cursor = "not-allowed";
		}
	})
	.catch(error => {
		console.error('Error verifying API key:', error);
		if (showAlert) alert("Something went wrong while verifying API key.");
	});
}

let uploadedFile = null;
let currentModel = null;

function handleFileAttach() {
	const input = document.getElementById('fileInput');
	const file = input.files[0];
	const key = sessionStorage.getItem('apiKey');

	if (!file || !key) return;

	currentModel = key.split("-")[1];
	const allowed = {
		r1: ['txt'],
		r2: ['txt', 'pdf'],
		r3: ['txt', 'pdf', 'docx']
	};

	const ext = file.name.split('.').pop().toLowerCase();
	if (!allowed[currentModel]?.includes(ext)) {
		alert(`❌ ${currentModel.toUpperCase()} model does not support .${ext} files`);
		input.value = "";
		uploadedFile = null;
		document.getElementById('fileNameDisplay').innerText = "";
		document.getElementById('removeFileBtn').style.display = 'none';
		return;
	}

	uploadedFile = file;
	document.getElementById('fileNameDisplay').innerText = file.name;
	document.getElementById('removeFileBtn').style.display = 'inline';
}

function removeUploadedFile() {
	document.getElementById('fileInput').value = '';
	uploadedFile = null;
	document.getElementById('fileNameDisplay').innerText = '';
	document.getElementById('removeFileBtn').style.display = 'none';
}


function analyzeText() {
	if (!isApiKeyVerified) {
		alert("❌ Please verify your API key first!");
		return;
	}

	const inputText = document.getElementById("userInput").value;
	const apiKey = sessionStorage.getItem('apiKey'); // Use saved key
	const analyzeBtn = document.getElementById("analyzeBtn");
	const spinner = document.getElementById("loadingSpinner");

	analyzeBtn.disabled = true;
	spinner.style.display = "inline-block";

	const formData = new FormData();
	formData.append("text", inputText);
	formData.append("api_key", apiKey);
	if (uploadedFile) {
		formData.append("file", uploadedFile);
	}

	fetch('/analyze', {
		method: 'POST',
		body: formData
	})
		.then(response => {
			if (response.status === 403) {
				alert("🚫 You've reached your usage limit of 20 analyses for today.");
				return null;
			}
			if (!response.ok) {
				throw new Error("An error occurred while analyzing text.");
			}
			return response.json();
		})
		.then(data => {
			if (data) {
				document.getElementById("emotionResult").innerText = data.predicted_emotion;
				document.getElementById("polarityResult").innerText = data.predicted_polarity;
			}
		})
		.catch(error => {
			console.error('Error analyzing text:', error);
			alert("Something went wrong while trying to analyze your input.");
		})
		.finally(() => {
			spinner.style.display = "none";
			analyzeBtn.disabled = false;
		});
}

function toggleUserDropdown() {
	const dropdown = document.getElementById("userDropdown");
	dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

window.onclick = function(event) {
	if (!event.target.matches('#userBtn')) {
		const dropdown = document.getElementById("userDropdown");
		if (dropdown && dropdown.style.display === "block") {
			dropdown.style.display = "none";
		}
	}
}

function logout() {
    sessionStorage.removeItem('apiKey');
    sessionStorage.removeItem('apiVerified');
    window.location.href = "/logout";
}

document.addEventListener('DOMContentLoaded', function () {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');

    const storedApiKey = sessionStorage.getItem('apiKey');
    if (storedApiKey) {
        document.getElementById('apiInput').value = storedApiKey;
        analyzeBtn.disabled = false;
    }
});

function handleUsageRedirect() {
	const key = sessionStorage.getItem('apiKey');
	const isVerified = sessionStorage.getItem('apiVerified');

	if (key && isVerified === 'true') {
		window.location.href = `/usage?api_key=${encodeURIComponent(key)}`;
	} else {
		window.location.href = '/apis';
	}
}

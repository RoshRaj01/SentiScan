function generateKey() {
	const selectedModel = document.getElementById('modelSelector').value;

	fetch("/generate_new_key", {
		method: "POST",
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ model: selectedModel }) // 🛠 send selected model
	})
	.then(res => res.json())
	.then(data => {
		if (data.api_key) {
			const keyList = document.getElementById("keyList");
			const newItem = document.createElement("li");
			newItem.innerHTML = `
                <code>${data.api_key}</code>
                <button class="small-btn" onclick="copyKey('${data.api_key}', this)">📋 Copy</button>
                <button class="small-btn delete-btn" onclick="deleteKey('${data.api_key}', this)">🗑️ Delete</button>
            `;
			keyList.appendChild(newItem);
		}
	})
	.catch(err => {
		console.error("Error:", err);
		alert("Could not generate new key.");
	});
}

function copyKey(apiKey, btnElement) {
	navigator.clipboard.writeText(apiKey)
	.then(() => {
		const originalText = btnElement.innerText;
		btnElement.innerText = "✅ Copied";
		btnElement.disabled = true;

		setTimeout(() => {
			btnElement.innerText = originalText;
			btnElement.disabled = false;
		}, 3000);
	})
	.catch(err => {
		console.error('❌ Failed to copy:', err);
	});
}


function deleteKey(apiKey, btnElement) {
	if (!confirm("⚠️ Are you sure you want to permanently delete this API key?")) {
		return;
	}

	fetch("/delete_api_key", {
		method: "POST",
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ api_key: apiKey })
	})
	.then(res => res.json())
	.then(data => {
		if (data.success) {
			const listItem = btnElement.parentElement;
			listItem.remove();
			alert("✅ API key deleted successfully!");
		} else {
			alert("❌ Failed to delete API key.");
		}
	})
	.catch(err => {
		console.error("Error:", err);
		alert("❌ Error deleting API key.");
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
    window.location.href = "/logout";
}
let latestGeneratedKey = "";

function generateKey() {
	const selectedModel = document.getElementById('modelSelector').value;

	fetch("/generate_new_key", {
		method: "POST",
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ model: selectedModel })
	})
	.then(res => res.json())
	.then(data => {
		if (data.api_key) {
			latestGeneratedKey = data.api_key;
			document.getElementById("newApiKeyDisplay").textContent = latestGeneratedKey;
			new bootstrap.Modal(document.getElementById('projectModal')).show(); // Show modal

			// Load projects
			fetch("/get_projects")
				.then(res => res.json())
				.then(projects => {
					const select = document.getElementById("projectDropdown");
					select.innerHTML = "";
					projects.forEach(p => {
						const opt = document.createElement("option");
						opt.value = p._id;
						opt.textContent = p.name;
						select.appendChild(opt);
					});
				});
		}
	})
	.catch(err => {
		console.error("Error:", err);
		alert("Could not generate new key.");
	});
}
function assignProjectToApi() {
	const mode = document.getElementById("assignMode").value;
	if (!latestGeneratedKey) return alert("No key to assign.");

	if (mode === "new") {
		const name = document.getElementById("newProjName").value.trim();
		if (!name) return alert("Enter a project name");

		fetch("/create_project", {
			method: "POST",
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ name, api_key: latestGeneratedKey })
		})
		.then(() => location.reload());
	} else {
		const id = document.getElementById("projectDropdown").value;
		if (!id) return alert("Pick a project");

		fetch("/assign_project", {
			method: "POST",
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ project_id: id, api_key: latestGeneratedKey })
		})
		.then(() => location.reload());
	}
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
			const row = btnElement.closest(".api-row");
			if (row) row.remove();
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

function loadProjects() {
	fetch("/get_projects")
		.then(res => res.json())
		.then(projects => {
			const select = document.getElementById("projectDropdown");
			select.innerHTML = "";
			projects.forEach(p => {
				const opt = document.createElement("option");
				opt.value = p._id;
				opt.textContent = p.name;
				select.appendChild(opt);
			});
		})
		.catch(err => console.error("Error loading projects:", err));
}


document.addEventListener("DOMContentLoaded", () => {
	document.getElementById("assignMode").addEventListener("change", e => {
		const mode = e.target.value;
		document.getElementById("newProjInput").style.display = mode === "new" ? "block" : "none";
		document.getElementById("existingProjSelect").style.display = mode === "existing" ? "block" : "none";
	});
});

function deleteProject(projectId, btnElement) {
	if (!confirm("⚠️ This will delete the entire project. Continue?")) return;

	fetch("/delete_project", {
		method: "POST",
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ project_id: projectId })
	})
	.then(res => res.json())
	.then(data => {
		if (data.success) {
			const block = btnElement.closest(".project-block");
			if (block) block.remove();
			alert("✅ Project deleted!");
		} else {
			alert("❌ Failed to delete project.");
		}
	})
	.catch(err => {
		console.error("Error:", err);
		alert("❌ Something went wrong.");
	});
}

function editProjectName(projectId) {
	const nameSpan = document.querySelector(`.project-name[data-project-id="${projectId}"]`);
	const currentName = nameSpan.textContent.trim();

	const newName = prompt("📝 Enter new project name:", currentName);
	if (!newName || newName === currentName) return;

	fetch("/rename_project", {
		method: "POST",
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ project_id: projectId, new_name: newName })
	})
	.then(res => res.json())
	.then(data => {
		if (data.success) {
			nameSpan.textContent = newName;
			alert("✅ Project renamed!");
		} else {
			alert("❌ Rename failed.");
		}
	})
	.catch(err => {
		console.error("Rename error:", err);
		alert("❌ Something went wrong.");
	});
}

function analyzeProject(projectId) {
    fetch("/project_analysis", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return alert("❌ " + data.error);

        alert(
            `📊 Project Analysis:\n\n🧠 Emotion: ${data.overall_emotion}\n⚖️ Polarity: ${data.overall_polarity}\n\n📝 Summary: ${data.summary}`
        );
    })
    .catch(err => {
        console.error("Analysis error:", err);
        alert("❌ Failed to analyze project.");
    });
}

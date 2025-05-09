// Toggle dropdown menu
function toggleUserDropdown() {
    const dropdown = document.getElementById("userDropdown");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

// Close dropdown if clicked outside
window.onclick = function(event) {
    const userBtn = document.getElementById('userBtn');
    const dropdown = document.getElementById('userDropdown');

    if (!userBtn.contains(event.target) && !dropdown.contains(event.target)) {
        if (dropdown.style.display === "block") {
            dropdown.style.display = "none";
        }
    }
};

function logout() {
    sessionStorage.removeItem('apiKey');
    window.location.href = "/logout";
}
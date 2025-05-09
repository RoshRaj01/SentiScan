document.getElementById("signupForm").addEventListener("submit", function (e) {
	const password = document.getElementById("passwordInput").value;
	const phoneInput = document.getElementById("phoneInput");
	const phone = phoneInput.value;

	const passwordError = document.getElementById("passwordError");
	const phoneError = document.getElementById("phoneError");

	const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;
	const phoneRegex = /^\d{10}$/;

	let prevent = false;

	if (!strongRegex.test(password)) {
		passwordError.style.display = "block";
		document.getElementById("passwordInput").value = "";
		prevent = true;
	} else {
		passwordError.style.display = "none";
	}

	if (!phoneRegex.test(phone)) {
		phoneError.style.display = "block";
		phoneInput.value = "";
		prevent = true;
	} else {
		phoneError.style.display = "none";
	}

	if (prevent) {
		e.preventDefault();
	}
});

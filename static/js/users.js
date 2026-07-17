(function () {
    const userForm = document.querySelector("[data-user-form]");
    const clientSelect = document.querySelector("[data-client-select]");
    const dataElement = document.getElementById("client-callcenter-data");
    const listTarget = document.querySelector("[data-client-callcenter-list]");

    let callcentersByClient = {};

    if (dataElement) {
        try {
            callcentersByClient = JSON.parse(dataElement.textContent);
        } catch (error) {
            callcentersByClient = {};
        }
    }

    function createStatusBadge(isActive) {
        const badge = document.createElement("em");

        badge.className = (
            "status-pill "
            + (isActive ? "is-active" : "is-inactive")
        );
        badge.textContent = isActive ? "Activo" : "Inactivo";

        return badge;
    }

    function renderCallcenters() {
        if (!clientSelect || !listTarget) {
            return;
        }

        const clientId = clientSelect.value;
        const callcenters = callcentersByClient[clientId] || [];
        const previewTitle = document.querySelector(
            "[data-client-preview] > strong"
        );

        listTarget.innerHTML = "";

        if (!clientId) {
            const message = document.createElement("p");

            if (previewTitle) {
                previewTitle.textContent = "Call centers disponibles";
            }

            message.textContent = (
                "Selecciona un cliente para ver sus call centers."
            );
            listTarget.appendChild(message);
            return;
        }

        if (previewTitle) {
            previewTitle.textContent = (
                "Este usuario puede gestionar: "
                + callcenters.length
                + (
                    callcenters.length === 1
                        ? " call center"
                        : " call centers"
                )
            );
        }

        if (callcenters.length === 0) {
            const message = document.createElement("p");

            message.textContent = (
                "Este cliente aún no tiene call centers registrados."
            );
            listTarget.appendChild(message);
            return;
        }

        const list = document.createElement("ul");

        list.className = "client-callcenter-list";

        callcenters.forEach(function (callcenter) {
            const item = document.createElement("li");
            const text = document.createElement("span");
            const name = document.createElement("strong");
            const codename = document.createElement("small");

            name.textContent = callcenter.name;
            codename.textContent = callcenter.codename;

            text.appendChild(name);
            text.appendChild(codename);
            item.appendChild(text);
            item.appendChild(
                createStatusBadge(callcenter.is_active)
            );
            list.appendChild(item);
        });

        listTarget.appendChild(list);
    }

    function getField(name) {
        if (!userForm) {
            return null;
        }

        return userForm.querySelector("[name='" + name + "']");
    }

    function getFieldWrapper(field) {
        return field ? field.closest(".form-field") : null;
    }

    function clearError(field) {
        const wrapper = getFieldWrapper(field);

        if (!field || !wrapper) {
            return;
        }

        field.removeAttribute("aria-invalid");
        wrapper.classList.remove("has-error");

        const error = wrapper.querySelector(".inline-field-error");

        if (error) {
            error.remove();
        }
    }

    function showError(field, message) {
        const wrapper = getFieldWrapper(field);

        if (!field || !wrapper) {
            return;
        }

        field.setAttribute("aria-invalid", "true");
        wrapper.classList.add("has-error");

        let error = wrapper.querySelector(".inline-field-error");

        if (!error) {
            error = document.createElement("span");
            error.className = "inline-field-error";
            wrapper.appendChild(error);
        }

        error.textContent = message;
    }

    function setFormAlert(message) {
        if (!userForm) {
            return;
        }

        const alert = userForm.querySelector("[data-form-alert]");

        if (!alert) {
            return;
        }

        if (!message) {
            alert.hidden = true;
            alert.textContent = "";
            return;
        }

        alert.hidden = false;
        alert.textContent = message;
    }

    function validateUserForm() {
        if (!userForm) {
            return true;
        }

        const username = getField("username");
        const email = getField("email");
        const client = getField("client");
        const password = getField("password1") || getField("new_password1");
        const passwordConfirm = (
            getField("password2") || getField("new_password2")
        );
        const fields = [
            username,
            email,
            client,
            password,
            passwordConfirm,
        ];
        let firstInvalidField = null;

        fields.forEach(clearError);
        setFormAlert("");

        function fail(field, message) {
            showError(field, message);

            if (!firstInvalidField) {
                firstInvalidField = field;
            }
        }

        if (username && username.value.trim() === "") {
            fail(username, "Escribe un usuario.");
        }

        if (client && client.value === "") {
            fail(client, "Selecciona un cliente.");
        }

        if (email && email.value.trim() && !email.checkValidity()) {
            fail(email, "Escribe un email válido.");
        }

        if (password && password.value === "") {
            fail(password, "Escribe una contraseña.");
        }

        if (passwordConfirm && passwordConfirm.value === "") {
            fail(passwordConfirm, "Confirma la contraseña.");
        }

        if (
            password
            && passwordConfirm
            && password.value
            && passwordConfirm.value
            && password.value !== passwordConfirm.value
        ) {
            fail(passwordConfirm, "Las contraseñas no coinciden.");
        }

        if (firstInvalidField) {
            setFormAlert(
                "Revisa los campos marcados antes de guardar."
            );
            firstInvalidField.focus();
            return false;
        }

        return true;
    }

    if (clientSelect) {
        clientSelect.addEventListener("change", renderCallcenters);
        clientSelect.addEventListener("change", function () {
            clearError(clientSelect);
        });
    }

    if (userForm) {
        userForm.addEventListener("submit", function (event) {
            if (!validateUserForm()) {
                event.preventDefault();
            }
        });

        userForm.addEventListener("input", function (event) {
            if (event.target.matches("input, select")) {
                clearError(event.target);
                setFormAlert("");
            }
        });
    }
}());

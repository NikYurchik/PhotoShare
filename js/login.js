async function postLoginAsJson({ url, formData }) {
    const plainFormData = Object.fromEntries(formData.entries());
    const formDataJsonString = JSON.stringify(plainFormData);

    const fetchOptions = {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        credentials: "include",
        body: formDataJsonString,
    };

    const response = await fetch(url, fetchOptions);

    if (!response.ok) {
        let errorMessage = await response.text();
        if (!Boolean(errorMessage)) {
            errorMessage = "HTTP error " + response.status;
        }
        throw new Error(errorMessage);
    }

    return response;
}

async function handleLoginSubmit(event) {
    event.preventDefault();

    let inp = document.getElementsByClassName('inp-error');
    for (let i = 0; i < inp.length; i++) {
        inp[i].textContent = "";
    }

    const form = event.currentTarget;
    const url = String(form.baseURI) + "api/auth/login";

    let responseData = undefined;
    let isReload = false;
    let isRedirect = false;
    let urlRedirect = "";

    try {
        const formData = new FormData(form);
        responseData = await postLoginAsJson({ url, formData });

        if (responseData.redirected) {
            isRedirect = true;
            urlRedirect = await check_redirect(responseData.url);
        }

        const responseJson = await responseData.json();
        const succs = responseJson.detail.success;
        const errs = responseJson.detail.errors;

        if (Boolean(errs)) {
            await errorsHandling(errs);
        }
        else if (Boolean(succs)) {
            for (const suc of succs) {
                if (suc.key == "redirect") {
                    isRedirect = true;
                    urlRedirect = suc.value;
                } 
                if (suc.key == "reload") {
                    isReload = true;
                } 
                else if (suc.key == "message") {
                    alert(suc.value)
                }
            }
        }

    } catch (error) {
        console.error(error);
        alert("Login " + error);
    }

    if (isRedirect) {
        if (Boolean(urlRedirect)) {
            // responseData.redirected = true;
            // responseData.status = 302;
            window.location.href = `${urlRedirect}`;
        } else {
            alert("Redirect.value is not URL");
        }
    }
    else if (isReload) {
        window.location.reload()
    }
}

async function handleLogoutClick(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const url = String(form.baseURI) + "api/auth/logout";
    console.log(url);

    let responseData = undefined;
    let isReload = false;

    try {
        const fetchOptions = {
            method: "POST",
        };

        responseData = await fetch(url, fetchOptions);

        if (!responseData.ok) {
                const errorMessage = await responseData.text();
                alert(errorMessage);
        }
        else {
            const responseJson = await responseData.json();
            const succs = responseJson.detail.success;
            const errs = responseJson.detail.errors;

            if (Boolean(errs)) {
                await errorsHandling(errs);
            }
            else if (Boolean(succs)) {
                for (const suc of succs) {
                    if (suc.key == "message") {
                        alert(suc.value);
                    }
                    else if (suc.key == "reload") {
                        isReload = true;
                    }
                }
            }
        }
    } catch (error) {
        console.error(`Error: ${error}`);
        alert(`Error: ${error}`);
        isRedirect = false;
        isReload = true;
    }

    if (isReload) {
        window.location.reload();
    }
}

const loginForm = document.getElementById("login-subscription");
if (Boolean(loginForm)) {
    loginForm.addEventListener("submit", handleLoginSubmit);
}
const logoutForm = document.getElementById("btn-logout");
if (Boolean(logoutForm)) {
    logoutForm.addEventListener("click", handleLogoutClick);
}

const refs = {
    openModalBtn: document.querySelector("[data-modal-open]"),
    closeModalBtn: document.querySelector("[data-modal-close]"),
    modal: document.querySelector("[data-modal]"),
};

if (Boolean(refs.openModalBtn)) {
    refs.openModalBtn.addEventListener("click", toggleModal);
}
refs.closeModalBtn.addEventListener("click", toggleModal);

function toggleModal() {
    document.body.classList.toggle("modal-open")
    refs.modal.classList.toggle("is-hidden");
}

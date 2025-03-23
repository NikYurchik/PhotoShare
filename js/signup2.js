(() => {
    async function postFormDataAsJson({ url, formData }) {
        const plainFormData = Object.fromEntries(formData.entries());
        const formDataJsonString = JSON.stringify(plainFormData);

        const fetchOptions = {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
            },
            body: formDataJsonString,
        };

        const response = await fetch(url, fetchOptions);

        if (!response.ok) {
            const errorMessage = await response.text();
            throw new Error(errorMessage);
        }

        return response;
    }

async function handleFormSubmit(event) {
        event.preventDefault();

        let inp = document.getElementsByClassName('inp-error');
        for (let i = 0; i < inp.length; i++) {
            inp[i].textContent = "";
        }

        const form = event.currentTarget;
        const url = form.action;

        let responseData = undefined;
        let isRedirect = false;
        let urlRedirect = "";

        try {
            const formData = new FormData(form);
            responseData = await postFormDataAsJson({ url, formData });

            if (responseData.redirected) {
                isRedirect = true;
                urlRedirect = responseData.url;
                if (urlRedirect.indexOf("?") >= 0) {
                    let urlSplit = urlRedirect.split("?");
                    urlRedirect = urlSplit[0];
                    let spr = "?";
                    let urlQ = urlSplit[1];                 // Строка параметров
                    if (urlQ.indexOf("&") >= 0) {           // Несколько параметров
                        urlQuery = urlQ.split("&");             // Массив параметров
                        for (urlQ of urlQuery) {
                            if (uQ1.indexOf("message=") == 0) {
                                alert(decodeURI(uQ1.substr(8)));               // Выводим сообщение
                            }
                            else {
                                urlRedirect = urlRedirect + spr + uQ1;  // Возвращаем параметр в URL
                                spr = "&";
                            }
                        }
                    }
                    else if (urlQ.indexOf("message=") == 0) {
                        alert(decodeURI(urlQ.substr(8)));                  // Выводим сообщение
                    }
                    else {
                        urlRedirect = urlRedirect + spr + urlQ;     // Возвращаем параметр в URL
                    }
                }
            }

            const responseJson = await responseData.json();
            const succs = responseJson.detail.success;
            const errs = responseJson.detail.errors;

            if (Boolean(errs)) {
                for (const err of errs) {
                    let element = document.getElementById(err.key);
                    element.textContent = err.value;
                }
            }
            else if (Boolean(succs)) {
                for (const suc of succs) {
                    if (suc.key == "redirect") {
                        isRedirect = true;
                        urlRedirect = suc.value;
                    } 
                    else if (suc.key == "message") {
                        alert(suc.value)
                    }
                }
            }

        } catch (error) {
            console.error(error);
        }

        if (isRedirect) {
            if (Boolean(urlRedirect)) {
                // alert("Redirect: " + urlRedirect);
                responseData.redirected = true;
                responseData.status = 302;
                window.location.href = `${urlRedirect}`;
            } else {
                alert("Redirect.value is not URL");
            }
        }
    }

    const exampleForm = document.getElementById("subscription");
    exampleForm.addEventListener("submit", handleFormSubmit);
})();

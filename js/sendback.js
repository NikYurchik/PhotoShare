class SendBackEnd
{
    constructor() {
        this.response = undefined;
        this.isReload = false;
        this.isRedirect = false;
        this.urlRedirect = '';
    }
    
    async fnFetch(self, url, fetchOptions, fnError, fnSucces) {   // self - экземпляр класса
        self.response = undefined;
        self.isReload = false;
        self.isRedirect = false;
        self.urlRedirect = '';
        try {
            self.response = await fetch(url, fetchOptions);
            if (!self.response.ok) {
                const errorMessage = await response.text();
                throw new Error(errorMessage);
            }
            if (self.response.redirected) {
                self.isRedirect = true;
                self.urlRedirect = await check_redirect(self.response.url);
            }
            else {
                const responseJson = await self.response.json();
                const succs = responseJson.detail.success;
                const errs = responseJson.detail.errors;
        
                if (Boolean(errs)) {
                    if (Boolean(fnError)) {
                        await fnError(errs);
                    } else {
                        await errorsHandling(errs);
                    }
                }
                else if (Boolean(succs)) {
                    for (const suc of succs) {
                        if (suc.key === "redirect") {
                            self.isRedirect = true;
                            self.urlRedirect = suc.value;
                        } 
                        else if (suc.key === "message") {
                            alert(`Message: ${suc.value}`);
                        }
                        else if (suc.key === "reload") {
                            self.isReload = true;
                        }
                        if (Boolean(fnSucces)) {
                            await fnSucces(suc.key, suc.value);
                        }
                    }
                }
            }
        } catch (error) {
            console.error(`Error: ${error}`);
            alert(`Error: ${error}`);
            self.isRedirect = false;
            self.isReload = true;
        }

        if (self.isRedirect) {
            if (!Boolean(self.urlRedirect)) {
                alert("Redirect.value is not URL");
                self.urlRedirect = '/';
            }
            window.location.href = `${self.urlRedirect}`;
        }
        else if (self.isReload) {
            window.location.reload();
        }
    }
}

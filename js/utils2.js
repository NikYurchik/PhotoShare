function addParamToURL(link, param, param2, param3, param4, param5) {
    let par = param.split('=');
    param2 = (Boolean(param2)) ? param2 : '?=?';
    param3 = (Boolean(param3)) ? param3 : '?=?';
    param4 = (Boolean(param4)) ? param4 : '?=?';
    param5 = (Boolean(param5)) ? param5 : '?=?';
    let par2 = param2.split('=');
    let par3 = param3.split('=');
    let par4 = param4.split('=');
    let par5 = param5.split('=');
    let p1 = link.split('?');
    let p2 = [];
    if (p1.length > 1) {
        p2 = p1[1].split('&');
        for (let j = 0; j < p2.length; j++) {
            let p3 = p2[j].split('=');
            if (p3[0] === par[0]) {
                p2[j] = param;
                param = '';
            } else if (p3[0] === par2[0]) {
                p2[j] = param2;
                param2 = '';
            } else if (p3[0] === par3[0]) {
                p2[j] = param3;
                param3 = '';
            } else if (p3[0] === par4[0]) {
                p2[j] = param4;
                param4 = '';
            } else if (p3[0] === par5[0]) {
                p2[j] = param5;
                param5 = '';
            }
        }
    }
    if (Boolean(param)) {
        p2.push(param);
    }
    if (Boolean(param2) && param2 !== '?=?') {
        p2.push(param2);
    }
    if (Boolean(param3) && param3 !== '?=?') {
        p2.push(param3);
    }
    if (Boolean(param4) && param4 !== '?=?') {
        p2.push(param4);
    }
    if (Boolean(param5) && param5 !== '?=?') {
        p2.push(param5);
    }
    p1[1] = p2.join('&');
    link = p1.join('?');
    return link;
}

function checkMessageInURL(link) {
    let p1 = link.split('?');
    if (p1.length > 1) {
        let p2 = p1[1].split('&');
        let idx = -1;
        for (let j = 0; j < p2.length; j++) {
            let p3 = p2[j].split('=');
            if (p3[0] === 'message') {
                alert(decodeURI(p3[1]));               // Выводим сообщение
                idx = j;
            }
        }
        if (idx >= 0) {
            let pt = [];
            for (let i = 0; i < p2.length; i++) {
                if (i !== idx) {
                    pt.push(p2[i]);
                }
            }
            p2 = pt;
        }
        p1[1] = p2.join('&');
        link = p1.join('?');
    }
    return link;
}

async function check_redirect(urlRedirect) {
    urlRedirect = checkMessageInURL(urlRedirect);
    return urlRedirect
}

async function errorsHandling(errors) {
    for (const err of errors) {
        let element = document.getElementById(err.key);
        if (Boolean(element)) {
            element.textContent = err.value;
        }
        else if (err.key == "message" || err.key == "error-msg") {
            alert(`Error message: ${err.value}`);
        }
        else {
            console.log(err)
            alert(`Error response: ${err}`)
        }
    }
}


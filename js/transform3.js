// Import the Cloudinary class.
// import {Cloudinary} from "/node_modules/@cloudinary/url-gen";

// Create a Cloudinary instance and set your cloud name.
// const cld = new Cloudinary({
//   cloud: {
//     cloudName: 'dqglsxwms'
//   }
// });

class photoTransform
{
    constructor(qualifiers, trans_data, id_qualifiers) {
        this.id_qualifiers = id_qualifiers;
        this.qualifiers = qualifiers;
        this.trans_data = trans_data;
        this.depends_list = [];
        // 1. Управляемый элемент.
        //   1.1. dep_id_ch - Квалификатор (id чек-бокса).
        //   1.3. dep_value - значение зависимой команды.
        //   1.5. dep_id - id управляемой детали.
        //
        // 2. Управляющий элемент.
        //   2.1. aff_id_ch - Квалификатор (id чек-бокса).
        //   2.3. aff_value - управляющее значение команды.
        //
        // {dep_id_ch, dep_value, dep_id, aff_id_ch, aff_value}
    }

    setDepends(dep_id_ch, dep_value, dep_id, aff_id_ch, aff_value) {
        // Сохранить связку Depends - связь управляемого и управляющего элементов.
        let depn = {"dep_id_ch": dep_id_ch,
                    "dep_value": dep_value,
                    "dep_id": dep_id,
                    //
                    "aff_id_ch": aff_id_ch,
                    "aff_value": aff_value};
        for (let i = 0; i < this.depends_list.length; i++) {
            let dep = this.depends_list[i];
            if (dep.dep_id_ch === dep_id_ch && dep.dep_value === dep_value && dep.dep_id === dep_id &&
                dep.aff_id_ch === aff_id_ch && dep.aff_value === aff_value) {
                    this.depends_list[i] = depn;
                    return;
            }
        }
        this.depends_list.push(depn);
    }

    getDepends(aff_id_ch, value) {     // Получить список зависимых элементов
        let res = [];
        for (let i = 0; i < this.depends_list.length; i++) {
            let depl = this.depends_list[i];
            if (depl.aff_id_ch === aff_id_ch && (!Boolean(value) || depl.aff_value === value)) {
                res.push(depl);
            }
        }
        return res;
    }

    getAffects(dep_id_ch, value) {    // Получить список управляющих элементов
        let res = [];
        for (let i = 0; i < this.depends_list.length; i++) {
            let depl = this.depends_list[i];
            if (depl.dep_id_ch === dep_id_ch && (!Boolean(value) || depl.dep_value === value)) {
                res.push(depl);
            }
        }
        return res;
    }

    getElementValue(element) {
        let elem_val = document.getElementById(element);  // Элемент ввода команды
        let value = elem_val.value;
        if (elem_val.nodeName === 'UL') {
            let res = this.getRadioCommand(elem_val);
            value = res.val;
        }
        return value;
    }

    toggleDepends(qual_name) {
        // Переключение видимости зависимого элемента .
        let is_hidden = true;
        if (Boolean(qual_name)) {
            // Управляющий элемент
            let qualifier = this.qualifiers[qual_name];               // Квалификатор
            let prefix =  (Boolean(qualifier.prefix)) ? qualifier.prefix : qual_name[0];
            let elem_ch = document.getElementById(qual_name);   // Чек-бокс квалификатора
            if (elem_ch.checked) {
                let value = this.getElementValue(`${prefix}_value`); // Значение команды

                let depl = this.getDepends(qual_name, value);        // Получить список зависимых элементов
                if (depl.length > 0) {
                    is_hidden = false;
                    for (let i = 0; i < depl.length; i++) {         // Перебор зависимых элементов
                        let dep = depl[i];
                        let dep_id_ch = dep.dep_id_ch                  // Квалификатор зависимого элемента
                        let dep_qual = this.qualifiers[dep_id_ch];
                        let dep_pref = dep_qual.prefix;
                        let dep_ch = document.getElementById(dep_id_ch);   // Чек-бокс квалификатора зависимого элемента
                        let dep_det = document.getElementById(dep.dep_id);      // Зависимая деталь
                        let title = dep_det.previousSibling;
                        if (dep_ch.checked) {
                            let dep_val = this.getElementValue(`${dep_pref}_value`);  // Значение команды зависиммого элемента
                            if (dep_val === dep.dep_value) {
                                dep_det.classList.remove("hidden");              // Снять hidden с зависиммого элемента
                                if (Boolean(title) && title.nodeName === 'P') {
                                    title.classList.remove("hidden");
                                }
                                continue;
                            }
                        }
                        dep_det.classList.add("hidden");    // Скрыть зависимый элемент
                        if (Boolean(title) && title.nodeName === 'P') {
                            title.classList.add("hidden");
                        }
                    }
                }
            } 
            if (is_hidden) {
                let depl = this.getDepends(qual_name);        // Получить список зависимых элементов
                for (let i = 0; i < depl.length; i++) {         // Перебор зависимых элементов
                    let dep = depl[i];
                    let dep_det = document.getElementById(dep.dep_id);      // Зависимая деталь
                    if (Boolean(dep_det)) {
                        let title = dep_det.previousSibling;
                        dep_det.classList.add("hidden");                    // Скрыть зависимый элемент
                        if (Boolean(title) && title.nodeName === 'P') {
                            title.classList.add("hidden");
                        }
                    }
                }
            }
            // Зависимый элемент
            is_hidden = true;
            if (elem_ch.checked) {
                let value = this.getElementValue(`${prefix}_value`);     // Значение команды

                let affl = this.getAffects(qual_name, value);    // Получить список управляющих элементов
                if (affl.length > 0) {
                    is_hidden = false;
                    for (let i = 0; i < affl.length; i++) {             // Перебор управляющих элементов
                        let aff = affl[i];
                        let aff_id_ch = aff.aff_id_ch                   // Квалификатор управляющего элемента
                        let aff_qual = this.qualifiers[aff_id_ch];
                        let aff_pref = aff_qual.prefix;
                        let aff_ch = document.getElementById(aff_id_ch);   // Чек-бокс квалификатора управляющего элемента
                        let dep_det = document.getElementById(aff.dep_id);      // Зависимая деталь
                        let title = dep_det.previousSibling;
                        if (aff_ch.checked) {
                            let aff_val = this.getElementValue(`${aff_pref}_value`);  // Значение команды управляющего элемента
                            if (aff_val === aff.aff_value) {
                                dep_det.classList.remove("hidden");          // Снять hidden с зависиммого элемента
                                if (Boolean(title) && title.nodeName === 'P') {
                                    title.classList.remove("hidden");
                                }
                                continue;
                            }
                        }
                        dep_det.classList.add("hidden");    // Скрыть зависимый элемент
                    }
                }
            }
            if (is_hidden ) {
                let depl = this.getAffects(qual_name);               // Получить список зависимых элементов
                for (let i = 0; i < depl.length; i++) {         // Перебор зависимых элементов
                    let dep = depl[i];
                    let dep_det = document.getElementById(dep.dep_id);      // Зависимая деталь
                    if (Boolean(dep_det)) {
                        let title = dep_det.previousSibling;
                        dep_det.classList.add("hidden");                    // Скрыть зависимый элемент
                        if (Boolean(title) && title.nodeName === 'P') {
                            title.classList.add("hidden");
                        }
                    }
                }
            }
        }
    }

    getTitle(txt, isCapital=true) {
        let tmp = "";
        if (Boolean(txt)) {
            let idx = txt.indexOf(':') + 1;
            if (idx === 0) {
                idx = txt.indexOf('.') + 1;
                idx = (idx > 1) ? 0 : idx;
            }
            tmp = (idx > 0) ? txt.slice(idx) : txt;
            tmp = tmp.replaceAll(',','').replaceAll('<','').replaceAll('>','').replaceAll('_',' ');

            idx = tmp.indexOf('.');
            if (idx < 0) {
                idx = tmp.indexOf(';');
            }
            tmp = (idx < 0) ? tmp : tmp.slice(0, idx);

            idx = tmp.indexOf(':');
            if (isCapital) {
                tmp = (idx >= 0) ? tmp.slice(0, idx).toUpperCase() + tmp.slice(idx) : tmp[0].toUpperCase() + tmp.slice(1);
            }
        }
        return tmp;
    }

    create_list(prefix, list_value, num_det, title, required, is_hidden) {
        let tmp = list_value.map((grav) => `<option value="${grav.value}">${grav.value}</option>`).join("");
        if (!required) {
            tmp = '<option value=""></option>' + tmp;
        }
        let hover = ` onmouseover="setHover('${prefix}_ds${num_det}')"  onmouseout="offHover('${prefix}_ds${num_det}')"`;
        let ttl = (Boolean(title)) ? `<p class="item-trans ${is_hidden}" id="${prefix}p_ds${num_det}">${this.getTitle(title)}</p>` : '';
        tmp = `${ttl}<select class="sel-inp ${is_hidden}" id="${prefix}_ds${num_det}"${hover}>${tmp}</select>`; 
        return tmp;
    }

    create_number(prefix, detail, num_det, title, isFloat, required, is_hidden) {
        let r_min = '';
        let r_max = '';
        let r_val = '';
        let t_min = 0;
        const req = (Boolean(required)) ? ' required' : '';
        if (Boolean(detail.min)) {
            t_min = (isFloat) ? detail.min * 100 : detail.min * 1;
            r_min = ` min="${t_min}"`;
        }
        if (Boolean(detail.max)) {
            let t_max = (isFloat) ? detail.max * 100 : detail.max * 1;
            r_max = ` max="${t_max}"`;
        }
        if (Boolean(detail.default)) {
            let t_val = (isFloat) ? detail.default * 100 : detail.default * 1;
            r_val = ` value="${t_val}"`;
        } else if (Boolean(required)) {
            r_val = ` value="${t_min}"`;
        }
        title = (isFloat && Boolean(title)) ? `${title} (%)` : title;
        let r_desc = detail.description;
        let tmp = (Boolean(title)) ? `<p class="item-trans ${is_hidden}" id="${prefix}p_di${num_det}">${this.getTitle(title)}</p>` : '';
        let hover = ` onmouseover="setHover('${prefix}_di${num_det}')"  onmouseout="offHover('${prefix}_di${num_det}')"`;
        tmp = tmp + `<input type="number"${r_min}${r_max}${r_val} class="group-inp ${is_hidden}"${req} id="${prefix}_di${num_det}"${hover}>`;
        return tmp;
    }

    setDescription(content, description) {
        let res = content;
        if (Boolean(description)) {
            res = `<div class="dropdown-item">${content}<p class="dropdown-desc hidden">${description}</p></div>`;
        }
        return res;
    }

    setHover(id) {
        const elem = document.getElementById(id);
        const p = elem.nextElementSibling;
        if (Boolean(p) && p.nodeName === 'P') {
            p.classList.remove("hidden");
        }
    }

    offHover(id) {
        const elem = document.getElementById(id);
        const p = elem.nextElementSibling;
        if (Boolean(p) && p.nodeName === 'P') {
            p.classList.add("hidden");
        }
    }

    create_one_detail(qual_name, prefix, command, qdet, num_det) {
        let tmp = '';
        let detail = qdet.detail;
        let is_hidden = '';
        if (Boolean(qdet.depends)) {
            is_hidden = (Boolean(qdet.depends)) ? 'hidden' : '';
        }
        let dep_id = '';
        let description = qdet.description;
        let title = (Boolean(detail)) ? detail : '';
        let required = (Boolean(qdet.required) && qdet.required === "true");
        let list_value = qdet.list_value;
        if (Boolean(list_value)) {
            tmp = tmp + this.create_list(prefix, list_value, num_det, title, required, is_hidden);
            tmp = this.setDescription(tmp, description);
            dep_id = `${prefix}_ds${num_det}`;
        }
        let range_int = qdet.range_int;
        if (Boolean(range_int)) {
            tmp = tmp + this.create_number(prefix, range_int, num_det, title, false, required, is_hidden);
            tmp = this.setDescription(tmp, description);
            dep_id = `${prefix}_di${num_det}`;
        }
        let range_float = qdet.range_float;
        if (Boolean(range_float)) {
            tmp = tmp + this.create_number(prefix, range_float, num_det, title, true, required, is_hidden);
            tmp = this.setDescription(tmp, description);
            dep_id = `${prefix}_di${num_det}`;
        }
        let range_color = qdet.range_color;
        if (Boolean(range_color)) {
            let c_val = (Boolean(range_color.default)) ? ` value="${range_color.default}"` : '';
            c_val = (!Boolean(c_val) && Boolean(required)) ? '  value="000000"' : c_val;
            dep_id = `${prefix}_dc${num_det}`;
            let hover = (Boolean(description)) ? ` onmouseover="setHover('${dep_id}')"  onmouseout="offHover('${dep_id}')"` : '';
            if (Boolean(title)) {
                tmp = tmp + `<p class="item-trans ${is_hidden}" id="${prefix}p_dc${num_det}">${this.getTitle(title)}</p>`;
            }
            tmp = tmp + `<input type="color"${c_val} class="sel-inp ${is_hidden}" id="${dep_id}"${hover}>`
            tmp = this.setDescription(tmp, description);
        }
        let radio = qdet.radio;
        if (Boolean(radio)) {
            let direction = qdet.direction;
            direction = (Boolean(direction) && direction === 'vertical') ? 'block' : 'flex';
            tmp = tmp + this.create_radio(qual_name, prefix, command, radio, `${prefix}r_radio${num_det}`, num_det, direction, is_hidden);
            dep_id = `${prefix}r_radio${num_det}`;
        }
        if (Boolean(qdet.depends)) {
            this.setDepends(qual_name, command, dep_id, qdet.depends.qualifier, qdet.depends.command);
        }

        let subdetails = qdet.details;
        if (Boolean(subdetails)) {
            tmp = tmp + this.create_details(qual_name, prefix, command, subdetails, num_det);
        }
        return tmp;
    }

    create_radio(qual_name, prefix, command, radios, name, num_det, direction, is_hidden) {
        const cnt_radio = radios.length;
        is_hidden = (Boolean(is_hidden)) ? is_hidden : '';
        let ids = [];
        let com;
        for (let i = 0; i < cnt_radio; i++) {ids.push(`${prefix}r_${i}`)};
        let tmp = '';
        let tmp2 = '';
        for (let k = 0; k < cnt_radio; k++) {
            let rad = radios[k];
            let val = rad.value;
            let description = rad.description;
            com = rad.command;
            let det = (Boolean(rad.detail)) ? rad.detail : com;
            let title = (Boolean(det)) ? this.getTitle(det, false) : this.getTitle(val, false);
            let idn = ids.filter((x, index) => index !== k).map((x) => `'${x}d'`).join(',');
            let checked = (k == 0) ? ' checked' : '';
            let psh = (Boolean(com)) ? ` placeholder="${com}"` : '';
            let rtmp = `<input type="radio" name="${name}" value="${val}"${psh} id="${ids[k]}" ${checked} onchange="fnRadioChange2('${ids[k]}', '${ids[k]}d', [${idn}])">`;
            rtmp = rtmp + `<label for="${ids[k]}">${title}</label>`;
            if (Boolean(description)) {
                let hover = ` onmouseover="setHover('${prefix}_li${num_det+k}')"  onmouseout="offHover('${prefix}_li${num_det+k}')"`;
                rtmp = `<div id="${prefix}_li${num_det+k}"${hover}>${rtmp}</div><p class="dropdown-desc hidden">${description}</p>`;
            }
            tmp = tmp + `<li class="dropdown-item">${rtmp}</li>`;
            let hidden = (k > 0) ? ' hidden' : '';
            tmp2 = tmp2 + `<div class="group-inp${hidden}" id="${ids[k]}d">`;
            let comm = (Boolean(com)) ? com : command;
            tmp2 = tmp2 + this.create_one_detail(qual_name, prefix, comm, rad, num_det+k) + '</div>'
        }
        direction = (Boolean(direction)) ? ` style="display: ${direction}"` : '';
        let id_value = (Boolean(com)) ? ` id="${prefix}_value"` : '';
        if (Boolean(com)) {
            tmp2 = `<div class="item-trans" id="${prefix}_det"> ${tmp2} </div>`;   // detail-box команд
        }
        tmp = `<div  role="group" class="group-trans"><ul class="topic-options ${is_hidden}" ${direction}${id_value}>${tmp}</ul></div> ${tmp2}`;
        return tmp;
    }

    create_details(qual_name, prefix, command, details, num_det) {
        num_det = (num_det > 0) ? num_det * 10 : 0;
        let tmp = '';
        for (let i = 0; i < details.length; i++) {
            let qdet = details[i];
            num_det++;
            tmp = tmp + this.create_one_detail(qual_name, prefix, command, qdet, num_det)
        }
        return tmp;
    }

    create_commands(qual_name) {
        let qualifier = this.qualifiers[qual_name];
        let prefix = (Boolean(qualifier.prefix)) ? qualifier.prefix : qual_name[0];
        let comm_div = document.getElementById(`${prefix}_div`);
        let div_str = '';
        let is_radio = (Boolean(qualifier.type)) ? qualifier.type : 'list';
        if (is_radio === 'radio') {
            let direction = qualifier.direction;
            direction = (Boolean(direction) && direction === 'vertical') ? 'block' : 'flex';
            div_str = this.create_radio(qual_name, prefix, '', qualifier.commands, `${prefix}_radio`, 0, direction);
        } else {
            let description = qualifier.description;
            let hover = '';
            if (Boolean(description)) {
                hover = ` onmouseover="setHover('${prefix}_value')"  onmouseout="offHover('${prefix}_value')"`;
            }
            div_str = qualifier.commands.map((grav) => `<option value="${grav.command}">${grav.command}</option>`).join("");
            let ch_str = `onchange="fnCommandChange('${qual_name}', '${prefix}_value', '${prefix}_div', '${prefix}_det')"`;
            div_str = `<select class="sel-inp" id="${prefix}_value" ${ch_str}${hover}>${div_str}</select>`; 
            div_str = this.setDescription(div_str, description);
            div_str = `${div_str} <div class="item-trans hidden" id="${prefix}_det"></div>`;   // detail-box команд
        }
        if (Boolean(div_str)) {
            comm_div.innerHTML = div_str;       // Отобразить сформированный блок команды
        }
    }

    // "<qualifier>"     - id check-box qualifier
    // "<prefix>_div"    - id блока с элементом выбора команды и блоком деталей
    // "<prefix>_value"  - id элемента ввода команды ("select" для списка, "ul" для радиокнопок)
    // "<prefix>_det"    - id блока с деталями (содержимое может меняться для каждой команды)

    fnRadioChange2(id, id2, ids_hidden) {
        const h_rad = document.getElementById(id);          // Выбранный элемент
        const h_inp = document.getElementById(id2);         // Управляемый (отображаемый) элемент
        if (h_rad.checked) {
            if (h_inp.classList.contains('hidden')) {
                h_inp.classList.remove("hidden");
            }
        }
        for (let i = 0; i < ids_hidden.length; i++) {       // Список скрываемых элементов
            const idn = ids_hidden[i];
            const h_idn = document.getElementById(idn);     // Скрываемый элеент
            if (!h_idn.classList.contains('hidden')) {
                h_idn.classList.add("hidden");
            }
        }
    }

    fnCommandChange(qual_name, id_value, id_div, id_det) {
        let value = this.getElementValue(id_value);
        const e_div = document.getElementById(id_div);
        const e_det = document.getElementById(id_det);
        
        const qe_pref = this.qualifiers[qual_name].prefix;
        const qe_com = this.qualifiers[qual_name].commands.find(grav => grav.command === value);     // Словарь команды
        const qe_det = qe_com.details;                                                          // Детали команды

        e_det.innerHTML = '';
        if (!Boolean(qe_det)) {
            if (!e_det.classList.contains('hidden')) {
                e_det.classList.add('hidden');                  // У команды нет деталей, скрываем блок
            }
        } else {
            let num_det = 0;                                    // У команды есть детали
            let e_str = this.create_details(qual_name, qe_pref, value, qe_det, num_det);   // Создаем блок деталей
            e_det.innerHTML = e_str;
            if (e_det.classList.contains('hidden')) {
                e_det.classList.remove('hidden');               // Пооказываем блок 
            }
        }
        this.toggleDepends(qual_name);       // Синхронизируем зависимые элементы с управляющими элементами
    }

    fnCheckChange(id, id_div) {
        const h_inp = document.getElementById(id);
        const h_div = document.getElementById(id_div);
        let h_value = h_div.getElementsByTagName('select')[0];
        if (!Boolean(h_value)) {
            h_value = h_div.getElementsByTagName('ul')[0];
        }
        
        if (h_inp.checked) {
            h_div.classList.remove("hidden");
            if (Boolean(h_value) && Boolean(h_value.onchange)) {
                h_value.onchange();
            }
        } else {
            if (Boolean(h_value) && Boolean(h_value.onchange)) {
                h_value.onchange();
            }
            h_div.classList.add("hidden")
        }
    }

    checkedQualifier(id) {
        const elem = document.getElementById(id);
        let res = (Boolean(elem) && elem.checked) ? true : false;
        return res;
    }

    createBody() {
        //     gravity: str | None = "center"      # условный центр изображения
        //     height: str | None = "800"          # высота изображения
        //     width: str | None = "800"           # ширина изображения
        //     crop: str | None = "fill"           # Режим обрезки
        //     radius: str | None = "0"            # радиус закругления углов
        //     effect: str | None = None           # Эффекты и улучшения изображений
        //     quality: str | None = "auto"        # % потери качества при сжатии
        //     fetch_format: str | None = None     # Преобразование фото в определенный формат
        const body = {};
        for (let qual_name in this.qualifiers) {
            const qualifier = this.qualifiers[qual_name];
            const prefix = (Boolean(qualifier.prefix)) ? qualifier.prefix : qual_name[0];
            if (this.checkedQualifier(qual_name))
            {
                body[qual_name] = this.createParamBody(qual_name, `${prefix}_value`, `${prefix}_det`);
            }
        }

        // // ------------------------  height  ------------------------
        // if (this.checkedQualifier('height')) {
        //     body.height = this.createParamBody('height', 'h_value', 'h_det');
        // }
        // // ------------------------  width  ------------------------
        // if (this.checkedQualifier('width')) {
        //     body.width = this.createParamBody('width', 'w_value', 'w_det');
        // }
        // // ------------------------  crop  ------------------------
        // if (this.checkedQualifier('crop')) {
        //     body.crop = this.createParamBody('crop', 'c_value', 'c_det');
        // }
        // // ------------------------  gravity  ------------------------
        // if (this.checkedQualifier('gravity')) {
        //     body.gravity = this.createParamBody('gravity', 'g_value', 'g_det');
        // }
        // // ------------------------  radius  ------------------------
        // if (this.checkedQualifier('radius')) {
        //     body.radius = this.createParamBody('radius', 'r_value', 'r_det');
        // }
        // // ------------------------  fetch_format  ------------------------
        // if (this.checkedQualifier('fetch_format')) {
        //     body.fetch_format = this.createParamBody('fetch_format', 'f_value', 'f_det');
        // }
        // // ------------------------  quality  ------------------------
        // if (this.checkedQualifier('quality')) {
        //     body.quality = this.createParamBody('quality', 'q_value', 'q_det');
        // }
        // // ------------------------  effect  ------------------------
        // if (this.checkedQualifier('effect')) {
        //     body.effect = this.createParamBody('effect', 'e_value', 'e_det');
        // }

        console.log(body);
        // alert('create body')
        return body;
    } 

    getRadioCommand(nodes) {
        let res = {};
        if (Boolean(nodes.children)) {
            let radios = nodes.getElementsByTagName('input');    // выбираем все input-radio
            for (let i = 0; i < radios.length; i++) {
                let elem = radios[i];
                let e_type = (elem.hasAttribute('type')) ? elem.getAttribute('type'): '';
                let e_check = (elem.checked) ? true : false;
                if (e_type === 'radio' && e_check) {
                    return {"com": elem.placeholder, "val": elem.value};
                }
            }
        }
        return res;
    }

    createParamBody(qual_name, id_value, id_det) {
        const e_value = document.getElementById(id_value);
        const e_det = document.getElementById(id_det);
        let command = e_value.value;
        let value = e_value.value;
        const pattern = /\.*(\<.*\>)\.*/i;
        if (e_value.nodeName === 'UL') {
            let res = this.getRadioCommand(e_value);
            command = res.com;
            value = (Boolean(res.val) && pattern.test(res.val)) ? `${res.val}||` : res.val;
        }
        const qe_com = this.qualifiers[qual_name].commands.find(grav => grav.command === command);     // Словарь команды
        let params = this.getTemplate(qe_com);
        let elements = this.getChildrens(e_det, 0, (e_value.nodeName === 'UL'));
        elements = this.syncElements(params, elements);
        let i = 0;
        let j = 0;
        let scom = '';
        while (i < params.length && j < elements.length) {
            let stmp = '';
            let p1 = params[i];
            let fmt = p1.format;
            i++;
            let e1 = elements[j];
            j++;
            p1.link = e1.link;
            let val = e1.value;
            if (p1.element === 'radio') {
                if (Boolean(fmt) && Boolean(val)) {
                    stmp = fmt.replace(/\.*(\<.*\>)\.*/i, val);
                }
            } else if (!e1.hidden && Boolean(val)) {
                if (p1.element === 'float') {
                    val = `${val / 100}`;
                    if (val.indexOf('.') < 0) {
                        val = `${val}.0`;
                    }
                } else if (p1.element === 'color') {
                    val = val.replace('#', '');
                }
                stmp = fmt.replace(/\.*(\<.*\>)\.*/i, val);
            }
            scom = `${scom}${stmp}`;
        }
        scom = `${value}${scom}`;
        return scom;
    }

    syncElements(params, elements) {
        if (params.length > elements.length) {
            // Поиск в params "radio_value" и в elements "radio".
            let pr = -1;
            let prv = -1;
            for (let p = 0; p < params.length; p++) {
                if (params[p].element === 'radio') {
                    pr = p;
                } else if (params[p].element === 'radio_value') {
                    prv = p;
                    break;
                }
            }
            // Скопировать в elements элемент "radio" в позицию параметра "radio_value".
            if (pr >= 0 && prv >= 0) {
                let els = [];
                let e = 0;
                let p = 0;
                while (e < params.length) {
                    if (e === prv) {
                        els.push(elements[pr]);
                    } else {
                        els.push(elements[p]);
                        p++;
                    }
                    e++;
                }
                elements = els;
            }
        }
        return elements;
    }

    getTemplate(qTemplate, level, qParent) {
        let qres = [];
        qParent = (Boolean(qParent)) ? qParent : '';
        level = (Boolean(level)) ? level : 0;
        let detail = (Boolean(qTemplate.detail)) ? qTemplate.detail : qTemplate.value;
        if (Boolean(detail)) {          // Если есть формат детали
            let txt = '';
            let list_value = qTemplate.list_value;
            if (Boolean(list_value)) {
                txt = 'list';
            }
            let range_int = qTemplate.range_int;
            if (Boolean(range_int)) {
                txt = 'int';
            }
            let range_float = qTemplate.range_float;
            if (Boolean(range_float)) {
                txt = 'float';
            }
            let range_color = qTemplate.range_color;
            if (Boolean(range_color)) {
                txt = 'color';
            }
            let radio_value = qTemplate.radio_value;
            if (Boolean(radio_value)) {
                txt = 'radio_value';
            }
            if (Boolean(txt)) {
                qres.push({element: txt, format: detail, level: level, parent: qParent});
            }
        }

        let radio = qTemplate.radio;
        if (Boolean(radio)) {
            qres.push({element: 'radio', format: detail, level: level, parent: qParent});
            for (let i = 0; i < radio.length; i++) {
                let qdet = radio[i];
                let qtmp = this.getTemplate(qdet, level + 1, 'radio');
                for (let j = 0; j < qtmp.length; j++) {
                    qres.push(qtmp[j]);
                }
            }
        }

        let details = qTemplate.details;
        if (Boolean(details)) {
            let qpar = (level > 0) ? 'details' : qParent;
            for (let i = 0; i < details.length; i++) {
                let qdet = details[i];
                let qtmp = this.getTemplate(qdet, level + 1, qpar);
                for (let j = 0; j < qtmp.length; j++) {
                    qres.push(qtmp[j]);
                }
            }
        }
        return qres;
    }

    getChildrens(nodes, level, skip_hidden) {
        let res = [];
        if (Boolean(nodes.children)) {
            for (let i = 0; i < nodes.children.length; i++) {
                let elem = nodes.children[i];
                let e_hidden = (elem.hasAttribute('hidden')) ? true : false;
                e_hidden = (elem.classList.contains('hidden')) ? true : e_hidden;
                if (!(Boolean(skip_hidden) && e_hidden)) {
                    if (elem.localName === 'input' || elem.localName === 'select') {
                        let e_type = (elem.hasAttribute('type')) ? elem.getAttribute('type'): '';
                        let e_name = (elem.hasAttribute('name')) ? elem.getAttribute('name'): '';
                        let e_check = (elem.checked) ? true : false;
                        if (e_type !== 'radio' || e_check) {
                            res.push({element: elem.localName, value: elem.value, level: level, type: e_type, name: e_name, checked: e_check, hidden: e_hidden, link: elem});
                        }
                    } else if (elem.children.length > 0) {
                        let elements = this.getChildrens(elem, level + 1);
                        for (let j = 0; j < elements.length; j++) {
                            let el1 = elements[j];
                            if (e_hidden) {
                                el1.hidden = true;
                            }
                            res.push(el1);
                        }
                    }
                }
            }
        }
        return res;
    }

    setRadioCommand(nodes, value) {
        let res = false;
        if (Boolean(nodes.children)) {
            let radios = nodes.getElementsByTagName('input');    // выбираем все input-radio
            let el_ch;
            for (let a = 0; a < radios.length; a++) {
                let rad = radios[a];
                if (!Boolean(rad.value) && !Boolean(el_ch)) {
                    el_ch = rad;
                }
                if (rad.value === value) {
                    rad.checked = true;
                    rad.onchange();
                    res = true;
                } else {
                    rad.checked = false;
                }
            }
            if (!res && Boolean(el_ch)) {
                el_ch.checked = true;
                el_ch.onchange();
            }
        }
        return res;
    }

    // "<qualifier>"     - id check-box qualifier
    // "<prefix>_div"    - id блока с элементом выбора команды и блоком деталей
    // "<prefix>_value"  - id элемента ввода команды ("select" для списка, "ul" для радиокнопок)
    // "<prefix>_det"    - id блока с деталями (содержимое может меняться для каждой команды)


    setCommandValues(qual_name) {
        let tmp = this.trans_data[qual_name];                // команда без префикса

        const qualifier = this.qualifiers[qual_name];
        const prefix = (Boolean(qualifier.prefix)) ? qualifier.prefix : qual_name[0];

        const comm_ch = document.getElementById(qual_name);

        this.create_commands(qual_name, `${prefix}_div`);
        if (!Boolean(tmp)) {
            comm_ch.checked = false;
            this.fnCheckChange(qual_name, `${prefix}_div`);   // Выключаем чек-бокс
        } else {
            comm_ch.checked = true;
            this.fnCheckChange(qual_name, `${prefix}_div`);   // Включаем чек-бокс

            let elst = tmp.split(':');
            const comm_val = document.getElementById(`${prefix}_value`);
            let command = elst[0];
            let skip_hidden = false;

            if (comm_val.nodeName === 'UL') {
                let vals = elst[0].split('||');         // Разделяем комаду и ее значение
                this.setRadioCommand(comm_val, vals[0]);     // Переключаем радио-кнопки
                command = this.getTitle(vals[0], false);
                skip_hidden = true;
                if (vals.length > 1) {
                    for (let i = 1; i < elst.length; i++) {
                        vals.push(elst[i]);
                    }
                    elst = vals;
                }
            } else {
                comm_val.value = command;         // Записываем команду
                this.fnCommandChange(qual_name, `${prefix}_value`, `${prefix}_div`, `${prefix}_det`);
            }

            let qe_com = qualifier.commands.find(grav => grav.command === command);     // Словарь команды
            if (!Boolean(qe_com)) {
                qe_com = qualifier.commands.find(grav => grav.value === command);       // Словарь команды
            }
            let params = this.getTemplate(qe_com);                                           // считываем структуру параметров

            const comm_det = document.getElementById(`${prefix}_det`);
            let details = this.getChildrens(comm_det, 0, skip_hidden);                       // считываем структуру деталей
            details = this.syncElements(params, details);

            let i = 0;
            let j = 0;
            let k = 1;
            let radios;

            while (i < params.length && j < details.length && k < elst.length) {
                let p1 = params[i];                     // тек. параметр
                let fmt = p1.format;                    // его формат
                if (fmt[0] === ':' || fmt[0] === ',' || fmt[0] === ';') {
                    fmt = fmt.slice(1);
                }
                let d1 = details[j];                // тек. деталь
                let stmp = elst[k];                 // тек. значение

                if (stmp === 'rgb') {
                    let elst2 = [];
                    stmp = `${stmp}:#${elst[k+1]}`;    // если тек. значение "rgb", то добавляем цвет (след. значение)
                    for (let m = 0; m < elst.length; m++) {
                        if (m < k) {
                            elst2.push(elst[m]);
                        } else if (m === k) {
                            elst2.push(stmp);
                        } else if (m > k+1) {
                            elst2.push(elst[m]);
                        }
                    }
                    elst = elst2;
                } else if (p1.element !== 'list') { 
                    let csplit = ',';
                    let idx = stmp.indexOf(csplit);
                    if (idx < 0) {
                        csplit = ';';
                        idx = stmp.indexOf(csplit);
                    }
                    if (idx > 0) {
                        let elst2 = [];
                        let ltmp = stmp.split(csplit);
                        stmp = ltmp[0];
                        for (let b = 0; b < elst.length; b++) {
                            if (b === k) {
                                for (let c = 0; c < ltmp.length; c++) {
                                    elst2.push(ltmp[c]);
                                }
                            } else {
                                elst2.push(elst[b]);
                            }
                        }
                        elst = elst2;
                    }
                }

                let pattern = '';
                if (p1.element === 'list') {
                    pattern = '^' + fmt.replace(/\.*(\<.*\>)\.*/i, "(.*)") + '$';  //  ^(.*)$ - list
                } else if (p1.element === 'int') {
                    pattern = '^' + fmt.replace(/\.*(\<.*\>)\.*/i, "(\\d+)") + '$';    // ^(-?\d+)$ - int
                } else if (p1.element === 'float') {
                    pattern = '^' + fmt.replace(/\.*(\<.*\>)\.*/i, "(-?\\d+\\.?\\d*)") + '$';    // ^(-?\d+\.?\d*)$ - float
                } else if (p1.element === 'color') {
                    pattern = '^' + fmt.replace(/\.*(\<.*\>)\.*/i, "(#[0-9|a-f|A-F]+)") + '$';    // ^rgb:(#[0-9|a-f|A-F]+)$ - color
                } else if (p1.element === 'radio_value') {
                    pattern = '^' + fmt.replace(/\.*(\<.*\>)\.*/i, "(.*)") + '$';  //  ^(.*)$ - radio_value
                } else if (p1.element === 'radio') {
                    if (Boolean(fmt)) {
                        pattern = '^' + fmt.replace(/\.*(\<.*\>)\.*/i, "(.*)") + '$';  //  ^(.*)$ - radio
                    }
                    let elem = d1.link.parentNode;
                    while (elem.nodeName !== 'UL') {    // подымаемся вверх и ищем тэг <ul>
                        elem = elem.parentNode;
                    }
                    radios = elem;    // Тэг <ul> с input-radio
                }

                const pattern2 = new RegExp(pattern, 'i');
                if (Boolean(pattern) && pattern2.test(stmp)) {
                    const myArr = stmp.match(pattern2);
                    stmp = myArr[myArr.length-1];
                    if (p1.element === 'float') {
                        stmp = stmp * 100;
                    }

                    if (p1.element === 'radio' || p1.element === 'radio_value') {
                        if (this.setRadioCommand(radios, stmp)) {
                            k++;
                        };
                    } else {
                        d1.link.value = stmp;
                        k++;
                    }
                }
                i++;
                j++;
            }
        }
    }

    setupTransData() {
        const ul_qualifiers = document.getElementById(this.id_qualifiers);
        let li_str = '';
        for (let qual_name in this.qualifiers) {
            let qualifier = this.qualifiers[qual_name];
            let prefix = (Boolean(qualifier.prefix)) ? qualifier.prefix : qual_name[0];
            li_str = `${li_str}<li class="li-trans">`;
            li_str = `${li_str}<input type="checkbox" name="topic" value="${qual_name}" id="${qual_name}" onchange="fnCheckChange('${qual_name}', '${prefix}_div')">`;
            li_str = `${li_str}<label for="${qual_name}">${this.getTitle(qual_name)}</label>`;
            li_str = `${li_str}<div class="item-trans hidden" id="${prefix}_div"></div></li>`;
        }
        ul_qualifiers.innerHTML = li_str;

        for (let qual_name in this.qualifiers) {
            this.setCommandValues(qual_name);
        }
    }

    async photoTransfomReset(event, that) {
        event.preventDefault();
        let msg = 'Clear form elements';
        if (this.trans_data.length > 0) {
            msg = 'Restore form elements';
        }
        console.log(msg)
        that.setupTransData();
    }

    async photoTransfomSubmit(event, that) {
        event.preventDefault();

        let inp = document.getElementsByClassName('inp-error');
        for (let i = 0; i < inp.length; i++) {
            inp[i].textContent = "";
        }

        const form = event.currentTarget;
        const url =form.action;

        const photo_src = document.getElementById("photo-url");

        let responseData = undefined;
        let isRedirect = false;
        let urlRedirect = "";
        let isReload = false;
        let isUpdate = Boolean(photo_src.name);

        try {
            let body = that.createBody();
            const bodyJsonString = JSON.stringify(body);
            let meth = (isUpdate) ? "PUT" : "POST";

            const fetchOptions = {
                method: meth,
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                },
                body: bodyJsonString,
            };

            responseData = await fetch(url, fetchOptions);

            if (!responseData.ok) {
                const errorMessage = await responseData.text();
                throw new Error(errorMessage);
            }

            if (responseData.redirected) {
                isRedirect = true;
                urlRedirect = await check_redirect(responseData.url);
            }
            else {
                const responseJson = await responseData.json();
                const succs = responseJson.detail.success;
                const errs = responseJson.detail.errors;

                this.trans_data = body;

                if (Boolean(errs)) {
                    await errorsHandling(errs);
                }
                else if (Boolean(succs)) {
                    for (const suc of succs) {
                        if (suc.key == "redirect") {
                            isRedirect = true;
                            urlRedirect = suc.value;
                        } 
                        else if (suc.key == "message") {
                            alert(`Message: ${suc.value}`);
                        }
                        else if (suc.key == "reload") {
                            isReload = true;
                        }
                        else if (suc.key == "file_url" && isUpdate) {
                            photo_src.src = suc.value;
                        }
                        else if (suc.key == "qr_url" && isUpdate) {
                            const qr_img = document.getElementById("qr-url");
                            if (Boolean(suc.value)) {
                                qr_img.src = suc.value;
                                qr_img.style.display = "block";
                            } else {
                                qr_img.src = '';
                                qr_img.style.display = "none";
                            }
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

        if (isRedirect) {
            if (!Boolean(urlRedirect)) {
                alert("Redirect.value is not URL");
                urlRedirect = '/';
            }
            window.location.href = `${urlRedirect}`;
        }
        else if (isReload) {
            window.location.reload();
        }
    }

}

/** @param {number} time */
function sleep(time) {
    return new Promise((resolve) => setTimeout(resolve, time));
}

/** @param {string} string */
function escape_regex(string) {
    return string.replace(/[/\-\\^$*+?.()|[\]{}]/g, '\\$&');
}

function is_portrait() {
    return window.matchMedia("(orientation: portrait)").matches
        || window.screen.width <= window.screen.height;
}

/**
 * @param {string} text
 * @param {string} text_to_search
 * @param {string} type
 */
function search_in_text(text, text_to_search, type) {
    text = text.toLowerCase().trim();
    text_to_search = text_to_search.toLowerCase().trim();

    switch (type) {
        case 'all-words':
            return text_to_search.split(' ').every(word => text.includes(word));
        case 'any-word':
            return text_to_search.split(' ').some(word => text.includes(word));
        case 'exactly':
            return text.includes(text_to_search);
        default:
            return false;
    }
}

/** @param {number} length */
function generate_id(length) {
    let result = 'id_';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_';
    const charactersLength = characters.length;
    let counter = 0;
    while (counter < length) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
        counter += 1;
    }
    return result;
}

function reload() {
    document.getElementById('reload').click();
    reset_load_characters();
}

function load_materials() {
    document.getElementById('load_materials').click();
}

function load_upgrades() {
    document.getElementById('load_upgrades').click();
}

function load_characters(force = false) {
    let load_characters = document.getElementById('load_characters');
    if (force || load_characters.dataset.loaded === 'false') {
        load_characters.dataset.loaded = 'true';
        load_characters.click();
    }
}

function reset_load_characters() {
    load_characters.dataset.loaded = 'false';
}

function filter_characters() {
    let show_only_non_global_characters = document.getElementById('show_only_non_global_characters');
}

function add_selection_from_character_list(cid) {
    document.querySelector(`[data-character="${cid}"][data-type="character_list"]`).classList.add('character_in_upgrades')
}

function remove_selection_from_character_list(cid) {
    document.querySelector(`[data-character="${cid}"][data-type="character_list"]`).classList.remove('character_in_upgrades')
}

function add_toggle_upgrade_materials(ele) {
    const hidden = ele.classList.contains('icon-btn-red');
    const upgrade_materials = ele.closest('form').querySelector('.upgrade_materials');

    if (hidden) {
        ele.classList.remove('icon-btn-red');
        ele.classList.add('icon-btn-green');
        upgrade_materials.classList.remove('hidden');
    } else {
        ele.classList.remove('icon-btn-green');
        ele.classList.add('icon-btn-red');
        upgrade_materials.classList.add('hidden');
    }
}

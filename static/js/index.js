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

function load_upgrades() {
    document.getElementById('load_upgrades').click();
}

function load_materials() {
    document.getElementById('load_materials').click();
}

function load_import_export() {
    document.getElementById('load_import_export').click();
}

function load_settings() {
    document.getElementById('load_settings').click();
}

function load_about() {
    document.getElementById('load_about').click();
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
    const search_characters_input = document.getElementById('search_characters_input').value.trim();
    const show_cn_only_characters = document.getElementById('show_cn_only_characters').checked;
    const characters = document.getElementById('characters').querySelectorAll('li');

    for (let character of characters) {
        let character_name = character.querySelector('span').textContent.trim();
        let cn_only = character.dataset.cn_only.trim() === '1';

        if (show_cn_only_characters) {
            if (character.dataset.cn_only === '0') {
                character.classList.add('hidden');
                continue;
            }
        }

        if (search_characters_input.length > 0 && !search_in_text(character_name, search_characters_input, 'all-words')) {
            character.classList.add('hidden');
            continue;
        }

        character.classList.remove('hidden');
    }
}

/** @param {string} cid */
function add_selection_from_character_list(cid) {
    document.querySelector(`[data-character="${cid}"][data-type="character_list"]`).classList.add('character_in_upgrades')
}

/** @param {string} cid */
function remove_selection_from_character_list(cid) {
    document.querySelector(`[data-character="${cid}"][data-type="character_list"]`).classList.remove('character_in_upgrades')
}

/**
 * @param {string} id
 * @returns {InputCounter}
 */
function initFlowbiteInputCounter(id) {
    const $targetEl = document.getElementById(`${id}`);

    return new InputCounter(
        $targetEl,
        document.getElementById(`${id}-increment`),
        document.getElementById(`${id}-decrement`),
        {
            minValue: $targetEl.dataset.min,
            maxValue: $targetEl.dataset.max,
            onIncrement: () => {
                $targetEl.dispatchEvent(new Event('change'));
            },
            onDecrement: () => {
                $targetEl.dispatchEvent(new Event('change'));
            }
        },
        {
            id: `InputCounter-${id}`,
            override: true
        }
    );
}

/**
 * @param {string} id
 * @param {string} id_tooltip
 * @returns {Tooltip}
 */
function initFlowbiteTooltip(id, id_tooltip) {
    const $targetEl = document.getElementById(`${id}`);
    const $triggerEl = document.getElementById(`${id_tooltip}`);

    return new Tooltip(
        $targetEl,
        $triggerEl,
        {
            placement: 'top',
            triggerType: 'hover',
            onHide: () => {},
            onShow: () => {},
            onToggle: () => {},
        },
        {
          id: `Tooltip-${id}`,
          override: true
        }
    );
}

function change_theme() {
    const $theme = document.getElementById('theme').value;
    if ($theme === 'light') {
        document.querySelector('html').classList.remove('dark');
        document.querySelector('html').classList.add('light');
    } else {
        document.querySelector('html').classList.remove('light');
        document.querySelector('html').classList.add('dark');
    }
}

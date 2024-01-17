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


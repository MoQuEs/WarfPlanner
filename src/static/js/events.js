Event.prototype.canChange = function () {
    return this.target.nodeName === 'SELECT' || this.canInput();
};

Event.prototype.canInput = function () {
    return this.target.nodeName === 'INPUT';
};

Event.prototype.canClick = function () {
    return this.target.nodeName !== 'INPUT' && this.target.nodeName !== 'SELECT';
};

/** @param {string} class_name */
Event.prototype.classContains = function (class_name) {
    return this.target.classList.contains(class_name) ?
        true : this.target.nodeName === 'I' && this.target.parentNode.classList.contains(class_name);
};

/** @param {string} data_name */
Event.prototype.dataContains = function (data_name) {
    return this.target.dataset[data_name] !== undefined ?
        true : this.target.nodeName === 'I' && this.target.parentNode.dataset[data_name] !== undefined;
};

/** @param {string} data_name */
Event.prototype.dataGet = function (data_name) {
    if (this.target.dataset[data_name] !== undefined) {
        return this.target.dataset[data_name];
    }

    if (this.target.nodeName === 'I' && this.target.parentNode.dataset[data_name] !== undefined) {
        return this.target.parentNode.dataset[data_name];
    }

    return undefined;
};

document.body.addEventListener('click', function (event) {
    if (!event.canClick()) {
        return;
    }
}, false);

document.body.addEventListener('input', function (event) {
    if (!event.canInput()) {
        return;
    }
}, false);

document.body.addEventListener('change', function (event) {
    if (!event.canChange()) {
        return;
    }
}, false);

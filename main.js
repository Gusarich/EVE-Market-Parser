const formatNumber = (n, fixed = true) => {
    if (n >= 1e9) return (n / 1e9).toFixed(2) + 'b';
    if (n >= 1e6) return (n / 1e6).toFixed(2) + 'm';
    if (n >= 1e3) return (n / 1e3).toFixed(2) + 'k';
    if (fixed) return n.toFixed(2);
    return n.toString();
};

const insertNewCell = (row, text) => {
    var cell = row.insertCell();
    cell.appendChild(document.createTextNode(text));
};

const updateTable = () => {
    var tbody = document.createElement('tbody');

    for (let item of data['items']) {
        var row = tbody.insertRow();
        insertNewCell(row, item[1]);
        insertNewCell(row, formatNumber(item[2], false));
        insertNewCell(
            row,
            formatNumber((item[5] / item[6]) * 100 - 100) +
                '%\n' +
                formatNumber(item[6]) +
                ' => ' +
                formatNumber(item[5])
        );
        insertNewCell(row, formatNumber(item[4]));
        insertNewCell(row, formatNumber(item[3]));
        insertNewCell(row, formatNumber(item[7]));
        insertNewCell(row, formatNumber(item[8]));
    }

    var old_tbody = document
        .getElementById('main')
        .getElementsByTagName('tbody')[0];
    old_tbody.parentNode.replaceChild(tbody, old_tbody);
};

const sortTable = (key) => {
    if (lastSort == key) {
        window.data['items'].reverse();
    } else {
        if (key == 0) {
            window.data['items'].sort((a, b) => {
                if (a[5] / a[6] < b[5] / b[6]) return -1;
                if (a[5] / a[6] > b[5] / b[6]) return 1;
                return 0;
            });
        } else {
            window.data['items'].sort((a, b) => {
                if (a[key] < b[key]) return -1;
                if (a[key] > b[key]) return 1;
                return 0;
            });
        }
        window.lastSort = key;
    }

    updateTable();
};

window.onload = async () => {
    window.lastSort = -1;
    window.tableHeader = document
        .getElementById('main')
        .getElementsByTagName('tr')[0];
    window.data = await (await fetch('/data.json')).json();
    document.getElementById('lastUpdate').innerText = (
        (Date.now() - data['lastUpdate'] * 1000) /
        60000
    ).toFixed(1);
    updateTable();
};

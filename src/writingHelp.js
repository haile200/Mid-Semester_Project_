// The editor stores HTML; corrections work on plain text with one line per paragraph.

export function htmlToParagraphs(html) {
    const doc = new DOMParser().parseFromString(html || '', 'text/html');
    const paragraphs = [...doc.body.querySelectorAll('p')];
    const lines = paragraphs.length ? paragraphs.map((p) => p.textContent) : [doc.body.textContent];
    return lines.join('\n');
}

function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export function paragraphsToHtml(text) {
    return text
        .split('\n')
        .map((line) => `<p>${line ? escapeHtml(line) : '<br>'}</p>`)
        .join('');
}

export function hasFormatting(html) {
    return /<(strong|em|u|a)\b/i.test(html || '');
}

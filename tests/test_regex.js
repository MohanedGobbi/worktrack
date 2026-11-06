const timeTranslations = {
    'January': 'يناير', 'February': 'فبراير', 'March': 'مارس', 'April': 'أبريل', 'May': 'مايو', 'June': 'يونيو',
    'July': 'يوليو', 'August': 'أغسطس', 'September': 'سبتمبر', 'October': 'أكتوبر', 'November': 'نوفمبر', 'December': 'ديسمبر',
    'Jan': 'يناير', 'Feb': 'فبراير', 'Mar': 'مارس', 'Apr': 'أبريل', 'Jun': 'يونيو',
    'Jul': 'يوليو', 'Aug': 'أغسطس', 'Sep': 'سبتمبر', 'Oct': 'أكتوبر', 'Nov': 'نوفمبر', 'Dec': 'ديسمبر',
    'a.m.': 'ص', 'p.m.': 'م', 'AM': 'ص', 'PM': 'م', 'am': 'ص', 'pm': 'م',
    'Jan.': 'يناير', 'Feb.': 'فبراير', 'Mar.': 'مارس', 'Apr.': 'أبريل', 'Aug.': 'أغسطس', 'Sep.': 'سبتمبر', 'Oct.': 'أكتوبر', 'Nov.': 'نوفمبر', 'Dec.': 'ديسمبر'
};

function translateDateAndMixedText(text) {
    let translated = text;
    // Iterate over the keys. Note: we should replace longer strings first to avoid partial replacements!
    const keys = Object.keys(timeTranslations).sort((a, b) => b.length - a.length);
    for (const en of keys) {
        const ar = timeTranslations[en];
        // For a.m. / p.m. with dots, \b might not work perfectly if followed by a dot.
        // Let's use a simpler replace with word boundary, but handle the dots properly
        const escapedEn = en.replace(/\./g, '\\.');
        const regex = new RegExp(`\\b${escapedEn}(?=\\s|$|\\b)`, 'g');
        translated = translated.replace(regex, ar);
    }
    return translated;
}

console.log(translateDateAndMixedText("May 30, 2026"));
console.log(translateDateAndMixedText("Nov. 15, 2023"));
console.log(translateDateAndMixedText("14:30 p.m."));
console.log(translateDateAndMixedText("August 01, 2024"));

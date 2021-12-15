// you receive an array of objects which you must sort in the by the key "sortField" in the "sortDirection"
function getSortedItems(items, sortField, sortDirection) {
    console.log(items)
    console.log(sortField)
    console.log(sortDirection)

    let COLUMN_NAMES = ["Title", "Description", "VoteCount", "ViewNumber"]
    function byField(fieldName) {
         return (a, b) => {
             if (!isNaN(a[fieldName]) && !isNaN(b[fieldName])) {
                 return +a[fieldName] > +b[fieldName] ? 1 : -1;
             }
             return a[fieldName] > b[fieldName] ? 1 : -1;
         }
    }

    if (COLUMN_NAMES.includes(sortField)) {
        items.sort(byField(sortField));
        return sortDirection === "desc" ? items.reverse() : items;
    }
    else {
        console.log(`Something wrong with sortField or undefined: ${sortField}`)
        return items
    }

     // === SAMPLE CODE ===
    // if you have not changed the original html uncomment the code below to have an idea of the
    // effect this function has on the table
    //
    // if (sortDirection === "asc") {
    //     const firstItem = items.shift()
    //     if (firstItem) {
    //         items.push(firstItem)
    //     }
    // } else {
    //     const lastItem = items.pop()
    //     if (lastItem) {
    //         items.push(lastItem)
    //     }
    // }
    //
    // return items
}

// you receive an array of objects which you must filter by all it's keys to have a value matching "filterValue"
function getFilteredItems(items, filterValue) {
    console.log(items)
    console.log(filterValue)

    function filterItems(ifExclude) {
        let searchedPhrase = filterValue
        if (filterValue.match(/^!?Description:/i)) {
            console.log("Went into Description")
            searchedPhrase.replace(/^(!?Description:)/i, "");
            console.log(`searchedPhrase: ${searchedPhrase}`)
            return (ifExclude ? items.filter(item => !item["Description"].match(new RegExp(searchedPhrase, 'i')))
                              : items.filter(item => item["Description"].match(new RegExp(searchedPhrase, 'i'))));
        }
        searchedPhrase.replace(/^(!)/, '');
        console.log(`searchedPhrase: ${searchedPhrase} | ${searchedPhrase.replace(/^(!)/, "")}`);
        return (ifExclude ? items.filter(item => !item["Title"].match(new RegExp(searchedPhrase, 'i')))
                          : items.filter(item => item["Title"].match(new RegExp(searchedPhrase, 'i'))));
    }

    if (filterValue.startsWith("!")) {
        console.log(true)
        return filterItems(true);
    }
    else {
        console.log(false)
        return filterItems(false);
    }

    // === SAMPLE CODE ===
    // if you have not changed the original html uncomment the code below to have an idea of the
    // effect this function has on the table
    //
    // for (let i=0; i<filterValue.length; i++) {
    //     items.pop()
    // }
    //
    // return items
}

let clickCounter = 0
let bodyEl = document.getElementsByTagName('body')[0]
let defaultFontColor = getComputedStyle(bodyEl).getPropertyValue('color')
let defaultBackgroundColor = getComputedStyle(bodyEl).getPropertyValue('background-color')
function toggleTheme() {
    console.log("toggle theme")
    if (clickCounter % 2 === 0)
    {
        bodyEl.style.color = "white"
        bodyEl.style.backgroundColor = "#1e1d1d"
    }
    else {
        bodyEl.style.color = defaultFontColor
        bodyEl.style.backgroundColor = defaultBackgroundColor
    }
    clickCounter++
}

function increaseFont() {
    console.log("increaseFont")
    let bodyEl = document.getElementsByTagName('body')[0]
    bodyEl.style.fontSize = 1.25 + "em"
}

function decreaseFont() {
    console.log("decreaseFont")
    let bodyEl = document.getElementsByTagName('body')[0]
    // let prevFontSize = parseFloat(getComputedStyle(bodyEl).getPropertyValue('font-size'))
    // console.log((bodyEl.style.fontSize))
    // console.log(prevFontSize)
    // bodyEl.style.fontSize = prevFontSize * 0.75 + "px"
    bodyEl.style.fontSize = 0.75 + "em"
}

function restoreFont() {
    console.log("restoreFont")
    let bodyEl = document.getElementsByTagName('body')[0]
    bodyEl.style.fontSize = 1 + "em"
}
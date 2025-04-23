// menuitem code
function deleteMenuitem(menuitemId, partyId){
    fetch('/delete-menu-item', 
        {
            method:'DELETE',
            body: JSON.stringify({ menuitemId: menuitemId})
        }
        ).then((_res) => {
            window.location.href=`/partydetails?partyId=${partyId}`; //reloads the window
        })
}


// party code

function deleteParty(partyId) {
    fetch('/delete-party', //sends delete request to delete-party endpoint
    {
        method:'DELETE',
        body: JSON.stringify({ partyId: partyId})
    }
    ).then((_res) => {
        window.location.href="/"; //reloads the window
    })
}

function goToPartyDetails(partyId) {
    window.location.href=`/partydetails?partyId=${partyId}`
}

// cocktails code


function onAddCocktail(cocktailId){
 const number = document.getElementById(`addCocktailInput-${cocktailId}`).value
 cocktailId
 const partyId = document.getElementById('partySelect').value
 fetch('/add-cocktail-to-party', 
    {
        method:'POST',
        body: JSON.stringify({ cocktailId: cocktailId, amount: number, partyId: partyId})
    }
    ).then((_res) => {
        refreshPage()
    })
}


const cocktailByNameSearch = document.getElementById('cocktailByNamesearch')
const cocktailByIngredientSearch = document.getElementById('cocktailByIngredientSearch')
const alcoholSelect = document.getElementById('alcoholSelect')

alcoholSelect.addEventListener('change', () => {
    refreshPage()
});

cocktailByNameSearch.addEventListener('change', () => {
    refreshPage()
});

cocktailByIngredientSearch.addEventListener('change', () => {
    refreshPage()
});

function refreshPage(){
    href = window.location.pathname
    cocktailName = cocktailByNameSearch.value
    ingredient = cocktailByIngredientSearch.value
    if(cocktailName){
        href = `${href}?cocktailName=${encodeURIComponent(cocktailName)}`
        if(ingredient){
            href = `${href}&ingredient=${encodeURIComponent(ingredient)}`
        }
        if(alcoholSelect.value){
            href = `${href}&alcoholic=${encodeURIComponent(alcoholSelect.value)}`
        }
    }
    else if(ingredient){
        href = `${href}?ingredient=${encodeURIComponent(ingredient)}`

        if(alcoholSelect.value){
            href = `${href}&alcoholic=${encodeURIComponent(alcoholSelect.value)}`
        }
    }
    else if(alcoholSelect.value){
        href = `${href}?alcoholic=${encodeURIComponent(alcoholSelect.value)}`
    }
    window.location.href = href
}


function showCocktailPopup(cocktailId){
    popoverElement = document.getElementById(`popover-${cocktailId}`)
     // Get the current scroll position
    var scrollPosition = window.scrollY || document.documentElement.scrollTop;
    popoverElement.style.top = scrollPosition + "px"
    popoverElement.style.display='block'
}

function hideCocktailPopup(cocktailId){
    popoverElement = document.getElementById(`popover-${cocktailId}`)
    popoverElement.style.display='None'
}

// ingredients code

function showIngredientAmountPopup(ingredientName){
    console.log(ingredientName)
    console.log("asdfa")
    popoverElement = document.getElementById(`popover-${ingredientName}`)
    console.log(ingredientName)
    // Get the current scroll position
    var scrollPosition = window.scrollY || document.documentElement.scrollTop;
    popoverElement.style.top = scrollPosition + "px"
    popoverElement.style.display='block'
}

function hideIngredientAmountPopup(ingredientName){
    popoverElement = document.getElementById(`popover-${ingredientName}`)
    popoverElement.style.display='None'
}
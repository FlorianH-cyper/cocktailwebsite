/* ==========================================================================
   Cocktail App - Frontend Logic
   - Theme toggle (light/dark with persistence)
   - Page-scoped event listeners
   - Shared recipe modal
   ========================================================================== */

(function () {
    'use strict';

    // ---------- Theme Toggle ----------
    const root = document.documentElement;
    const themeToggle = document.getElementById('themeToggle');

    function setTheme(theme) {
        root.setAttribute('data-theme', theme);
        try { localStorage.setItem('theme', theme); } catch (e) { /* no-op */ }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
            setTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    // ---------- Recipe Modal ----------
    const modal = document.getElementById('recipeModal');
    const modalTitle = document.getElementById('recipeModalTitle');
    const modalImage = document.getElementById('recipeModalImage');
    const modalText = document.getElementById('recipeModalText');

    function openRecipeModal(data) {
        if (!modal) return;
        modalTitle.textContent = data.name || 'Recipe';
        modalImage.src = data.image || '';
        modalImage.alt = data.name || '';
        modalText.textContent = data.instructions || 'No instructions available.';
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closeRecipeModal() {
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal || e.target.closest('[data-modal-close]')) {
                closeRecipeModal();
            }
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && modal.classList.contains('is-open')) closeRecipeModal();
        });
    }

    // Recipe buttons (including rows added by live search)
    document.addEventListener('click', function (e) {
        const recipeBtn = e.target.closest('[data-recipe-trigger]');
        if (recipeBtn) {
            openRecipeModal({
                name: recipeBtn.getAttribute('data-recipe-name'),
                image: recipeBtn.getAttribute('data-recipe-image'),
                instructions: recipeBtn.getAttribute('data-recipe-instructions')
            });
            return;
        }

        const addBtn = e.target.closest('[data-add-cocktail]');
        if (addBtn) {
            const cocktailId = addBtn.getAttribute('data-add-cocktail');
            const input = document.getElementById('addCocktailInput-' + cocktailId);
            const partySelect = document.getElementById('partySelect');
            const amount = input ? input.value : '';
            const partyId = partySelect ? partySelect.value : '';
            if (!partyId) {
                alert('Please create a party first.');
                return;
            }
            if (!amount || Number(amount) <= 0) {
                if (input) input.focus();
                return;
            }
            fetch('/add-cocktail-to-party', {
                method: 'POST',
                body: JSON.stringify({
                    cocktailId: Number(cocktailId),
                    amount: Number(amount),
                    partyId: Number(partyId)
                })
            }).then(function () { window.location.reload(); });
        }
    });

    // ---------- Party actions ----------
    document.querySelectorAll('[data-delete-party]').forEach(function (el) {
        el.addEventListener('click', function () {
            const partyId = el.getAttribute('data-delete-party');
            if (!confirm('Delete this party?')) return;
            fetch('/delete-party', {
                method: 'DELETE',
                body: JSON.stringify({ partyId: Number(partyId) })
            }).then(function () { window.location.href = '/'; });
        });
    });

    document.querySelectorAll('[data-go-party]').forEach(function (el) {
        el.addEventListener('click', function () {
            const partyId = el.getAttribute('data-go-party');
            window.location.href = '/partydetails?partyId=' + encodeURIComponent(partyId);
        });
    });

    // ---------- Menu item actions ----------
    document.querySelectorAll('[data-delete-menuitem]').forEach(function (el) {
        el.addEventListener('click', function () {
            const menuitemId = el.getAttribute('data-delete-menuitem');
            const partyId = el.getAttribute('data-party-id');
            fetch('/delete-menu-item', {
                method: 'DELETE',
                body: JSON.stringify({ menuitemId: Number(menuitemId) })
            }).then(function () {
                window.location.href = '/partydetails?partyId=' + encodeURIComponent(partyId);
            });
        });
    });

    document.querySelectorAll('[data-toggle-recipe]').forEach(function (el) {
        el.addEventListener('click', function () {
            const targetId = el.getAttribute('data-toggle-recipe');
            const target = document.getElementById(targetId);
            if (target) target.classList.toggle('is-open');
        });
    });

    // ---------- Cocktail Search (AJAX, no full page reload) ----------
    const nameInput = document.getElementById('cocktailByNamesearch');
    const ingredientInput = document.getElementById('cocktailByIngredientSearch');
    const alcoholSelect = document.getElementById('alcoholSelect');
    const resultsWrap = document.getElementById('cocktailSearchResults');
    const resultsMeta = document.getElementById('cocktailResultsMeta');
    const resultsBody = document.getElementById('cocktailResultsBody');
    const resultsEmpty = document.getElementById('cocktailResultsEmpty');

    function buildSearchParams() {
        const params = new URLSearchParams();
        if (nameInput && nameInput.value) params.set('cocktailName', nameInput.value);
        if (ingredientInput && ingredientInput.value) params.set('ingredient', ingredientInput.value);
        if (alcoholSelect && alcoholSelect.value && alcoholSelect.value !== 'both') {
            params.set('alcoholic', alcoholSelect.value);
        }
        return params;
    }

    function updateResultsMeta(count, truncated) {
        if (!resultsMeta) return;
        if (truncated) {
            resultsMeta.innerHTML = '<span>First ' + count + ' results — narrow your search for more matches</span>';
        } else {
            const label = count === 1 ? 'result' : 'results';
            resultsMeta.innerHTML = '<span>' + count + ' ' + label + '</span>';
        }
    }

    function createCocktailRow(cocktail) {
        const tr = document.createElement('tr');

        const thumbCell = document.createElement('td');
        thumbCell.className = 'cell--shrink';
        const img = document.createElement('img');
        img.className = 'cocktail-thumb';
        img.src = cocktail.thumb;
        img.alt = cocktail.name;
        img.loading = 'lazy';
        img.decoding = 'async';
        thumbCell.appendChild(img);

        const nameCell = document.createElement('td');
        const nameEl = document.createElement('div');
        nameEl.className = 'cocktail-name';
        nameEl.textContent = cocktail.name;
        const countEl = document.createElement('div');
        countEl.className = 'muted';
        countEl.style.fontSize = 'var(--fs-xs)';
        countEl.textContent = cocktail.number_of_ingredients + ' ingredients';
        nameCell.appendChild(nameEl);
        nameCell.appendChild(countEl);

        const ingredientsCell = document.createElement('td');
        const ingredientsEl = document.createElement('div');
        ingredientsEl.className = 'cocktail-ingredients';
        ingredientsEl.textContent = cocktail.all_ingredients;
        ingredientsCell.appendChild(ingredientsEl);

        const actionsCell = document.createElement('td');
        actionsCell.className = 'cell--right';
        const addCell = document.createElement('div');
        addCell.className = 'add-cell';

        const amountInput = document.createElement('input');
        amountInput.className = 'input';
        amountInput.id = 'addCocktailInput-' + cocktail.id;
        amountInput.type = 'number';
        amountInput.min = '1';
        amountInput.placeholder = '# drinks';

        const recipeBtn = document.createElement('button');
        recipeBtn.type = 'button';
        recipeBtn.className = 'btn btn--secondary btn--sm';
        recipeBtn.setAttribute('data-recipe-trigger', '');
        recipeBtn.setAttribute('data-recipe-name', cocktail.name);
        recipeBtn.setAttribute('data-recipe-image', cocktail.image);
        recipeBtn.setAttribute('data-recipe-instructions', cocktail.instructions);
        recipeBtn.textContent = 'Recipe';

        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.className = 'btn btn--sm';
        addBtn.setAttribute('data-add-cocktail', String(cocktail.id));
        addBtn.textContent = '+ Add';

        addCell.appendChild(amountInput);
        addCell.appendChild(recipeBtn);
        addCell.appendChild(addBtn);
        actionsCell.appendChild(addCell);

        tr.appendChild(thumbCell);
        tr.appendChild(nameCell);
        tr.appendChild(ingredientsCell);
        tr.appendChild(actionsCell);
        return tr;
    }

    function renderSearchResults(data) {
        if (!resultsBody || !resultsWrap || !resultsEmpty) return;

        resultsBody.replaceChildren();
        const cocktails = data.cocktails || [];

        if (cocktails.length === 0) {
            resultsWrap.hidden = true;
            resultsEmpty.hidden = false;
            return;
        }

        resultsWrap.hidden = false;
        resultsEmpty.hidden = true;
        updateResultsMeta(cocktails.length, data.truncated);

        const fragment = document.createDocumentFragment();
        cocktails.forEach(function (cocktail) {
            fragment.appendChild(createCocktailRow(cocktail));
        });
        resultsBody.appendChild(fragment);
    }

    let searchRequestId = 0;

    function refreshSearch() {
        const params = buildSearchParams();
        const qs = params.toString();
        const url = window.location.pathname + (qs ? '?' + qs : '');
        window.history.replaceState(null, '', url);

        if (!resultsBody) {
            window.location.href = url;
            return;
        }

        const requestId = ++searchRequestId;
        fetch('/api/cocktails' + (qs ? '?' + qs : ''))
            .then(function (response) { return response.json(); })
            .then(function (data) {
                if (requestId !== searchRequestId) return;
                renderSearchResults(data);
            })
            .catch(function () {
                window.location.href = url;
            });
    }

    function bindSearchInput(el) {
        if (!el) return;
        let timer;
        el.addEventListener('change', refreshSearch);
        el.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                refreshSearch();
            }
        });
        el.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(refreshSearch, 300);
        });
    }

    bindSearchInput(nameInput);
    bindSearchInput(ingredientInput);
    if (alcoholSelect) alcoholSelect.addEventListener('change', refreshSearch);
})();

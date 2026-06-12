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
    const modalRatingSummary = document.getElementById('recipeModalRatingSummary');
    const modalStarRating = document.getElementById('recipeModalStarRating');

    function formatRatingSummary(avg, count) {
        if (!count) return 'No ratings yet';
        var label = count === 1 ? 'rating' : 'ratings';
        return '★ ' + avg + ' · ' + count + ' ' + label;
    }

    function setStarRatingState(container, userStars) {
        if (!container) return;
        var stars = container.querySelectorAll('.star-rating__star');
        var activeStars = userStars ? Number(userStars) : 0;
        container.setAttribute('data-user-stars', userStars || '');
        stars.forEach(function (star) {
            var value = Number(star.getAttribute('data-star'));
            star.classList.toggle('is-active', value <= activeStars);
        });
    }

    function updateRatingSummaryElement(element, summary) {
        if (!element || !summary) return;
        element.textContent = formatRatingSummary(summary.avg, summary.count);
    }

    function updateRatingDisplays(cocktailId, summary) {
        document.querySelectorAll('[data-rating-summary="' + cocktailId + '"]').forEach(function (el) {
            updateRatingSummaryElement(el, summary);
        });
        document.querySelectorAll('[data-rating-input="' + cocktailId + '"]').forEach(function (el) {
            setStarRatingState(el, summary.user_stars);
        });
        document.querySelectorAll('[data-recipe-trigger][data-recipe-id="' + cocktailId + '"]').forEach(function (el) {
            el.setAttribute('data-recipe-avg', summary.avg != null ? String(summary.avg) : '');
            el.setAttribute('data-recipe-count', String(summary.count || 0));
            el.setAttribute('data-recipe-user-stars', summary.user_stars != null ? String(summary.user_stars) : '');
        });
    }

    function submitRating(cocktailId, stars) {
        return fetch('/api/cocktails/' + cocktailId + '/rate', {
            method: 'POST',
            body: JSON.stringify({ stars: stars })
        }).then(function (response) {
            if (!response.ok) throw new Error('Rating failed');
            return response.json();
        }).then(function (summary) {
            updateRatingDisplays(cocktailId, summary);
            if (modalStarRating && modalStarRating.getAttribute('data-rating-input') === String(cocktailId)) {
                updateRatingSummaryElement(modalRatingSummary, summary);
            }
        });
    }

    function openRecipeModal(data) {
        if (!modal) return;
        modalTitle.textContent = data.name || 'Recipe';
        modalImage.src = data.image || '';
        modalImage.alt = data.name || '';
        modalText.textContent = data.instructions || 'No instructions available.';
        if (modalStarRating) {
            modalStarRating.setAttribute('data-rating-input', data.id ? String(data.id) : '');
        }
        updateRatingSummaryElement(modalRatingSummary, {
            avg: data.avg,
            count: data.count || 0
        });
        setStarRatingState(modalStarRating, data.userStars);
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
        const starBtn = e.target.closest('.star-rating__star');
        if (starBtn) {
            const ratingInput = starBtn.closest('[data-rating-input]');
            const cocktailId = ratingInput ? ratingInput.getAttribute('data-rating-input') : '';
            const stars = Number(starBtn.getAttribute('data-star'));
            if (cocktailId && stars) {
                submitRating(cocktailId, stars);
            }
            return;
        }

        const recipeBtn = e.target.closest('[data-recipe-trigger]');
        if (recipeBtn) {
            openRecipeModal({
                id: recipeBtn.getAttribute('data-recipe-id'),
                name: recipeBtn.getAttribute('data-recipe-name'),
                image: recipeBtn.getAttribute('data-recipe-image'),
                instructions: recipeBtn.getAttribute('data-recipe-instructions'),
                avg: recipeBtn.getAttribute('data-recipe-avg') || null,
                count: Number(recipeBtn.getAttribute('data-recipe-count') || 0),
                userStars: recipeBtn.getAttribute('data-recipe-user-stars') || null
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

        const ratingSummary = document.createElement('div');
        ratingSummary.className = 'cocktail-rating-summary muted';
        ratingSummary.setAttribute('data-rating-summary', String(cocktail.id));
        ratingSummary.style.fontSize = 'var(--fs-xs)';
        ratingSummary.textContent = formatRatingSummary(cocktail.avg_rating, cocktail.rating_count || 0);
        nameCell.appendChild(ratingSummary);

        const ratingInput = document.createElement('div');
        ratingInput.className = 'star-rating star-rating--compact';
        ratingInput.setAttribute('data-rating-input', String(cocktail.id));
        ratingInput.setAttribute('aria-label', 'Rate ' + cocktail.name);
        for (var star = 1; star <= 5; star++) {
            const starBtn = document.createElement('button');
            starBtn.type = 'button';
            starBtn.className = 'star-rating__star';
            starBtn.setAttribute('data-star', String(star));
            starBtn.setAttribute('aria-label', star + (star === 1 ? ' star' : ' stars'));
            starBtn.textContent = '★';
            ratingInput.appendChild(starBtn);
        }
        setStarRatingState(ratingInput, cocktail.user_stars);
        nameCell.appendChild(ratingInput);

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
        recipeBtn.setAttribute('data-recipe-id', String(cocktail.id));
        recipeBtn.setAttribute('data-recipe-name', cocktail.name);
        recipeBtn.setAttribute('data-recipe-image', cocktail.image);
        recipeBtn.setAttribute('data-recipe-instructions', cocktail.instructions);
        recipeBtn.setAttribute('data-recipe-avg', cocktail.avg_rating != null ? String(cocktail.avg_rating) : '');
        recipeBtn.setAttribute('data-recipe-count', String(cocktail.rating_count || 0));
        recipeBtn.setAttribute('data-recipe-user-stars', cocktail.user_stars != null ? String(cocktail.user_stars) : '');
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

    document.querySelectorAll('[data-rating-input]').forEach(function (el) {
        setStarRatingState(el, el.getAttribute('data-user-stars'));
    });
})();

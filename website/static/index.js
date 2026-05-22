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

    // Recipe buttons (any element with data-recipe attributes)
    document.querySelectorAll('[data-recipe-trigger]').forEach(function (el) {
        el.addEventListener('click', function () {
            openRecipeModal({
                name: el.getAttribute('data-recipe-name'),
                image: el.getAttribute('data-recipe-image'),
                instructions: el.getAttribute('data-recipe-instructions')
            });
        });
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

    // ---------- Cocktail Search ----------
    const nameInput = document.getElementById('cocktailByNamesearch');
    const ingredientInput = document.getElementById('cocktailByIngredientSearch');
    const alcoholSelect = document.getElementById('alcoholSelect');

    function refreshSearch() {
        const params = new URLSearchParams();
        if (nameInput && nameInput.value) params.set('cocktailName', nameInput.value);
        if (ingredientInput && ingredientInput.value) params.set('ingredient', ingredientInput.value);
        if (alcoholSelect && alcoholSelect.value && alcoholSelect.value !== 'both') {
            params.set('alcoholic', alcoholSelect.value);
        }
        const qs = params.toString();
        window.location.href = window.location.pathname + (qs ? '?' + qs : '');
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
            timer = setTimeout(refreshSearch, 600);
        });
    }

    bindSearchInput(nameInput);
    bindSearchInput(ingredientInput);
    if (alcoholSelect) alcoholSelect.addEventListener('change', refreshSearch);

    // Add cocktail to party
    document.querySelectorAll('[data-add-cocktail]').forEach(function (el) {
        el.addEventListener('click', function () {
            const cocktailId = el.getAttribute('data-add-cocktail');
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
        });
    });
})();

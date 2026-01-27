/**
 * Catalog Page Logic
 * Handles fetching books, filtering, sorting, pagination, and UI interactions.
 */

document.addEventListener('DOMContentLoaded', function () {
    // --- DOM Elements ---
    const bookContainer = document.getElementById('bookContainer');
    const pagination = document.getElementById('pagination');
    const resultsCount = document.getElementById('resultsCount');
    const loader = document.getElementById('loader');
    const emptyState = document.getElementById('emptyState');
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const categorySelect = document.getElementById('categorySelect');
    const authorInput = document.getElementById('authorInput');
    const stockCheck = document.getElementById('stockCheck');
    const sortSelect = document.getElementById('sortSelect');
    const applyBtn = document.getElementById('applyFiltersBtn');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    const emptyClearBtn = document.getElementById('emptyClearBtn');
    const gridViewBtn = document.getElementById('gridViewBtn');
    const listViewBtn = document.getElementById('listViewBtn');
    const activeFiltersContainer = document.getElementById('activeFilters');
    const totalBooksHeader = document.getElementById('totalBooksHeader');
    const sidebarFeatured = document.getElementById('sidebarFeatured');

    // --- State ---
    let currentState = {
        q: '',
        category: 'All',
        price_max: 2000,
        author: '',
        in_stock: false,
        sort: 'rating',
        page: 1,
        view: localStorage.getItem('catalogView') || 'grid'
    };

    // --- Initialize Price Slider ---
    const priceSlider = document.getElementById('priceSlider');
    const priceMinDisplay = document.getElementById('priceMinDisplay');
    const priceMaxDisplay = document.getElementById('priceMaxDisplay');

    if (priceSlider && typeof noUiSlider !== 'undefined') {
        noUiSlider.create(priceSlider, {
            start: [0, 2000],
            connect: true,
            range: {
                'min': 0,
                'max': 3000
            },
            step: 50,
            tooltips: [false, false]
        });

        // Update display on slide
        priceSlider.noUiSlider.on('update', function (values, handle) {
            const min = Math.round(values[0]);
            const max = Math.round(values[1]);
            priceMinDisplay.textContent = `₹${min}`;
            priceMaxDisplay.textContent = max >= 3000 ? '₹3000+' : `₹${max}`;
        });

        // Update state on change (end of slide)
        priceSlider.noUiSlider.on('change', function (values) {
            currentState.price_max = Math.round(values[1]);
            // User complained price filter not working.
            // Let's trigger fetch on slide end to be proactive, or respect "Apply".
            // If Apply button exists, maybe stick to it. But "Price Range" filter usually implies active change in many UXs.
            // Let's stick to update state, but verify Apply works.
        });
    }

    // --- Initialization ---
    init();

    function init() {
        // Load initial params from URL
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.has('q')) currentState.q = urlParams.get('q');
        if (urlParams.has('category')) currentState.category = urlParams.get('category');
        if (urlParams.has('author')) currentState.author = urlParams.get('author');
        if (urlParams.has('sort')) currentState.sort = urlParams.get('sort');

        // Sync UI with State
        searchInput.value = currentState.q;
        categorySelect.value = currentState.category;
        authorInput.value = currentState.author;
        sortSelect.value = currentState.sort;

        updateViewToggle(currentState.view);

        // Fetch Data
        fetchCategories();
        fetchBooks();
        fetchFeatured();
    }

    // --- Data Fetching ---

    async function fetchCategories() {
        // Get categories from the select element that was populated by Flask template
        // If no options exist, add some defaults
        if (categorySelect.options.length <= 1) {
            const defaultCategories = [
                'Fiction', 'Non-Fiction', 'Science Fiction', 'Fantasy',
                'Romance', 'Mystery', 'Thriller', 'Biography',
                'History', 'Children\'s', 'Academic', 'Science'
            ];

            defaultCategories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat;
                option.textContent = cat;
                categorySelect.appendChild(option);
            });
        }

        // Set current selection
        categorySelect.value = currentState.category;
    }

    async function fetchBooks() {
        showLoader();
        updateURL();
        renderActiveFilters();

        const params = new URLSearchParams({
            q: currentState.q,
            category: currentState.category === 'All' ? '' : currentState.category,
            price_max: currentState.price_max,
            author: currentState.author,
            in_stock: currentState.in_stock,
            sort: currentState.sort,
            page: currentState.page
        });

        try {
            const response = await fetch(`/api/books?${params}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();

            // Update UI
            if (totalBooksHeader) {
                totalBooksHeader.textContent = data.total;
            }

            const startNum = (data.page - 1) * data.per_page + 1;
            const endNum = Math.min(data.page * data.per_page, data.total);
            resultsCount.textContent = `Showing ${startNum}-${endNum} of ${data.total} books`;

            renderBooks(data.books);
            renderPagination(data.page, data.pages);

        } catch (error) {
            console.error('Error:', error);
            bookContainer.innerHTML = '<div class="col-12 text-center text-danger py-5">Failed to load books. Please try again later.</div>';
        } finally {
            hideLoader();
        }
    }

    async function fetchFeatured() {
        try {
            const response = await fetch(`/api/books?sort=rating&page=1`);
            const data = await response.json();
            const top3 = data.books.slice(0, 3);

            if (sidebarFeatured) {
                sidebarFeatured.innerHTML = top3.map(book => `
                    <div class="d-flex align-items-center gap-3 mb-3">
                        <img src="${book.image}" 
                             alt="${book.title}" 
                             class="rounded shadow-sm" 
                             style="width: 45px; height: 60px; object-fit: cover;"
                             onerror="this.src='/static/images/book-placeholder.jpg'">
                        <div style="flex: 1; min-width: 0;">
                            <a href="/book/${book.isbn}" 
                               class="text-decoration-none text-dark fw-bold small d-block text-truncate" 
                               title="${book.title}">
                                ${book.title}
                            </a>
                            <div class="text-warning" style="font-size: 0.7rem;">
                                ${renderStars(book.rating)}
                            </div>
                            <span class="text-primary fw-bold small">₹${book.price}</span>
                        </div>
                    </div>
                `).join('');
            }
        } catch (e) {
            console.error('Failed to load featured books:', e);
            if (sidebarFeatured) {
                sidebarFeatured.innerHTML = '<small class="text-muted">Could not load featured books.</small>';
            }
        }
    }

    // --- Rendering ---

    function renderBooks(books) {
        if (!books || books.length === 0) {
            bookContainer.innerHTML = '';
            emptyState.classList.remove('d-none');
            return;
        }

        emptyState.classList.add('d-none');

        const viewClass = currentState.view === 'list' ? 'col-12' : 'col-12 col-sm-6 col-md-4 col-lg-3';
        const cardClass = currentState.view === 'list' ? 'list-view' : '';

        bookContainer.innerHTML = books.map(book => {
            const isOutOfStock = book.stock <= 0;
            const stockClass = isOutOfStock ? 'text-danger' : (book.stock < 10 ? 'text-warning' : 'text-success');
            const stockText = isOutOfStock ? 'Out of Stock' : (book.stock < 10 ? `Only ${book.stock} left` : 'In Stock');
            const btnState = isOutOfStock ? 'disabled' : '';

            return `
            <div class="${viewClass} mb-4">
                <div class="card book-card h-100 ${cardClass}">
                    <span class="category-badge">${book.category}</span>
                    <div class="book-image-container">
                        <img src="${book.image}" 
                             class="card-img-top" 
                             alt="${book.title}" 
                             loading="lazy" 
                             onerror="this.src='/static/images/book-placeholder.jpg'">
                        <div class="quick-view-overlay">
                             <a href="/book/${book.isbn}" class="btn btn-light btn-sm rounded-pill shadow-sm fw-bold">
                                Quick View
                             </a>
                        </div>
                    </div>
                    <div class="card-body d-flex flex-column">
                        <div class="mb-2">
                            <span class="text-warning small">${renderStars(book.rating)}</span>
                            <span class="text-muted small ms-1">(${book.ratings_count || 0})</span>
                        </div>
                        <h6 class="card-title fw-bold mb-1" style="min-height: 40px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${book.title}">
                            <a href="/book/${book.isbn}" class="text-decoration-none text-dark">${book.title}</a>
                        </h6>
                        <p class="small text-muted mb-2">by ${book.author}</p>
                        
                        <div class="mt-auto pt-2 border-top">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="h5 mb-0 fw-bold text-primary">₹${parseFloat(book.price).toFixed(2)}</span>
                                <span class="small fw-bold ${stockClass}">${stockText}</span>
                            </div>
                            <button class="btn btn-primary w-100 btn-sm add-to-cart-btn" 
                                    data-isbn="${book.isbn}" 
                                    ${btnState} 
                                    onclick="addToCart(this)">
                                <i class="fas fa-cart-plus me-1"></i> Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            `;
        }).join('');
    }

    function renderStars(rating) {
        if (!rating) return '<span class="text-muted">No rating</span>';

        let output = '';
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;

        for (let i = 1; i <= 5; i++) {
            if (i <= fullStars) {
                output += '<i class="fas fa-star"></i>';
            } else if (i === fullStars + 1 && hasHalfStar) {
                output += '<i class="fas fa-star-half-alt"></i>';
            } else {
                output += '<i class="far fa-star"></i>';
            }
        }

        return output;
    }

    function renderActiveFilters() {
        const filters = [];
        if (currentState.q) filters.push({ label: `Search: ${currentState.q}`, key: 'q' });
        if (currentState.category !== 'All') filters.push({ label: currentState.category, key: 'category' });
        if (currentState.author) filters.push({ label: `Author: ${currentState.author}`, key: 'author' });
        if (currentState.in_stock) filters.push({ label: 'In Stock', key: 'in_stock' });
        if (currentState.price_max < 2000) filters.push({ label: `Max ₹${currentState.price_max}`, key: 'price_max' });

        activeFiltersContainer.innerHTML = filters.map(f => `
            <span class="badge bg-light text-dark border d-inline-flex align-items-center gap-2 me-2 mb-2">
                ${f.label}
                <button type="button" class="btn-close" style="width: 0.5em; height: 0.5em;" aria-label="Remove" onclick="removeFilter('${f.key}')"></button>
            </span>
        `).join('');
    }

    function renderPagination(page, pages) {
        pagination.innerHTML = '';
        if (pages <= 1) return;

        // Previous
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>`;
        if (page > 1) {
            prevLi.onclick = (e) => { e.preventDefault(); changePage(page - 1); };
        }
        pagination.appendChild(prevLi);

        // Page Numbers (Show max 7)
        let startPage = Math.max(1, page - 3);
        let endPage = Math.min(pages, startPage + 6);
        if (endPage - startPage < 6) startPage = Math.max(1, endPage - 6);

        for (let i = startPage; i <= endPage; i++) {
            const li = document.createElement('li');
            li.className = `page-item ${i === page ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            li.onclick = (e) => { e.preventDefault(); changePage(i); };
            pagination.appendChild(li);
        }

        // Next
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${page === pages ? 'disabled' : ''}`;
        nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>`;
        if (page < pages) {
            nextLi.onclick = (e) => { e.preventDefault(); changePage(page + 1); };
        }
        pagination.appendChild(nextLi);
    }

    // --- Actions ---

    window.changePage = function (newPage) {
        currentState.page = newPage;
        fetchBooks();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    window.removeFilter = function (key) {
        if (key === 'q') {
            currentState.q = '';
            searchInput.value = '';
            clearSearchBtn.classList.add('d-none');
        }
        if (key === 'category') {
            currentState.category = 'All';
            categorySelect.value = 'All';
        }
        if (key === 'author') {
            currentState.author = '';
            authorInput.value = '';
        }
        if (key === 'in_stock') {
            currentState.in_stock = false;
            stockCheck.checked = false;
        }
        if (key === 'price_max') {
            currentState.price_max = 2000;
            if (priceSlider && priceSlider.noUiSlider) {
                priceSlider.noUiSlider.set([0, 2000]);
            }
        }

        currentState.page = 1;
        fetchBooks();
    };

    // Add to Cart Logic
    window.addToCart = async function (btn) {
        const isbn13 = btn.dataset.isbn;
        const originalHtml = btn.innerHTML;

        // Loading State
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...';

        try {
            const res = await fetch('/api/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ isbn13: isbn13, quantity: 1 })
            });

            // Handle unauthorized access (redirect to login)
            if (res.status === 401) {
                const data = await res.json();
                if (data.redirect) {
                    window.location.href = data.redirect;
                    return;
                }
            }

            const data = await res.json();

            if (data.success) {
                btn.classList.replace('btn-primary', 'btn-success');
                btn.innerHTML = '<i class="fas fa-check"></i> Added!';

                // Update cart badge in navbar
                const cartBadge = document.querySelector('.fa-shopping-cart + .badge');
                if (cartBadge) {
                    cartBadge.textContent = data.cart_count;
                }

                setTimeout(() => {
                    btn.classList.replace('btn-success', 'btn-primary');
                    btn.innerHTML = originalHtml;
                    btn.disabled = false;
                }, 2000);
            } else {
                throw new Error(data.message || 'Failed to add to cart');
            }
        } catch (e) {
            alert('Failed to add to cart: ' + e.message);
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    };

    // --- Event Listeners ---

    // Apply & Clear Buttons
    if (applyBtn) {
        applyBtn.addEventListener('click', () => {
            currentState.page = 1;
            fetchBooks();
        });
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            currentState = {
                ...currentState,
                q: '',
                category: 'All',
                price_max: 2000,
                author: '',
                in_stock: false,
                page: 1
            };

            // Reset UI
            searchInput.value = '';
            categorySelect.value = 'All';
            authorInput.value = '';
            stockCheck.checked = false;
            clearSearchBtn.classList.add('d-none');

            if (priceSlider && priceSlider.noUiSlider) {
                priceSlider.noUiSlider.set([0, 2000]);
            }

            fetchBooks();
        });
    }

    if (emptyClearBtn) {
        emptyClearBtn.addEventListener('click', () => clearFiltersBtn.click());
    }


    // Search with Debounce
    let searchTimeout;
    const debounce = (fn, delay = 500) => {
        return (...args) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => fn(...args), delay);
        };
    };

    searchInput.addEventListener('input', (e) => {
        currentState.q = e.target.value.trim();
        debounce(() => {
            currentState.page = 1;
            fetchBooks();
        })();
        clearSearchBtn.classList.toggle('d-none', !currentState.q);
    });

    // Author Filter
    authorInput.addEventListener('input', (e) => {
        currentState.author = e.target.value.trim();
        // Optional: Auto-fetch or wait for Apply
        // To be responsive matching search, let's auto-fetch
        debounce(() => {
            currentState.page = 1;
            fetchBooks();
        })();
    });

    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        currentState.q = '';
        clearSearchBtn.classList.add('d-none');
        currentState.page = 1;
        fetchBooks();
    });

    // Instant Filter Changes
    categorySelect.addEventListener('change', (e) => {
        currentState.category = e.target.value;
        currentState.page = 1;
        fetchBooks();
    });

    if (stockCheck) {
        stockCheck.addEventListener('change', (e) => {
            currentState.in_stock = e.target.checked;
            currentState.page = 1;
            fetchBooks();
        });
    }

    sortSelect.addEventListener('change', (e) => {
        currentState.sort = e.target.value;
        fetchBooks();
    });

    // View Toggles
    if (gridViewBtn) {
        gridViewBtn.addEventListener('click', () => {
            currentState.view = 'grid';
            localStorage.setItem('catalogView', 'grid');
            updateViewToggle('grid');
            renderBooks([]); // Will be refilled by current data
            fetchBooks();
        });
    }

    if (listViewBtn) {
        listViewBtn.addEventListener('click', () => {
            currentState.view = 'list';
            localStorage.setItem('catalogView', 'list');
            updateViewToggle('list');
            renderBooks([]);
            fetchBooks();
        });
    }

    function updateViewToggle(view) {
        if (view === 'grid') {
            gridViewBtn?.classList.add('active', 'btn-primary');
            gridViewBtn?.classList.remove('btn-outline-secondary');
            listViewBtn?.classList.remove('active', 'btn-primary');
            listViewBtn?.classList.add('btn-outline-secondary');
        } else {
            listViewBtn?.classList.add('active', 'btn-primary');
            listViewBtn?.classList.remove('btn-outline-secondary');
            gridViewBtn?.classList.remove('active', 'btn-primary');
            gridViewBtn?.classList.add('btn-outline-secondary');
        }
    }

    // Helper: Update URL without page reload
    function updateURL() {
        const url = new URL(window.location);
        url.searchParams.set('q', currentState.q);
        url.searchParams.set('category', currentState.category);
        url.searchParams.set('sort', currentState.sort);
        url.searchParams.set('page', currentState.page);

        if (currentState.author) {
            url.searchParams.set('author', currentState.author);
        } else {
            url.searchParams.delete('author');
        }

        window.history.replaceState({}, '', url);
    }

    // UI Helpers
    function showLoader() {
        bookContainer.style.opacity = '0.5';
        bookContainer.style.pointerEvents = 'none';
    }

    function hideLoader() {
        bookContainer.style.opacity = '1';
        bookContainer.style.pointerEvents = 'auto';
        if (loader) {
            loader.classList.add('d-none');
        }
    }
});

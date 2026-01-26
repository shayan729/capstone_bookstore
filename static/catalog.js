document.addEventListener('DOMContentLoaded', function () {
    const bookGrid = document.getElementById('bookGrid');
    const pagination = document.getElementById('pagination');
    const resultsCount = document.getElementById('resultsCount');
    const loader = document.getElementById('loader');

    // Filter Inputs
    const searchInput = document.getElementById('searchInput');
    const categorySelect = document.getElementById('categorySelect');
    const priceRange = document.getElementById('priceRange');
    const priceValue = document.getElementById('priceValue');
    const authorInput = document.getElementById('authorInput');
    const stockCheck = document.getElementById('stockCheck');
    const applyBtn = document.getElementById('applyFilters');
    const clearBtn = document.getElementById('clearFilters');
    const sortSelect = document.getElementById('sortSelect');

    let currentPage = 1;

    // Price Slider UI Update
    priceRange.addEventListener('input', (e) => {
        priceValue.textContent = `Up to ₹${e.target.value}`;
    });

    // Fetch Books Function
    async function fetchBooks(page = 1) {
        // Show loader
        bookGrid.style.opacity = '0.5';
        loader.classList.remove('d-none');

        const params = new URLSearchParams({
            q: searchInput.value,
            category: categorySelect.value,
            price_max: priceRange.value,
            author: authorInput.value,
            in_stock: stockCheck.checked,
            sort: sortSelect.value,
            page: page
        });

        try {
            const response = await fetch(`/api/books?${params}`);
            const data = await response.json();

            renderBooks(data.books);
            renderPagination(data.page, data.pages);
            resultsCount.textContent = `Showing ${data.total} books`;
            currentPage = data.page;

        } catch (error) {
            console.error('Error fetching books:', error);
            bookGrid.innerHTML = '<div class="col-12 text-center text-danger">Failed to load books. Please try again.</div>';
        } finally {
            // Hide loader
            bookGrid.style.opacity = '1';
            loader.classList.add('d-none');
        }
    }

    // Render Books Grid
    function renderBooks(books) {
        bookGrid.innerHTML = '';

        if (books.length === 0) {
            bookGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-search text-muted display-4"></i>
                    <p class="mt-3 text-muted">No books found matching your criteria.</p>
                </div>
            `;
            return;
        }

        books.forEach(book => {
            const isOutOfStock = book.stock <= 0;
            const stockBadge = isOutOfStock
                ? '<span class="badge bg-secondary position-absolute top-0 start-0 m-3">Out of Stock</span>'
                : `<span class="badge bg-success position-absolute top-0 start-0 m-3">In Stock: ${book.stock}</span>`;

            const btnClass = isOutOfStock ? 'btn-secondary disabled' : 'btn-outline-primary';
            const cardOpacity = isOutOfStock ? 'opacity-75' : '';

            const bookCard = `
                <div class="col-6 col-md-4 col-xl-3">
                    <div class="card book-card h-100 border-0 shadow-sm ${cardOpacity}">
                        ${stockBadge}
                        <img src="${book.image}" class="card-img-top" alt="${book.title}" style="height: 240px; object-fit: cover;">
                        <div class="card-body d-flex flex-column p-3">
                            <small class="text-muted mb-1">${book.category}</small>
                            <h6 class="card-title fw-bold text-truncate-2 mb-1" style="min-height: 2.4em;">${book.title}</h6>
                            <p class="small text-muted mb-2">${book.author}</p>
                            
                            <div class="mt-auto">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <span class="fs-5 fw-bold text-primary">₹${book.price}</span>
                                </div>
                                <div class="d-grid gap-2">
                                    <button class="btn ${btnClass} btn-sm"><i class="bi bi-cart-plus"></i> Add to Cart</button>
                                    <button class="btn btn-light btn-sm text-muted">Details</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            bookGrid.innerHTML += bookCard;
        });
    }

    // Render Pagination
    function renderPagination(current, total) {
        pagination.innerHTML = '';

        if (total <= 1) return;

        // Previous
        const prevDisabled = current === 1 ? 'disabled' : '';
        pagination.innerHTML += `
            <li class="page-item ${prevDisabled}">
                <a class="page-link" href="#" data-page="${current - 1}">&laquo;</a>
            </li>
        `;

        // Pages
        for (let i = 1; i <= total; i++) {
            const active = i === current ? 'active' : '';
            pagination.innerHTML += `
                <li class="page-item ${active}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }

        // Next
        const nextDisabled = current === total ? 'disabled' : '';
        pagination.innerHTML += `
            <li class="page-item ${nextDisabled}">
                <a class="page-link" href="#" data-page="${current + 1}">&raquo;</a>
            </li>
        `;

        // Add event listeners to new links
        document.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.target.dataset.page);
                if (page && page !== currentPage) {
                    fetchBooks(page);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }

    // Event Listeners for Filters
    applyBtn.addEventListener('click', () => fetchBooks(1));

    // Auto-search logic (debounced for text inputs)
    let timeout = null;
    const debounceSearch = () => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fetchBooks(1), 500);
    };

    searchInput.addEventListener('input', debounceSearch);
    authorInput.addEventListener('input', debounceSearch);
    categorySelect.addEventListener('change', () => fetchBooks(1));
    stockCheck.addEventListener('change', () => fetchBooks(1));
    sortSelect.addEventListener('change', () => fetchBooks(1));

    // Clear Filters
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        categorySelect.value = 'All';
        priceRange.value = 2000;
        priceValue.textContent = 'Up to ₹2000';
        authorInput.value = '';
        stockCheck.checked = false;
        sortSelect.value = 'newest';
        fetchBooks(1);
    });

    // Initial Fetch
    fetchBooks();
});

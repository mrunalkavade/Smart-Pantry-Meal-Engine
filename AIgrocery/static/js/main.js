document.addEventListener('DOMContentLoaded', () => {
    // Navigation Logic
    const navItems = document.querySelectorAll('.nav-item');
    const views = document.querySelectorAll('.view');
    const modal = document.getElementById('recipe-modal');
    const closeModalBtn = document.getElementById('close-modal');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('data-target');
            
            navItems.forEach(n => n.classList.remove('active'));
            if(item.style.display !== 'none') item.classList.add('active'); // Don't highlight hidden cart
            
            views.forEach(v => { v.classList.add('hidden'); v.classList.remove('active'); });
            document.getElementById(`view-${targetId}`).classList.remove('hidden');
            document.getElementById(`view-${targetId}`).classList.add('active');

            if(targetId === 'dashboard') fetchHomepage();
            if(targetId === 'pantry') fetchPantry();
            if(targetId === 'cart') fetchCart();
            window.scrollTo(0,0);
        });
    });

    closeModalBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if(e.target === modal) modal.classList.add('hidden');
    });

    // Category Logic
    const chips = document.querySelectorAll('.category-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const cat = chip.getAttribute('data-category');
            fetchHomepage(cat);
            chips.forEach(c => { c.style.borderColor = 'transparent'; c.style.color = 'var(--text-main)'; });
            chip.style.borderColor = 'var(--primary)';
            chip.style.color = 'var(--primary)';
        });
    });

    // Sync Action
    document.getElementById('btn-sync-receipt').addEventListener('click', async () => {
        const status = document.getElementById('sync-status');
        status.style.display = 'block';
        status.style.backgroundColor = '#feebc8';
        status.style.color = '#c05621';
        status.innerText = "Parsing digital receipt order with AI...";
        
        try {
            const res = await fetch('/api/ingest_receipt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ receipt_text: "Fresh Salmon, Almond Milk, Brown Rice, Spinach" })
            });
            const data = await res.json();
            status.innerText = `Success! Added ${data.items_added} items automatically.`;
            status.style.backgroundColor = '#c6f6d5';
            status.style.color = '#22543d';
            fetchHomepage(); // refresh dashboard
            setTimeout(() => status.style.display = 'none', 4000);
        } catch(e) {
            status.innerText = "Error syncing receipt.";
            status.style.color = "red";
        }
    });

    // Planner UI - Generation
    document.getElementById('plan-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const goal = document.getElementById('diet-goal').value;
        const resBox = document.getElementById('plan-results');
        
        resBox.classList.remove('hidden');
        resBox.innerHTML = '<p>Generating AI Recipe based on Pantry...</p>';

        const res = await fetch('/api/planner', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({goal: goal})
        });
        const data = await res.json();
        
        resBox.innerHTML = `<button class="btn-primary w-100" onclick='window.showRecipeModal(${JSON.stringify(data.recipe).replace(/'/g, "&apos;")})'>View Generated Recipe</button>`;
        window.showRecipeModal(data.recipe);
    });

    // Chatbot Implementation
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');
    const chatHistory = document.getElementById('chat-history');

    sendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') sendChatMessage(); });

    async function sendChatMessage() {
        const text = chatInput.value.trim();
        if(!text) return;
        
        const userDiv = document.createElement('div');
        userDiv.className = 'msg user-msg';
        userDiv.innerText = text;
        chatHistory.appendChild(userDiv);
        chatInput.value = '';
        chatHistory.scrollTop = chatHistory.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await res.json();
            
            if(data.reply) {
                const botDiv = document.createElement('div');
                botDiv.className = 'msg bot-msg';
                botDiv.innerHTML = data.reply.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                chatHistory.appendChild(botDiv);
            }
            
            if (data.recipe) {
                const btnDiv = document.createElement('div');
                btnDiv.innerHTML = `<button class="btn-primary btn-sm mt-2" onclick='window.showRecipeModal(${JSON.stringify(data.recipe).replace(/'/g, "&apos;")})'>Open ${data.recipe.title}</button>`;
                chatHistory.appendChild(btnDiv);
            }

            if (data.recipes) {
                data.recipes.forEach(r => {
                    const btnDiv = document.createElement('div');
                    btnDiv.innerHTML = `<button class="btn-primary btn-sm mt-1" onclick='window.showRecipeModal(${JSON.stringify(r).replace(/'/g, "&apos;")})'>Open ${r.title}</button>`;
                    chatHistory.appendChild(btnDiv);
                });
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        } catch(e) {
            console.error(e);
        }
    }

    fetchHomepage();
});

// Modal Logic
window.showRecipeModal = function(recipe) {
    const modal = document.getElementById('recipe-modal');
    const modalBody = document.getElementById('modal-body');
    
    let ingHTML = recipe.ingredients_status.map(i => {
        if(i.includes('✗')) return `<li style="color:#c53030; font-weight:500;">${i}</li>`;
        return `<li style="color:#22543d;">${i}</li>`;
    }).join('');
    
    let stepHTML = recipe.steps.map(s => `<li>${s}</li>`).join('');
    
    let missingAction = '';
    if (recipe.missing_ingredients && recipe.missing_ingredients.length > 0) {
        let itemsHtml = recipe.missing_ingredients.map(ing => `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; border-bottom:1px solid #fbd38d; padding-bottom:5px;">
                <span>${ing}</span>
                <button class="btn-primary btn-sm" onclick="window.triggerAddToCart('${ing.replace(/'/g, "\\'")}', this)">Add to Cart</button>
            </div>
        `).join('');
        
        missingAction = `
            <div class="card p-3 mt-3" style="background:#fffaf0; border:1px solid #ecc94b; border-radius:12px;">
                <h4 style="color:#b7791f; margin-bottom:12px;">Missing Ingredients</h4>
                ${itemsHtml}
            </div>
        `;
    }
    
    modalBody.innerHTML = `
        <img src="${recipe.image_url}" loading="lazy" style="width:100%; height:200px; object-fit:cover; border-radius:12px; margin-bottom:15px; background:#f7fafc;">
        <h3 style="font-size:1.4rem; font-weight:700;">${recipe.title}</h3>
        <p class="subtitle mt-1">${recipe.description || ''}</p>
        <div style="margin: 15px 0;">
            <span class="tag info">${recipe.nutrition_tag || 'Balanced'}</span>
            <span class="tag success">${recipe.pantry_match_pct || 100}% Pantry Match</span>
        </div>
        
        <h4 class="mt-3 mb-2">Ingredients</h4>
        <ul style="padding-left:20px; font-size:0.9rem; line-height:1.6;">${ingHTML}</ul>
        
        ${missingAction}

        <h4 class="mt-4 mb-2">Instructions</h4>
        <ol style="padding-left:20px; font-size:0.9rem; line-height:1.6;">${stepHTML}</ol>
        <div style="background:var(--secondary); padding:10px; border-radius:8px; margin-top:20px; font-size:0.85rem; font-weight:600; text-align:center;">
            Macros: ${recipe.macros}
        </div>
    `;
    modal.classList.remove('hidden');
};

window.triggerAddToCart = async function(itemName, btnElement = null) {
    if(btnElement) btnElement.innerText = "...";
    await fetch('/api/cart', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: itemName})
    });
    if(btnElement) {
        btnElement.innerText = "Added ✓";
        btnElement.style.background = "#319795";
        btnElement.disabled = true;
    } else {
        alert('Added to Cart!');
    }
};

// Data Fetchers
async function fetchHomepage(category = 'All') {
    const res = await fetch(`/api/home_data?category=${category}`);
    const data = await res.json();
    
    document.getElementById('pantry-summary-header').innerText = `${data.pantry_summary.total_items} Items | Est. ₹${data.pantry_summary.total_value.toFixed(2)}`;
    
    const catResults = document.getElementById('category-results');
    const homeSections = document.getElementById('home-sections');
    
    const renderCard = (item) => `
        <div class="h-card" style="min-width: 150px; cursor:pointer;" onclick="window.triggerAddToCart('${item.name}')">
            <img src="${item.image_url}" loading="lazy" class="h-card-img" style="height:100px; width:100%; object-fit:cover; background:#f7fafc;">
            <div class="h-card-body">
                <h4 class="h-card-title">${item.name}</h4>
                <div class="tag info mt-1">${item.category}</div>
                <button class="btn-primary btn-sm w-100 mt-2" onclick="event.stopPropagation(); window.triggerAddToCart('${item.name}')">Add to Cart</button>
            </div>
        </div>
    `;

    if (data.is_category) {
        homeSections.classList.add('hidden');
        catResults.classList.remove('hidden');
        catResults.innerHTML = data.category_items.map(item => `
            <div class="list-card">
                <img src="${item.image_url}" loading="lazy" class="list-img" style="background:#f7fafc;">
                <div class="list-info">
                    <div class="list-title">${item.name}</div>
                    <div class="tag info mt-1" style="font-size:0.65rem;">Cat: ${item.category}</div>
                </div>
                <div class="list-action">
                    <button class="btn-primary btn-sm mt-1" onclick="window.triggerAddToCart('${item.name}')">Add to Cart</button>
                </div>
            </div>
        `).join('') || '<p class="subtitle mt-3 " style="grid-column: 1 / -1;">No items found for this category.</p>';
    } else {
        homeSections.classList.remove('hidden');
        catResults.classList.add('hidden');
        
        document.getElementById('dash-popular').innerHTML = data.popular.map(i => renderCard(i)).join('');
        document.getElementById('dash-recommended').innerHTML = data.recommended.map(i => renderCard(i)).join('');
        document.getElementById('dash-fresh').innerHTML = data.fresh.map(i => renderCard(i)).join('');
        document.getElementById('dash-dairy').innerHTML = data.dairy.map(i => renderCard(i)).join('');
        document.getElementById('dash-quick').innerHTML = data.quick.map(i => renderCard(i)).join('');
    }
}

async function fetchPantry() {
    const res = await fetch('/api/pantry');
    const items = await res.json();
    document.getElementById('pantry-count').innerText = `${items.length} items`;
    
    const grid = document.getElementById('pantry-grid');
    grid.innerHTML = items.map(item => `
        <div class="list-card">
            <img src="${item.image_url}" loading="lazy" class="list-img" style="background:#f7fafc;">
            <div class="list-info">
                <div class="list-title">${item.name}</div>
                <div class="list-desc">Qty: ${item.quantity}  |  ${item.nutrition_value}</div>
                <div class="tag info mt-1" style="font-size:0.65rem;">Cat: ${item.category}</div>
            </div>
            <div class="list-action">
                <div class="tag warning">Exp: ${item.expiry_date}</div>
            </div>
        </div>
    `).join('');
}

async function fetchCart() {
    const res = await fetch('/api/cart');
    const data = await res.json();
    const container = document.getElementById('cart-container');
    const comparisonPanel = document.getElementById('store-comparison-panel');
    const btnBuy = document.getElementById('btn-buy-cheapest');

    if(!data.cart || data.cart.length === 0) {
        comparisonPanel.innerHTML = '';
        btnBuy.classList.add('hidden');
        container.innerHTML = '<p class="subtitle mt-3">Your cart is empty.</p>';
        return;
    }

    // 1. Render Store Comparison
    let cmpHtml = '';
    const stores = ["Instamart", "BigBasket", "DMart"];
    window.currentBestStore = data.best_store;
    
    stores.forEach(st => {
        let isBest = st === data.best_store;
        let badgeHtml = isBest && data.savings > 0 ? `<span class="savings-badge">You save ₹${data.savings}</span>` : '';
        cmpHtml += `
            <div class="store-card ${isBest ? 'best-deal' : ''}" onclick="window.overrideCartStore('${st}')">
                <div class="store-name">
                    ${st} ${isBest ? '⭐' : ''} ${badgeHtml}
                </div>
                <div class="store-price">₹${data.store_totals[st] || 0}</div>
            </div>
        `;
    });
    comparisonPanel.innerHTML = cmpHtml;
    btnBuy.classList.remove('hidden');

    // 2. Render Cart Items
    let html = '<div class="item-grid">';
    html += data.cart.map(item => `
        <div class="list-card" style="align-items:flex-start;">
            <img src="${item.image_url || 'https://loremflickr.com/100/100/food'}" loading="lazy" class="list-img" style="background:#f7fafc;">
            <div class="list-info">
                <div class="list-title">${item.name}</div>
                <div class="list-desc mt-1">${item.measurement || '1 Pack'} | Cat: ${item.category}</div>
                <select class="store-dropdown" onchange="window.switchItemStore(${item.id}, this.value)">
                    ${stores.map(s => `<option value="${s}" ${s === item.store ? 'selected' : ''}>${s} (₹${item.prices && item.prices[s] ? item.prices[s] : item.price})</option>`).join('')}
                </select>
                <div class="tag success mt-1" style="font-size:0.65rem;">✓ ${item.badge || 'Added'}</div>
            </div>
            <div class="list-action" style="align-self:center; display:flex; flex-direction:column; align-items:flex-end; gap:8px;">
                <div class="price-tag">₹${(item.price * (item.quantity || 1)).toFixed(2)}</div>
                <div style="display:flex; align-items:center; gap:6px;">
                    <button onclick="window.cartQty(${item.id},'decrease')" style="width:28px;height:28px;border-radius:50%;border:1px solid var(--border);background:var(--secondary);font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;">−</button>
                    <span style="font-weight:700; min-width:16px; text-align:center;">${item.quantity || 1}</span>
                    <button onclick="window.cartQty(${item.id},'increase')" style="width:28px;height:28px;border-radius:50%;border:none;background:var(--primary);color:white;font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;">+</button>
                </div>
            </div>
        </div>
    `).join('');
    html += '</div>';
    
    container.innerHTML = html;
}

window.overrideCartStore = async function(storeName) {
    if(!confirm(`Switch entire cart to ${storeName}?`)) return;
    await fetch('/api/cart/checkout_store', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({store: storeName})
    });
    fetchCart();
};

window.buyCheapestCart = async function() {
    if (!confirm('Complete purchase? Items will be moved to your Pantry.')) return;
    
    const btn = document.getElementById('btn-buy-cheapest');
    if (btn) { btn.innerText = 'Processing...'; btn.disabled = true; }

    try {
        const res = await fetch('/api/cart/checkout', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        const data = await res.json();

        if (res.ok) {
            // Show success then switch to pantry
            alert(data.message || 'Purchase complete! Your pantry has been updated.');
            // Refresh cart (now empty) and switch to pantry view
            fetchCart();
            document.querySelector('[data-target="pantry"]').click();
        } else {
            alert(data.message || 'Checkout failed.');
            if (btn) { btn.innerText = 'Buy Selected Cart'; btn.disabled = false; }
        }
    } catch (e) {
        alert('Checkout error. Please try again.');
        if (btn) { btn.innerText = 'Buy Selected Cart'; btn.disabled = false; }
    }
};

window.switchItemStore = async function(itemId, newStore) {
    await fetch('/api/cart/switch_item', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({item_id: itemId, store: newStore})
    });
    fetchCart();
};

window.cartQty = async function(itemId, action) {
    const res = await fetch(`/api/cart/${itemId}/quantity`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: action})
    });
    // Always re-render the cart (whether quantity changed or item deleted)
    fetchCart();
};

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        API_URLS: [
            './deliveries_index.json',
            '../site/deliveries_index.json',
            'https://eddiedevlife.github.io/agentix-vault/deliveries_index.json',
            'https://eddiedevlife.github.io/agentix-vault/site/deliveries_index.json'
        ],
        THEME_KEY: 'agentix-theme',
        DEFAULT_THEME: 'dark'
    };

    // DOM Elements
    const elements = {
        toggleBtn: document.getElementById('theme-toggle'),
        menuBtn: document.getElementById('menu-toggle'),
        mobileNav: document.getElementById('mobile-nav'),
        html: document.documentElement,
        demoContainer: document.getElementById('demo-stats'),
        demoList: document.getElementById('demo-list')
    };

    /**
     * Theme Management
     */
    const ThemeManager = {
        init() {
            const savedTheme = localStorage.getItem(CONFIG.THEME_KEY) || CONFIG.DEFAULT_THEME;
            this.apply(savedTheme);
            
            elements.toggleBtn?.addEventListener('click', () => {
                const current = elements.html.getAttribute('data-theme');
                this.apply(current === 'dark' ? 'light' : 'dark');
            });
        },
        apply(theme) {
            elements.html.setAttribute('data-theme', theme);
            localStorage.setItem(CONFIG.THEME_KEY, theme);
        }
    };

    /**
     * Mobile Menu
     */
    const MenuManager = {
        init() {
            if (!elements.menuBtn || !elements.mobileNav) return;

            const close = () => this.setOpen(false);
            elements.menuBtn.addEventListener('click', () => {
                const isOpen = elements.menuBtn.getAttribute('aria-expanded') === 'true';
                this.setOpen(!isOpen);
            });
            elements.mobileNav.addEventListener('click', (e) => {
                const target = e.target;
                if (target && target.tagName === 'A') close();
            });
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') close();
            });
        },
        setOpen(open) {
            if (!elements.menuBtn || !elements.mobileNav) return;
            elements.menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
            elements.mobileNav.hidden = !open;
        }
    };

    /**
     * Data Fetching & UI Rendering
     */
    const Dashboard = {
        async init() {
            if (!elements.demoContainer || !elements.demoList) return;
            await this.load();
        },

        async load() {
            try {
                const data = await this.fetchFirstOk(CONFIG.API_URLS);
                this.render(data?.deliveries || []);
            } catch (error) {
                console.error('Vault Connection Failure:', error);
                this.renderError();
            }
        },

        async fetchFirstOk(urls) {
            let lastError = null;

            for (const url of urls) {
                try {
                    const response = await fetch(this.withCacheBust(url), { cache: 'no-store' });
                    if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
                    return await response.json();
                } catch (err) {
                    lastError = err;
                }
            }

            throw lastError || new Error('Failed to fetch metrics');
        },

        withCacheBust(url) {
            try {
                const u = new URL(url, window.location.href);
                u.searchParams.set('_ts', String(Date.now()));
                return u.toString();
            } catch {
                const sep = url.includes('?') ? '&' : '?';
                return `${url}${sep}_ts=${Date.now()}`;
            }
        },

        render(deliveries) {
            const total = deliveries.length;
            const totalElapsed = deliveries.reduce((acc, d) => acc + (d.elapsed_seconds || 0), 0);
            const avgElapsed = total > 0 ? (totalElapsed / total).toFixed(1) : 0;
            const passed = deliveries.filter(d => (d.validation_status || '').toLowerCase() === 'passed').length;

            elements.demoContainer.innerHTML = `
                <div class="stat-card">
                    <strong>${total}</strong>
                    <span>Entregas totais</span>
                </div>
                <div class="stat-card">
                    <strong>${passed}</strong>
                    <span>Validadas</span>
                </div>
                <div class="stat-card">
                    <strong>${avgElapsed}s</strong>
                    <span>Tempo médio</span>
                </div>
            `;

            if (total === 0) {
                elements.demoList.innerHTML = '<div class="skeleton-card">Nenhuma entrega registrada ainda.</div>';
                return;
            }

            const lastFive = deliveries.slice(-5).reverse();
            elements.demoList.innerHTML = lastFive.map(d => this.createListItem(d)).join('');
        },

        createListItem(d) {
            const date = d.updated_at ? new Date(d.updated_at).toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            }) : 'Data N/A';
            
            const status = (d.validation_status || 'pending').toLowerCase();
            const badgeClass = status === 'passed' ? 'badge-done' : (status === 'working' ? 'badge-working' : 'badge-idle');
            const name = d.delivery_name || d.name || 'Entrega sem nome';
            
            return `
                <div class="delivery-item">
                    <span><strong>${name}</strong></span>
                    <span style="color: var(--text-secondary); font-size: 0.9rem;">${date}</span>
                    <span class="badge ${badgeClass}">${status}</span>
                </div>
            `;
        },

        renderError() {
            const isFile = window.location.protocol === 'file:';
            elements.demoContainer.innerHTML = `
                <div class="skeleton-card" style="border-color: #ef4444; color: #ef4444;">
                    <p>⚠️ <strong>Conexão interrompida</strong></p>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem;">Não foi possível sincronizar com o Agentix Vault.</p>
                    ${isFile ? '<p style="font-size: 0.85rem; margin-top: 0.5rem; color: var(--text-secondary);">Dica: evite abrir via <code>file://</code>. Rode um servidor local (ex: <code>python3 -m http.server</code>) para o fetch funcionar.</p>' : ''}
                    <button onclick="window.location.reload()" class="btn btn-secondary" style="margin-top: 1rem; padding: 0.5rem 1rem; font-size: 0.8rem;">Tentar novamente</button>
                </div>
            `;
            elements.demoList.innerHTML = '';
        }
    };

    // Initialize all modules
    ThemeManager.init();
    MenuManager.init();
    Dashboard.init();

})();

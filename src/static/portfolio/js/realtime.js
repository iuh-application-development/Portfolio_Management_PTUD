/**
 * Realtime Data Updates for ASTROLUX Portfolio Management
 * Handles auto-refresh for dashboard, wallet, admin stats, and market data
 */

class RealtimeManager {
    constructor() {
        this.intervals = new Map();
        this.isUpdating = new Map();
        this.isPageVisible = !document.hidden;
        this.isOnline = navigator.onLine;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Page visibility API
        document.addEventListener('visibilitychange', () => {
            this.isPageVisible = !document.hidden;
            if (this.isPageVisible) {
                console.log('Page visible - resuming updates');
                this.resumeUpdates();
            } else {
                console.log('Page hidden - pausing updates');
                this.pauseUpdates();
            }
        });
        
        // Network status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.resumeUpdates();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.pauseUpdates();
        });
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => {
            this.stopAllUpdates();
        });
    }
    
    // Utility functions
    formatCurrency(amount) {
        return new Intl.NumberFormat('vi-VN').format(Math.round(amount));
    }
    
    formatDateTime(date = new Date()) {
        return date.toLocaleString('vi-VN');
    }
    
    showNotification(message, type = 'info') {
        if (window.showRealtimeNotification) {
            window.showRealtimeNotification(message, type);
        }
    }
    
    // Generic fetch with error handling
    async fetchData(url, updateKey) {
        if (this.isUpdating.get(updateKey) || !this.isOnline || !this.isPageVisible) {
            return null;
        }
        
        this.isUpdating.set(updateKey, true);
        
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Unknown error');
            }
            
            return data.data;
        } catch (error) {
            console.error(`Error fetching ${updateKey}:`, error);
            this.showNotification(`Lỗi cập nhật ${updateKey}: ${error.message}`, 'error');
            return null;
        } finally {
            this.isUpdating.set(updateKey, false);
        }
    }
    
    // Dashboard updates
    async updateDashboard() {
        const data = await this.fetchData('/api/dashboard-data/', 'dashboard');
        if (!data) return;
        
        try {
            // Update wallet balance
            const walletBalanceEl = document.querySelector('#wallet-balance');
            if (walletBalanceEl) {
                this.updateElementWithAnimation(walletBalanceEl, this.formatCurrency(data.wallet_balance));
            }
            
            // Update total stocks value
            const totalAssetsEl = document.querySelector('#total-assets');
            if (totalAssetsEl) {
                this.updateElementWithAnimation(totalAssetsEl, this.formatCurrency(data.total_assets));
            }
            
            // Update profit/loss
            this.updateProfitLoss(data.total_profit_loss, data.profit_loss_percentage);
            
            // Update number of stocks
            const numStocksEl = document.querySelector('#num-stocks');
            if (numStocksEl) {
                this.updateElementWithAnimation(numStocksEl, data.number_of_stocks);
            }
            
            // Update last updated time
            const lastUpdatedEl = document.querySelector('#last-updated');
            if (lastUpdatedEl) {
                lastUpdatedEl.textContent = `Cập nhật lúc: ${data.last_updated}`;
            }
            
            this.pulseStatCards();
            console.log('Dashboard updated:', data.last_updated);
            
        } catch (error) {
            console.error('Error updating dashboard UI:', error);
        }
    }
    
    // Wallet updates
    async updateWallet() {
        const data = await this.fetchData('/api/wallet-data/', 'wallet');
        if (!data) return;
        
        try {
            // Update current balance
            const balanceEl = document.querySelector('#current-balance');
            if (balanceEl) {
                const oldBalance = balanceEl.textContent;
                const newBalance = this.formatCurrency(data.balance) + ' VNĐ';
                
                if (oldBalance !== newBalance) {
                    this.highlightChange(balanceEl);
                    balanceEl.textContent = newBalance;
                }
            }
            
            // Update totals
            this.updateElementIfExists('#total-deposit', this.formatCurrency(data.total_deposit) + ' VNĐ');
            this.updateElementIfExists('#total-withdraw', this.formatCurrency(data.total_withdraw) + ' VNĐ');
            this.updateElementIfExists('#monthly-deposit', this.formatCurrency(data.monthly_deposit) + ' VNĐ');
            this.updateElementIfExists('#monthly-withdraw', this.formatCurrency(data.monthly_withdraw) + ' VNĐ');
            
            // Update recent transactions
            this.updateRecentTransactions(data.recent_transactions);
            
            // Update timestamp
            const lastUpdatedEl = document.querySelector('#wallet-last-updated');
            if (lastUpdatedEl) {
                lastUpdatedEl.textContent = `Cập nhật: ${data.last_updated}`;
            }
            
            console.log('Wallet updated:', data.last_updated);
            
        } catch (error) {
            console.error('Error updating wallet UI:', error);
        }
    }
    
    // Admin stats updates
    async updateAdminStats() {
        const data = await this.fetchData('/api/admin-stats/', 'admin');
        if (!data) return;
        
        try {
            // Update stats with animation
            this.updateElementWithAnimation('#total-users', data.total_users);
            this.updateElementWithAnimation('#total-transactions', data.total_transactions);
            
            // Special handling for pending withdrawals
            const pendingEl = document.querySelector('#pending-withdrawals');
            if (pendingEl) {
                const oldValue = parseInt(pendingEl.textContent) || 0;
                const newValue = data.pending_withdrawals;
                
                this.updateElementWithAnimation(pendingEl, newValue);
                
                // Highlight if new pending transactions
                if (newValue > oldValue) {
                    this.pulseElement(pendingEl.closest('.stats-card'));
                    this.showNotification(`Có ${newValue - oldValue} giao dịch chờ duyệt mới!`, 'warning');
                }
            }
            
            // Update wallet balance
            const walletBalanceEl = document.querySelector('#total-wallet-balance');
            if (walletBalanceEl) {
                walletBalanceEl.textContent = this.formatCurrency(data.total_wallet_balance) + ' VNĐ';
            }
            
            // Update timestamp
            const lastUpdatedEl = document.querySelector('#admin-last-updated');
            if (lastUpdatedEl) {
                lastUpdatedEl.textContent = `Cập nhật lúc: ${data.last_updated}`;
            }
            
            console.log('Admin stats updated:', data.last_updated);
            
        } catch (error) {
            console.error('Error updating admin UI:', error);
        }
    }
    
    // Market data updates (simulated)
    async updateMarketData() {
        const data = await this.fetchData('/api/market-data/', 'market');
        if (!data) return;
        
        try {
            // Update market cards if they exist
            data.stocks.forEach(stock => {
                const stockCard = document.querySelector(`[data-symbol="${stock.symbol}"]`);
                if (stockCard) {
                    this.updateStockCard(stockCard, stock);
                }
            });
            
            console.log('Market data updated:', data.last_updated);
            
        } catch (error) {
            console.error('Error updating market UI:', error);
        }
    }
    
    // UI Helper methods
    updateElementWithAnimation(selector, newValue) {
        const element = typeof selector === 'string' ? document.querySelector(selector) : selector;
        if (!element) return;
        
        const oldValue = element.textContent;
        const newText = newValue.toString();
        
        if (oldValue !== newText) {
            element.style.transition = 'all 0.3s ease';
            element.style.transform = 'scale(1.05)';
            element.style.color = '#0d6efd';
            
            setTimeout(() => {
                element.textContent = newText;
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 150);
        }
    }
    
    updateElementIfExists(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = value;
        }
    }
    
    highlightChange(element) {
        element.style.transition = 'all 0.3s ease';
        element.style.backgroundColor = '#e3f2fd';
        setTimeout(() => {
            element.style.backgroundColor = '';
        }, 1000);
    }
    
    pulseElement(element) {
        if (element) {
            element.style.animation = 'pulse 2s';
            setTimeout(() => {
                element.style.animation = '';
            }, 2000);
        }
    }
    
    pulseStatCards() {
        document.querySelectorAll('.stat-card').forEach(card => {
            card.style.transition = 'transform 0.2s ease';
            card.style.transform = 'scale(1.02)';
            setTimeout(() => {
                card.style.transform = 'scale(1)';
            }, 200);
        });
    }
    
    updateProfitLoss(profitLoss, percentage) {
        const profitLossEl = document.querySelector('#profit-loss');
        const profitLossPercentEl = document.querySelector('#profit-loss-percent');
        
        if (profitLossEl && profitLossPercentEl) {
            const isProfit = profitLoss >= 0;
            const prefix = isProfit ? '+' : '';
            
            profitLossEl.textContent = prefix + this.formatCurrency(profitLoss);
            profitLossEl.className = `stat-card-value ${isProfit ? 'text-success' : 'text-danger'}`;
            
            profitLossPercentEl.textContent = prefix + percentage.toFixed(2) + '%';
            profitLossPercentEl.className = `badge ${isProfit ? 'bg-success-soft text-success' : 'bg-danger-soft text-danger'}`;
        }
    }
    
    updateRecentTransactions(transactions) {
        const tableBody = document.querySelector('#recent-transactions-tbody');
        if (!tableBody || !transactions) return;
        
        let html = '';
        transactions.forEach(transaction => {
            const iconClass = transaction.type === 'deposit' ? 'fa-arrow-down' : 'fa-arrow-up';
            const bgClass = transaction.type === 'deposit' ? 'bg-success-light text-success' : 'bg-danger-light text-danger';
            const amountPrefix = transaction.type === 'deposit' ? '+' : '-';
            const statusBadge = this.getStatusBadge(transaction.status);
            
            html += `
                <tr>
                    <td class="ps-4">${transaction.transaction_time}</td>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="icon-circle ${bgClass} me-2" style="width: 32px; height: 32px;">
                                <i class="fas ${iconClass}"></i>
                            </div>
                            <div>
                                <strong>${transaction.type_display}</strong>
                                ${transaction.description ? `<br><small class="text-muted">${transaction.description.substring(0, 50)}${transaction.description.length > 50 ? '...' : ''}</small>` : ''}
                            </div>
                        </div>
                    </td>
                    <td class="fw-medium ${transaction.type === 'deposit' ? 'text-success' : 'text-danger'}">
                        ${amountPrefix}${this.formatCurrency(transaction.quantity)} VNĐ
                    </td>
                    <td>
                        <span class="text-muted">${transaction.bank_name}</span>
                    </td>
                    <td>
                        ${statusBadge}
                    </td>
                    <td class="text-end pe-4">
                        <span class="text-monospace small">#${transaction.id}</span>
                    </td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    }
    
    getStatusBadge(status) {
        const statusMap = {
            'completed': '<span class="badge bg-success rounded-pill">Hoàn thành</span>',
            'pending': '<span class="badge bg-warning rounded-pill">Đang xử lý</span>',
            'failed': '<span class="badge bg-danger rounded-pill">Thất bại</span>',
            'cancelled': '<span class="badge bg-secondary rounded-pill">Đã hủy</span>'
        };
        return statusMap[status] || `<span class="badge bg-light text-dark rounded-pill">${status}</span>`;
    }
    
    updateStockCard(card, stock) {
        // Update stock price display
        const priceEl = card.querySelector('.stock-price');
        if (priceEl) {
            priceEl.textContent = this.formatCurrency(stock.price);
        }
        
        // Update change indicator
        const changeEl = card.querySelector('.stock-change');
        if (changeEl) {
            const prefix = stock.change_percent > 0 ? '+' : '';
            changeEl.textContent = prefix + stock.change_percent.toFixed(2) + '%';
            changeEl.className = `stock-change ${stock.trend === 'up' ? 'text-success' : stock.trend === 'down' ? 'text-danger' : 'text-muted'}`;
        }
    }
    
    // Interval management
    startUpdates(type, updateFunction, interval) {
        this.stopUpdates(type);
        
        // Initial update
        updateFunction.call(this);
        
        // Set interval
        const intervalId = setInterval(() => {
            if (this.isPageVisible && this.isOnline) {
                updateFunction.call(this);
            }
        }, interval);
        
        this.intervals.set(type, intervalId);
        console.log(`Started ${type} updates with ${interval/1000}s interval`);
    }
    
    stopUpdates(type) {
        const intervalId = this.intervals.get(type);
        if (intervalId) {
            clearInterval(intervalId);
            this.intervals.delete(type);
            console.log(`Stopped ${type} updates`);
        }
    }
    
    pauseUpdates() {
        console.log('Pausing all updates');
        // Intervals continue running but won't execute updates due to visibility check
    }
    
    resumeUpdates() {
        console.log('Resuming all updates');
        // Force immediate update for all active intervals
        this.intervals.forEach((intervalId, type) => {
            switch(type) {
                case 'dashboard':
                    this.updateDashboard();
                    break;
                case 'wallet':
                    this.updateWallet();
                    break;
                case 'admin':
                    this.updateAdminStats();
                    break;
                case 'market':
                    this.updateMarketData();
                    break;
            }
        });
    }
    
    stopAllUpdates() {
        this.intervals.forEach((intervalId, type) => {
            clearInterval(intervalId);
        });
        this.intervals.clear();
        console.log('Stopped all updates');
    }
    
    // Manual refresh functions
    manualRefresh(type) {
        switch(type) {
            case 'dashboard':
                this.updateDashboard();
                break;
            case 'wallet':
                this.updateWallet();
                break;
            case 'admin':
                this.updateAdminStats();
                break;
            case 'market':
                this.updateMarketData();
                break;
        }
        
        // Add spin effect to refresh buttons
        const refreshBtn = document.querySelector(`#${type}-refresh-btn, #manual-refresh-btn, #wallet-refresh-btn, #admin-refresh-btn`);
        if (refreshBtn) {
            const icon = refreshBtn.querySelector('i');
            if (icon) {
                icon.style.animation = 'spin 1s linear';
                setTimeout(() => {
                    icon.style.animation = '';
                }, 1000);
            }
        }
    }
}

// Initialize realtime manager
window.realtimeManager = new RealtimeManager();

// Page-specific initialization
document.addEventListener('DOMContentLoaded', function() {
    const path = window.location.pathname;
    
    // Dashboard updates (30 seconds)
    if (path === '/' || path === '/dashboard/') {
        window.realtimeManager.startUpdates('dashboard', window.realtimeManager.updateDashboard, 30000);
        
        // Manual refresh button
        const refreshBtn = document.querySelector('#manual-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                window.realtimeManager.manualRefresh('dashboard');
            });
        }
    }
    
    // Wallet updates (20 seconds)
    if (path === '/wallet/' || path.includes('/wallet')) {
        window.realtimeManager.startUpdates('wallet', window.realtimeManager.updateWallet, 20000);
        
        // Manual refresh button
        const refreshBtn = document.querySelector('#wallet-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                window.realtimeManager.manualRefresh('wallet');
            });
        }
    }
    
    // Admin updates (45 seconds)
    if (path.includes('/admin/dashboard')) {
        window.realtimeManager.startUpdates('admin', window.realtimeManager.updateAdminStats, 45000);
        
        // Manual refresh button
        const refreshBtn = document.querySelector('#admin-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                window.realtimeManager.manualRefresh('admin');
            });
        }
    }
    
    // Market data updates (60 seconds) - for asset list and market pages
    if (path.includes('/assets/') || path.includes('/market/')) {
        window.realtimeManager.startUpdates('market', window.realtimeManager.updateMarketData, 60000);
    }
}); 
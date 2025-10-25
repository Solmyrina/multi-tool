// Utility functions for trip detail page

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Get category color badge class
function getCategoryColor(category) {
    const colors = {
        'sightseeing': 'primary',
        'dining': 'success',
        'transport': 'warning',
        'entertainment': 'info',
        'shopping': 'secondary',
        'other': 'dark'
    };
    return colors[category] || 'secondary';
}

// Get priority color badge class
function getPriorityColor(priority) {
    const colors = {
        'must_see': 'danger',
        'high': 'warning',
        'medium': 'info',
        'low': 'secondary',
        'optional': 'light'
    };
    return colors[priority] || 'secondary';
}

// Get role badge color
function getRoleBadgeColor(role) {
    const colors = {
        'owner': 'danger',
        'editor': 'primary',
        'viewer': 'secondary'
    };
    return colors[role] || 'secondary';
}

// Export to window for global access
window.showToast = showToast;
window.getCategoryColor = getCategoryColor;
window.getPriorityColor = getPriorityColor;
window.getRoleBadgeColor = getRoleBadgeColor;

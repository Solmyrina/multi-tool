// Trip Detail Page Initialization
// This script initializes all modules when the page loads

document.addEventListener('DOMContentLoaded', function() {
    console.log('Trip detail page initializing... Trip ID:', typeof tripId !== 'undefined' ? tripId : 'undefined');
    
    // Verify tripId is available
    if (typeof tripId === 'undefined') {
        console.error('tripId not defined! Check that template sets it before loading scripts.');
        return;
    }
    
    // Initialize calendar module
    if (typeof Calendar !== 'undefined') {
        Calendar.init(tripId);
        console.log('✓ Calendar module initialized');
    } else {
        console.warn('Calendar module not loaded');
    }
    
    // Initialize modals (Bootstrap)
    try {
        if (typeof bootstrap !== 'undefined') {
            window.activityModal = new bootstrap.Modal(document.getElementById('activityModal'));
            window.accommodationModal = new bootstrap.Modal(document.getElementById('accommodationModal'));
            window.expenseModal = new bootstrap.Modal(document.getElementById('expenseModal'));
            window.packingModal = new bootstrap.Modal(document.getElementById('packingModal'));
            window.shareModal = new bootstrap.Modal(document.getElementById('shareModal'));
            window.permissionModal = new bootstrap.Modal(document.getElementById('permissionModal'));
            console.log('✓ Bootstrap modals initialized');
        }
    } catch (e) {
        console.warn('Error initializing modals:', e);
    }
    
    // Load initial tab content (Overview is shown by default)
    setTimeout(() => {
        if (typeof initializeMap === 'function') {
            initializeMap();
            console.log('✓ Map initialized on overview tab');
        }
    }, 100);
    
    console.log('✓ Trip detail page initialization complete');
});

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
            const modalIds = ['activityModal', 'accommodationModal', 'expenseModal', 'packingModal', 'shareModal', 'permissionModal'];
            modalIds.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    window[id] = new bootstrap.Modal(element);
                } else {
                    console.warn(`Modal element #${id} not found`);
                }
            });
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

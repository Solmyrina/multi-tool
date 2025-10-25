// Calendar Module - Week View with Drag & Drop
// Version: 2.0 - Refactored for clarity

const Calendar = {
    weekStart: new Date(),
    events: {},
    draggedEvent: null,
    dragStartY: 0,
    currentDropZone: null,
    
    // Initialize to start of week (Monday)
    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        // Adjust so Monday = 0, Sunday = 6
        const dayOffset = day === 0 ? 6 : day - 1;
        const diff = d.getDate() - dayOffset;
        const weekStart = new Date(d.setDate(diff));
        console.log('Week start:', weekStart.toDateString(), 'Day of week:', weekStart.getDay());
        return weekStart;
    },
    
    // Initialize calendar when tab is shown
    init(tripId) {
        console.log('Calendar.init() called');
        this.tripId = tripId;
        
        const calendarTab = document.getElementById('calendar-tab');
        if (calendarTab) {
            console.log('Calendar tab found, adding event listeners');
            
            // Bootstrap tab event
            calendarTab.addEventListener('shown.bs.tab', () => {
                console.log('Calendar tab shown event fired');
                const container = document.getElementById('calendarWeekView');
                console.log('Calendar container:', container);
                if (container && !container.querySelector('.calendar-week-grid')) {
                    console.log('Loading calendar with first event...');
                    this.loadFirstEvent();
                }
            });
            
            // Click backup
            calendarTab.addEventListener('click', () => {
                console.log('Calendar tab clicked');
                setTimeout(() => {
                    const container = document.getElementById('calendarWeekView');
                    if (container && !container.querySelector('.calendar-week-grid')) {
                        this.loadFirstEvent();
                    }
                }, 100);
            });
        } else {
            console.error('Calendar tab not found!');
        }
        
        // Setup navigation buttons
        const todayBtn = document.querySelector('[onclick="calendarToday()"]');
        const prevBtn = document.querySelector('[onclick="calendarPrevWeek()"]');
        const nextBtn = document.querySelector('[onclick="calendarNextWeek()"]');
        
        if (todayBtn) todayBtn.onclick = () => this.goToday();
        if (prevBtn) prevBtn.onclick = () => this.prevWeek();
        if (nextBtn) nextBtn.onclick = () => this.nextWeek();
    },
    
    // Find and load first event date
    async loadFirstEvent() {
        console.log('loadFirstEvent() called');
        try {
            const [activitiesRes, accommodationsRes] = await Promise.all([
                fetch(`/api/trips/${this.tripId}/activities`),
                fetch(`/api/trips/${this.tripId}/accommodations`)
            ]);
            
            console.log('Activities response:', activitiesRes.status);
            console.log('Accommodations response:', accommodationsRes.status);
            
            const activities = await activitiesRes.json();
            const accommodations = await accommodationsRes.json();
            
            console.log('Activities count:', activities.length);
            console.log('Accommodations count:', accommodations.length);
            
            let firstDate = null;
            
            // Find earliest activity
            activities.forEach(activity => {
                const activityDate = new Date(activity.start_datetime || activity.start_date);
                if (!firstDate || activityDate < firstDate) {
                    firstDate = activityDate;
                }
            });
            
            // Find earliest accommodation
            accommodations.forEach(accommodation => {
                const checkIn = new Date(accommodation.check_in_date);
                if (!firstDate || checkIn < firstDate) {
                    firstDate = checkIn;
                }
            });
            
            console.log('First event date found:', firstDate);
            
            if (firstDate) {
                this.weekStart = this.getWeekStart(firstDate);
            } else {
                this.weekStart = this.getWeekStart(new Date());
            }
            
            console.log('Calling load()...');
            this.load();
        } catch (error) {
            console.error('Error in loadFirstEvent:', error);
            this.weekStart = this.getWeekStart(new Date());
            this.load();
        }
    },
    
    goToday() {
        this.weekStart = this.getWeekStart(new Date());
        this.load();
    },
    
    goTomorrow() {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        this.weekStart = this.getWeekStart(tomorrow);
        this.load();
    },
    
    prevWeek() {
        this.weekStart.setDate(this.weekStart.getDate() - 7);
        this.load();
    },
    
    nextWeek() {
        this.weekStart.setDate(this.weekStart.getDate() + 7);
        this.load();
    },
    
    // Load calendar data and render
    async load() {
        console.log('Calendar.load() called');
        const container = document.getElementById('calendarWeekView');
        
        if (!container) {
            console.error('Calendar container not found!');
            return;
        }
        
        try {
            // Fetch data
            const [activitiesRes, accommodationsRes] = await Promise.all([
                fetch(`/api/trips/${this.tripId}/activities`),
                fetch(`/api/trips/${this.tripId}/accommodations`)
            ]);
            
            const activities = await activitiesRes.json();
            const accommodations = await accommodationsRes.json();
            
            // Build events object
            this.events = {};
            
            const weekEnd = new Date(this.weekStart);
            weekEnd.setDate(this.weekStart.getDate() + 7);
            
            // Initialize days
            for (let d = new Date(this.weekStart); d < weekEnd; d.setDate(d.getDate() + 1)) {
                const dateStr = d.toISOString().split('T')[0];
                this.events[dateStr] = [];
            }
            
            // Add activities
            activities.forEach(activity => {
                const startDate = new Date(activity.start_datetime || activity.start_date);
                const dateStr = startDate.toISOString().split('T')[0];
                
                if (this.events[dateStr]) {
                    let startTime = '09:00', endTime = '10:00';
                    
                    if (activity.start_datetime) {
                        const start = new Date(activity.start_datetime);
                        startTime = `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')}`;
                        
                        if (activity.end_datetime) {
                            const end = new Date(activity.end_datetime);
                            endTime = `${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`;
                        }
                    }
                    
                    this.events[dateStr].push({
                        id: activity.id,
                        type: 'activity',
                        category: activity.category,
                        title: activity.name,
                        startTime,
                        endTime,
                        location: activity.location_name || ''
                    });
                }
            });
            
            // Add accommodations
            accommodations.forEach(accommodation => {
                const checkIn = new Date(accommodation.check_in_date);
                const checkOut = new Date(accommodation.check_out_date);
                
                if (!checkIn || !checkOut) return;
                
                const checkInStr = checkIn.toISOString().split('T')[0];
                const checkOutStr = checkOut.toISOString().split('T')[0];
                
                for (let dateStr in this.events) {
                    if (dateStr >= checkInStr && dateStr <= checkOutStr) {
                        let startTime = dateStr === checkInStr ? (accommodation.check_in_time || '15:00') : '00:00';
                        let endTime = dateStr === checkOutStr ? (accommodation.check_out_time || '11:00') : '23:59';
                        
                        this.events[dateStr].push({
                            id: accommodation.id,
                            type: 'accommodation',
                            category: 'accommodation',
                            title: accommodation.name,
                            startTime,
                            endTime,
                            location: accommodation.address || accommodation.city || ''
                        });
                    }
                }
            });
            
            this.render();
            this.updateHeader();
            
        } catch (error) {
            console.error('Error loading calendar:', error);
            container.innerHTML = `<div class="alert alert-danger m-3"><i class="fas fa-exclamation-triangle"></i> Failed to load calendar: ${error.message}</div>`;
        }
    },
    
    // Update week header
    updateHeader() {
        const weekEnd = new Date(this.weekStart);
        weekEnd.setDate(this.weekStart.getDate() + 6);
        
        const options = { month: 'long', day: 'numeric', year: 'numeric' };
        const rangeText = `${this.weekStart.toLocaleDateString(undefined, options)} - ${weekEnd.toLocaleDateString(undefined, options)}`;
        
        document.getElementById('calendarWeekRange').textContent = rangeText;
    },
    
    // Render week view
    render() {
        console.log('Calendar.render() called');
        const container = document.getElementById('calendarWeekView');
        
        if (!container) {
            console.error('Calendar container not found in render()!');
            return;
        }
        
        let html = '<div class="calendar-week-grid">';
        
        // Time gutter (left sidebar)
        html += '<div class="calendar-time-gutter">';
        html += '<div class="calendar-day-header"></div>';
        
        for (let hour = 0; hour < 24; hour++) {
            const time = hour < 12 ? (hour || 12) + ' AM' : (hour === 12 ? '12' : hour - 12) + ' PM';
            html += `<div class="calendar-time-slot hour-mark">${hour > 0 ? time : ''}</div>`;
        }
        html += '</div>';
        
        // Days container
        html += '<div class="calendar-days-container">';
        
        const today = new Date().toISOString().split('T')[0];
        const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        // 7 day columns starting from Monday
        for (let i = 0; i < 7; i++) {
            const dayDate = new Date(this.weekStart);
            dayDate.setDate(this.weekStart.getDate() + i);
            const dateStr = dayDate.toISOString().split('T')[0];
            const dayOfWeek = dayDate.getDay();
            
            if (i === 0) {
                console.log('First day of week:', dayDate.toDateString(), 'getDay():', dayOfWeek, 'Should be Monday (1)');
            }
            
            const isToday = dateStr === today;
            const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
            
            html += `<div class="calendar-day-column ${isToday ? 'today' : ''} ${isWeekend ? 'weekend' : ''}" data-date="${dateStr}">`;
            html += `<div class="calendar-day-header">`;
            html += `<div class="calendar-day-name">${dayNames[dayOfWeek]}</div>`;
            html += `<div class="calendar-day-number">${dayDate.getDate()}</div>`;
            html += '</div>';
            html += `<div class="calendar-events-area" data-date="${dateStr}"></div>`;
            html += '</div>';
        }
        
        html += '</div></div>';
        
        container.innerHTML = html;
        
        // Add events to each day
        for (let dateStr in this.events) {
            const eventsArea = container.querySelector(`.calendar-events-area[data-date="${dateStr}"]`);
            if (eventsArea && this.events[dateStr].length > 0) {
                this.renderDayEvents(eventsArea, this.events[dateStr], dateStr);
            }
        }
        
        this.addCurrentTimeLine();
        this.setupDragAndDrop();
        
        // Initialize tooltips
        setTimeout(() => {
            const tooltips = container.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltips.forEach(tooltip => {
                try {
                    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                        new bootstrap.Tooltip(tooltip);
                    }
                } catch (e) {
                    console.warn('Could not initialize tooltip:', e);
                }
            });
        }, 100);
    },
    
    // Render events in a day
    renderDayEvents(eventsArea, events, dateStr) {
        events.forEach(event => {
            const eventEl = this.createEventElement(event, dateStr);
            eventsArea.appendChild(eventEl);
        });
    },
    
    // Create event DOM element
    createEventElement(event, dateStr) {
        const eventEl = document.createElement('div');
        eventEl.className = `calendar-event ${event.type === 'activity' ? 'activity-' + event.category : event.category}`;
        eventEl.draggable = true;
        eventEl.dataset.eventId = event.id;
        eventEl.dataset.eventType = event.type;
        eventEl.dataset.eventDate = dateStr;
        
        // Calculate position and height
        const startMinutes = this.timeToMinutes(event.startTime);
        const endMinutes = this.timeToMinutes(event.endTime);
        const duration = endMinutes - startMinutes;
        
        const topPx = (startMinutes / 60) * 60;
        const heightPx = Math.max((duration / 60) * 60, 25);
        
        // ONLY set positioning via inline styles
        eventEl.style.top = topPx + 'px';
        eventEl.style.height = heightPx + 'px';
        
        // Content
        eventEl.innerHTML = `<strong>${event.title}</strong><div style="font-size: 0.65rem;">${event.startTime}</div>`;
        eventEl.title = `${event.title} (${event.startTime} - ${event.endTime})${event.location ? '\n' + event.location : ''}`;
        
        // Event handlers
        eventEl.addEventListener('dragstart', (e) => this.handleEventDragStart(e));
        eventEl.addEventListener('dragend', (e) => this.handleEventDragEnd(e));
        eventEl.addEventListener('click', (e) => {
            if (event.type === 'activity') {
                window.editActivity(event.id);
            } else {
                window.editAccommodation(event.id);
            }
        });
        
        return eventEl;
    },
    
    // Utility functions
    timeToMinutes(timeStr) {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    },
    
    minutesToTime(minutes) {
        minutes = Math.max(0, Math.min(minutes, 1439));
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    },
    
    // Drag and drop handlers
    handleEventDragStart(e) {
        this.draggedEvent = e.target;
        this.dragStartY = e.clientY;
        
        setTimeout(() => {
            e.target.classList.add('dragging');
        }, 0);
        
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.innerHTML);
    },
    
    handleEventDragEnd(e) {
        e.target.classList.remove('dragging');
        if (this.currentDropZone) {
            this.currentDropZone.classList.remove('active');
        }
        this.draggedEvent = null;
    },
    
    setupDragAndDrop() {
        // Implement drag and drop logic here
        console.log('setupDragAndDrop() called');
    },
    
    addCurrentTimeLine() {
        const now = new Date();
        const todayStr = now.toISOString().split('T')[0];
        const eventsArea = document.querySelector(`.calendar-events-area[data-date="${todayStr}"]`);
        
        if (eventsArea) {
            const minutes = now.getHours() * 60 + now.getMinutes();
            const topPx = (minutes / 60) * 60;
            
            const line = document.createElement('div');
            line.className = 'calendar-current-time-line';
            line.style.top = topPx + 'px';
            eventsArea.appendChild(line);
        }
    }
};

// Export for global access
window.Calendar = Calendar;

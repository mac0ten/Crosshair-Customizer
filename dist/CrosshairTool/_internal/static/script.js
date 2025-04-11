// Helper functions to safely set control values
function setInputValue(id, value, isNumber = false) {
    const element = document.getElementById(id);
    if (element && value !== null && value !== undefined) {
        element.value = isNumber ? Number(value) : value;
    }
}

function setCheckboxValue(id, value) {
    const element = document.getElementById(id);
    if (element && typeof value === 'boolean') {
        element.checked = value;
    }
}

function setColorValue(id, value) {
    const element = document.getElementById(id);
    if (element && typeof value === 'string') {
        element.value = value;
    }
}

function setRangeValue(id, value) {
    setInputValue(id, value, true); // Range inputs often treated as numbers
    
    // Update the displayed value in the corresponding span
    const valueDisplayId = `${id}Value`;
    const valueDisplay = document.getElementById(valueDisplayId);
    if (valueDisplay) {
        valueDisplay.textContent = value;
    }
}

function setPreviewImage(settings) {
    const fileNameSpan = document.getElementById('currentFileName');
    const previewImg = document.getElementById('imagePreview');
    let filePath = null;
    let type = settings.type;

    if (type === 'static' && settings.static?.image_path) {
        filePath = settings.static.image_path;
    } else if (type === 'animated' && settings.animated?.gif_path) {
        filePath = settings.animated.gif_path;
    }

    if (filePath) {
        fileNameSpan.textContent = filePath;
        // Construct URL relative to Flask's user_uploads route
        previewImg.src = `/user_uploads/${encodeURIComponent(filePath)}`;
        previewImg.style.display = 'block';
    } else {
        fileNameSpan.textContent = 'None';
        previewImg.src = '';
        previewImg.style.display = 'none';
    }
}

// Helper functions to safely get/set control values
function getInputValue(id, isNumber = false, defaultValue = null) {
    const element = document.getElementById(id);
    if (element) {
        const value = element.value;
        if (isNumber) {
            const num = Number(value);
            return isNaN(num) ? defaultValue : num;
        }
        return value;
    } 
    return defaultValue;
}

function getCheckboxValue(id, defaultValue = false) {
    const element = document.getElementById(id);
    return element ? element.checked : defaultValue;
}

function getColorValue(id, defaultValue = '#000000') {
    const element = document.getElementById(id);
    // Basic validation for hex color format
    return element && /^#[0-9A-F]{6}$/i.test(element.value) ? element.value : defaultValue;
}

function getRangeValue(id, defaultValue = 0) {
     return getInputValue(id, true, defaultValue);
}

// --- Theme management functions ---
function setTheme(isDark) {
    const htmlElement = document.documentElement;
    if (isDark) {
        htmlElement.setAttribute('data-theme', 'dark');
    } else {
        htmlElement.setAttribute('data-theme', 'light');
    }
    // Save preference
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function loadThemePreference() {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set theme based on saved preference or system preference
    const isDark = savedTheme ? savedTheme === 'dark' : prefersDark;
    setTheme(isDark);
    
    // Update toggle state
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.checked = isDark;
    }
}

// --- Global state variable to hold the last known settings --- 
let currentAppSettings = {};

document.addEventListener('DOMContentLoaded', () => {
    // --- Element References ---
    const crosshairTypeSelect = document.getElementById('crosshairType');
    const parametricControls = document.getElementById('parametricControls');
    const imageControls = document.getElementById('imageControls');
    const gifSpeedControl = document.getElementById('gifSpeedControl');
    const gifPresetControl = document.getElementById('gifPresetControl');
    const gifPresetGrid = document.getElementById('gifPresetGrid');
    const imageUploadInput = document.getElementById('imageUpload'); 
    const profileNameInput = document.getElementById('profileName');
    const saveProfileBtn = document.getElementById('saveProfileBtn');
    const profileListSelect = document.getElementById('profileList');
    const loadProfileBtn = document.getElementById('loadProfileBtn');
    const deleteProfileBtn = document.getElementById('deleteProfileBtn');
    const statusMessagesDiv = document.getElementById('statusMessages'); // Get status div
    const themeToggle = document.getElementById('themeToggle'); // Get theme toggle
    const allCards = document.querySelectorAll('.card'); // Get all cards for mobile accordion
    const mobileQuickNav = document.getElementById('mobileQuickNav'); // Mobile quick nav button
    const allNumberInputs = document.querySelectorAll('input[type="number"]'); // Number inputs for stepper
    const presetPaginationDiv = document.getElementById('presetPagination'); // New element for pagination
    const presetPageInfo = document.getElementById('presetPageInfo'); // New element for page info
    const presetPrevBtn = document.getElementById('presetPrevBtn'); // New button
    const presetNextBtn = document.getElementById('presetNextBtn'); // New button
    let selectedPresetCard = null;
    let currentPresetPage = 1;
    let totalPresetPages = 1;
    const presetsPerPage = 24; // Match server default or set desired value

    // Load and apply theme preference
    loadThemePreference();
    
    // Convert number inputs to stepper controls for better mobile UX
    function setupNumberSteppers() {
        allNumberInputs.forEach(input => {
            // Skip if already inside a stepper
            if (input.parentElement.classList.contains('number-input-stepper')) {
                return;
            }
            
            // Create stepper wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'number-input-stepper';
            
            // Create minus button
            const minusBtn = document.createElement('button');
            minusBtn.className = 'stepper-btn';
            minusBtn.type = 'button';
            minusBtn.textContent = '-';
            minusBtn.setAttribute('aria-label', 'Decrease value');
            
            // Create plus button
            const plusBtn = document.createElement('button');
            plusBtn.className = 'stepper-btn';
            plusBtn.type = 'button';
            plusBtn.textContent = '+';
            plusBtn.setAttribute('aria-label', 'Increase value');
            
            // Get the parent element and attributes for the input
            const parent = input.parentElement;
            const min = parseFloat(input.getAttribute('min') || 0);
            const max = parseFloat(input.getAttribute('max') || Infinity);
            const step = parseFloat(input.getAttribute('step') || 1);
            
            // Event listeners for buttons
            minusBtn.addEventListener('click', () => {
                let value = parseFloat(input.value || 0);
                value = Math.max(min, value - step);
                input.value = value;
                
                // Trigger change event for the input
                const event = new Event('input', { bubbles: true });
                input.dispatchEvent(event);
            });
            
            plusBtn.addEventListener('click', () => {
                let value = parseFloat(input.value || 0);
                value = Math.min(max, value + step);
                input.value = value;
                
                // Trigger change event for the input
                const event = new Event('input', { bubbles: true });
                input.dispatchEvent(event);
            });
            
            // Replace the input with our stepper
            parent.replaceChild(wrapper, input);
            wrapper.appendChild(minusBtn);
            wrapper.appendChild(input);
            wrapper.appendChild(plusBtn);
        });
    }
    
    // Initialize number steppers for better mobile UX
    setupNumberSteppers();
    
    let isCurrentlyMobile = window.innerWidth <= 768;

    // Set up mobile accordion functionality
    function setupMobileAccordion() {
        const wasMobile = isCurrentlyMobile; // Store previous state
        isCurrentlyMobile = window.innerWidth <= 768; // Update current state

        // Toggle mobile quick nav visibility
        if (mobileQuickNav) {
            mobileQuickNav.style.display = isCurrentlyMobile ? 'flex' : 'none';
        }

        allCards.forEach(card => {
            const cardHeader = card.querySelector('.card-header');
            if (!cardHeader) return;

            // Remove previous listener - simple approach
            const newCardHeader = cardHeader.cloneNode(true);
            cardHeader.parentNode.replaceChild(newCardHeader, cardHeader);
            const currentCardHeader = card.querySelector('.card-header'); // Re-select after replacing

            if (isCurrentlyMobile) {
                card.classList.add('mobile-accordion');
                
                // Apply initial collapse state ONLY when switching from desktop to mobile
                if (!wasMobile) { 
                    if (card.id !== 'crosshairTypeCard') {
                        card.classList.add('collapsed');
                    }
                } // Otherwise, respect the current collapsed/expanded state
                
                // Add click listener for mobile toggling
                currentCardHeader.addEventListener('click', () => {
                    card.classList.toggle('collapsed');
                });

            } else {
                // Desktop view: remove mobile classes and ensure expanded
                card.classList.remove('mobile-accordion', 'collapsed');
                // Listener is removed by the cloneNode/replaceChild or never added
            }
        });
    }
    
    // Function to setup quick navigation modal for mobile
    function setupQuickNavigation() {
        if (!mobileQuickNav) return;
        
        // Create modal for quick navigation
        const navModal = document.createElement('div');
        navModal.className = 'quick-nav-modal';
        navModal.style.display = 'none';
        document.body.appendChild(navModal);
        
        // Add menu items to modal
        navModal.innerHTML = `
            <div class="quick-nav-content">
                <button class="quick-nav-item" data-target="crosshairTypeCard">Crosshair Type</button>
                <button class="quick-nav-item" data-target="parametricControls">Parametric Settings</button>
                <button class="quick-nav-item" data-target="imageControls">Image/GIF Settings</button>
                <button class="quick-nav-item" data-target="profileCard">Profiles</button>
                <button class="quick-nav-close">Close</button>
            </div>
        `;
        
        // Add CSS for the modal
        const style = document.createElement('style');
        style.textContent = `
            .quick-nav-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                z-index: 1000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .quick-nav-content {
                background-color: var(--card-bg);
                border-radius: var(--radius);
                width: 80%;
                max-width: 300px;
                padding: 1rem;
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            .quick-nav-item, .quick-nav-close {
                padding: 0.75rem;
                border: none;
                border-radius: var(--radius-sm);
                background-color: var(--gray-100);
                color: var(--text-color);
                font-size: 0.875rem;
                text-align: left;
                cursor: pointer;
                transition: background-color 0.2s ease;
            }
            .quick-nav-item:hover, .quick-nav-close:hover {
                background-color: var(--gray-200);
            }
            .quick-nav-close {
                margin-top: 0.5rem;
                background-color: var(--gray-300);
                text-align: center;
            }
        `;
        document.head.appendChild(style);
        
        // Toggle modal on button click
        mobileQuickNav.addEventListener('click', () => {
            navModal.style.display = 'flex';
        });
        
        // Close modal on close button click
        const closeBtn = navModal.querySelector('.quick-nav-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                navModal.style.display = 'none';
            });
        }
        
        // Close modal on backdrop click
        navModal.addEventListener('click', (e) => {
            if (e.target === navModal) {
                navModal.style.display = 'none';
            }
        });
        
        // Navigation item clicks
        const navItems = navModal.querySelectorAll('.quick-nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const targetId = item.getAttribute('data-target');
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    // Scroll to the element
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                    
                    // Expand the card if it's collapsed
                    if (targetElement.classList.contains('collapsed')) {
                        targetElement.classList.remove('collapsed');
                    }
                }
                
                // Close the modal
                navModal.style.display = 'none';
            });
        });
    }
    
    // Initialize mobile accordion and set up DEBOUNCED resize listener
    setupMobileAccordion();
    setupQuickNavigation();
    window.addEventListener('resize', debounce(setupMobileAccordion, 250)); // Debounce resize
    
    // Set up theme toggle
    themeToggle.addEventListener('change', () => {
        setTheme(themeToggle.checked);
    });

    // Get all relevant range inputs for setting up live value display
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    
    // Set up range input value displays
    rangeInputs.forEach(rangeInput => {
        const valueDisplayId = `${rangeInput.id}Value`;
        const valueDisplay = document.getElementById(valueDisplayId);
        const valueTextDisplay = document.querySelector(`[id="${valueDisplayId}"].range-value-text`);
        
        // Initialize with current value
        if (valueDisplay) {
            valueDisplay.textContent = rangeInput.value;
        }
        if (valueTextDisplay) {
            valueTextDisplay.textContent = rangeInput.value;
        }
        
        // Update value display when range changes
        rangeInput.addEventListener('input', () => {
            if (valueDisplay) {
                valueDisplay.textContent = rangeInput.value;
            }
            if (valueTextDisplay) {
                valueTextDisplay.textContent = rangeInput.value;
            }
        });
    });

    // Get all relevant input controls for adding listeners later (excluding profile buttons/select)
    const allControls = document.querySelectorAll(
        '#crosshairType, #parametricControls input, #parametricControls select, #imageControls input:not(#imageUpload), #imageControls select'
    );

    // --- UI Helper Functions --- 
    let statusClearTimer;
    function showStatusMessage(message, type = 'info', duration = 3000) {
        if (!statusMessagesDiv) return;
        // Clear previous timer if any
        clearTimeout(statusClearTimer);
        // Set text and classes
        statusMessagesDiv.textContent = message;
        statusMessagesDiv.className = 'status-area'; // Reset classes
        
        // Add the visible class for transition effect
        statusMessagesDiv.classList.add('visible');
        
        if (type === 'success') {
            statusMessagesDiv.classList.add('status-success');
        } else if (type === 'error') {
            statusMessagesDiv.classList.add('status-error');
        } else { // default to info
            statusMessagesDiv.classList.add('status-info');
        }
        // Auto-clear message after duration
        if (duration > 0) {
            statusClearTimer = setTimeout(() => {
                statusMessagesDiv.classList.remove('visible');
                // After fade out, reset the content
                setTimeout(() => {
                    statusMessagesDiv.textContent = '';
                    statusMessagesDiv.className = 'status-area';
                }, 300); // Match the CSS transition time
            }, duration);
        }
    }

    function toggleControls() {
        const selectedType = crosshairTypeSelect.value;
        parametricControls.classList.remove('visible');
        imageControls.classList.remove('visible');
        gifSpeedControl.style.display = 'none';
        gifPresetControl.style.display = 'none';

        if (selectedType === 'parametric') {
            parametricControls.classList.add('visible');
            // Auto-expand the parametric card on mobile
            if (window.innerWidth <= 768) {
                parametricControls.classList.remove('collapsed');
                imageControls.classList.add('collapsed');
            }
        } else if (selectedType === 'static') {
            imageControls.classList.add('visible');
            // Auto-expand the image card on mobile
            if (window.innerWidth <= 768) {
                imageControls.classList.remove('collapsed');
                parametricControls.classList.add('collapsed');
            }
        } else if (selectedType === 'animated') {
            imageControls.classList.add('visible');
            gifSpeedControl.style.display = 'block';
            gifPresetControl.style.display = 'block';
            // Auto-expand the image card on mobile
            if (window.innerWidth <= 768) {
                imageControls.classList.remove('collapsed');
                parametricControls.classList.add('collapsed');
            }
        }
        
        // Reset number steppers for newly visible controls
        setTimeout(() => {
            setupNumberSteppers();
        }, 100);
    }

    // Function to populate all controls from settings object
    function populateControls(settings) {
        if (!settings) return;

        setInputValue('crosshairType', settings.type);

        // Parametric
        if (settings.parametric) {
            const p = settings.parametric;
            setCheckboxValue('centerDotEnabled', p.center_dot_enabled);
            setColorValue('centerDotColor', p.center_dot_color);
            setInputValue('centerDotSize', p.center_dot_size, true);
            setRangeValue('centerDotOpacity', p.center_dot_opacity);

            setCheckboxValue('innerLinesEnabled', p.inner_lines_enabled);
            setColorValue('innerLinesColor', p.inner_lines_color);
            setInputValue('innerLinesThickness', p.inner_lines_thickness, true);
            setInputValue('innerLinesLength', p.inner_lines_length, true);
            setInputValue('innerLinesGap', p.inner_lines_gap, true);
            setRangeValue('innerLinesOpacity', p.inner_lines_opacity);
            
            // TODO: Add outer lines population if controls are added
            // setCheckboxValue('outerLinesEnabled', p.outer_lines_enabled);
            // ... 

            setCheckboxValue('outlineEnabled', p.outline_enabled);
            setColorValue('outlineColor', p.outline_color);
            setInputValue('outlineThickness', p.outline_thickness, true);
            setRangeValue('outlineOpacity', p.outline_opacity);
            
            setCheckboxValue('tShape', p.t_shape);
        }

        // Static / Animated common controls
        if (settings.static) {
            setRangeValue('imageOpacity', settings.static.opacity);
            setInputValue('imageScale', settings.static.scale, true);
        }
         // Use animated settings if type is animated, otherwise fallback to static for common fields
        const imageSettings = settings.type === 'animated' ? settings.animated : settings.static;
        if (imageSettings) {
            setRangeValue('imageOpacity', imageSettings.opacity);
            setInputValue('imageScale', imageSettings.scale, true);
        }

        // Animated specific
        if (settings.animated) {
            setInputValue('gifSpeed', settings.animated.speed, true);
        }
        
        // Set image preview
        setPreviewImage(settings);

        // Update visibility based on the populated type
        toggleControls();
    }

    // Function to gather current settings from the UI
    function getCurrentSettingsFromUI() {
        const settings = {
            type: getInputValue('crosshairType'),
            parametric: {
                center_dot_enabled: getCheckboxValue('centerDotEnabled'),
                center_dot_color: getColorValue('centerDotColor', '#FF0000'),
                center_dot_size: getInputValue('centerDotSize', true, 3),
                center_dot_opacity: getRangeValue('centerDotOpacity', 200),
                
                inner_lines_enabled: getCheckboxValue('innerLinesEnabled'),
                inner_lines_color: getColorValue('innerLinesColor', '#FFFFFF'),
                inner_lines_thickness: getInputValue('innerLinesThickness', true, 1),
                inner_lines_length: getInputValue('innerLinesLength', true, 5),
                inner_lines_gap: getInputValue('innerLinesGap', true, 3),
                inner_lines_opacity: getRangeValue('innerLinesOpacity', 255),

                // TODO: Add outer lines getters if controls added
                outer_lines_enabled: currentAppSettings.parametric?.outer_lines_enabled ?? false, // Preserve previous state
                outer_lines_color: currentAppSettings.parametric?.outer_lines_color ?? '#00FF00',
                outer_lines_thickness: currentAppSettings.parametric?.outer_lines_thickness ?? 1,
                outer_lines_length: currentAppSettings.parametric?.outer_lines_length ?? 2,
                outer_lines_gap: currentAppSettings.parametric?.outer_lines_gap ?? 8,
                outer_lines_opacity: currentAppSettings.parametric?.outer_lines_opacity ?? 180,

                outline_enabled: getCheckboxValue('outlineEnabled'),
                outline_color: getColorValue('outlineColor', '#000000'),
                outline_thickness: getInputValue('outlineThickness', true, 1),
                outline_opacity: getRangeValue('outlineOpacity', 150),
                
                t_shape: getCheckboxValue('tShape')
            },
            static: {
                // Preserve image path from current state unless explicitly changed by upload (Phase 4)
                image_path: currentAppSettings.static?.image_path ?? null,
                opacity: getRangeValue('imageOpacity', 255),
                scale: getInputValue('imageScale', true, 1.0)
            },
            animated: {
                 // Preserve gif path from current state unless explicitly changed by upload (Phase 4)
                gif_path: currentAppSettings.animated?.gif_path ?? null,
                opacity: getRangeValue('imageOpacity', 255),
                scale: getInputValue('imageScale', true, 1.0),
                speed: getInputValue('gifSpeed', true, 100)
            }
        };

        // Adjust opacity/scale based on current type selected
         const currentType = settings.type;
         const opacity = getRangeValue('imageOpacity', 255);
         const scale = getInputValue('imageScale', true, 1.0);
         if (currentType === 'static') {
             settings.static.opacity = opacity;
             settings.static.scale = scale;
         } else if (currentType === 'animated') {
             settings.animated.opacity = opacity;
             settings.animated.scale = scale;
         }

        return settings;
    }

    // Debounce function to limit how often a function is called
    function debounce(func, delay) {
        let timeoutId;
        return function(...args) {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    }

    // Function to send update to the server
    async function sendUpdate() {
        const newSettings = getCurrentSettingsFromUI();
        console.log("Sending settings:", JSON.stringify(newSettings)); 
        
        // Show subtle loading indicator or status change
        const activeCard = document.querySelector(`#${newSettings.type}Controls`);
        if (activeCard) {
            activeCard.style.opacity = '0.8';
        }
        
        try {
            const response = await fetch('/update_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newSettings),
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status} - ${errorData.details || errorData.error || 'Unknown error'}`);
            }
            const result = await response.json();
            console.log("Update result:", result);
            currentAppSettings = newSettings; 
            setPreviewImage(newSettings); 
            showStatusMessage("Settings updated", "success", 1500); // Show brief success feedback
        } catch (error) {
            console.error("Error sending settings update:", error);
            showStatusMessage(`Failed to update settings: ${error.message}`, "error"); 
        } finally {
            // Restore opacity
            if (activeCard) {
                activeCard.style.opacity = '1';
            }
        }
    }
    const debouncedSendUpdate = debounce(sendUpdate, 300);

    // Fetch initial settings and populate controls
    async function fetchAndApplySettings() {
        try {
            showStatusMessage("Loading settings...", "info", 0);
            const response = await fetch('/get_settings');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const settings = await response.json();
            console.log("Fetched settings:", settings);
            currentAppSettings = settings; 
            populateControls(currentAppSettings);
            // Re-initialize number steppers after populating controls
            setTimeout(() => {
                setupNumberSteppers();
            }, 100);
            showStatusMessage("Settings loaded successfully", "success", 1500);
        } catch (error) {
            console.error("Error fetching initial settings:", error);
            showStatusMessage(`Failed to load current settings: ${error.message}`, "error");
            toggleControls();
        }
    }

    // --- Image Upload Handler ---
    async function handleImageUpload(event) {
        const file = event.target.files[0];
        if (!file) {
            return; // No file selected
        }

        const formData = new FormData();
        formData.append('file', file);

        console.log(`Uploading file: ${file.name}`);
        showStatusMessage(`Uploading ${file.name}...`, "info", 0); // Show persistent info message

        try {
            // Add visual feedback for upload in progress
            const uploadLabel = document.querySelector('.file-input-label');
            if (uploadLabel) {
                uploadLabel.classList.add('btn-secondary');
                uploadLabel.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> Uploading...';
            }
            
            // Disable input during upload
            imageUploadInput.disabled = true; 
            
            const response = await fetch('/upload_image', {
                method: 'POST',
                body: formData,
                // Let browser set Content-Type for FormData
            });

            const result = await response.json(); // Always expect JSON back

            if (!response.ok) {
                 throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            console.log("Upload successful:", result);
            // Update global state and UI with the new settings returned from server
            currentAppSettings = result.new_settings;
            populateControls(currentAppSettings);
            showStatusMessage(`${file.name} uploaded successfully!`, "success", 3000);

        } catch (error) {
            console.error("Error uploading file:", error);
            showStatusMessage(`File upload failed: ${error.message}`, "error", 5000);
            // Clear the file input potentially
            imageUploadInput.value = ''; 
        } finally {
            // Restore the upload button
            const uploadLabel = document.querySelector('.file-input-label');
            if (uploadLabel) {
                uploadLabel.classList.remove('btn-secondary');
                uploadLabel.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg> Upload Image/GIF';
            }
             // Re-enable input
             imageUploadInput.disabled = false;
        }
    }

    // --- Profile Management Functions ---

    // Function to fetch profiles and populate the dropdown
    async function fetchAndPopulateProfiles() {
        try {
            showStatusMessage("Loading profiles...", "info", 1500);
            const response = await fetch('/list_profiles');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.success && Array.isArray(data.profiles)) {
                profileListSelect.innerHTML = ''; // Clear existing options
                if (data.profiles.length === 0) {
                     const option = document.createElement('option');
                     option.textContent = "No profiles saved";
                     option.disabled = true;
                     profileListSelect.appendChild(option);
                     
                     // Disable buttons if no profiles
                     loadProfileBtn.disabled = true;
                     deleteProfileBtn.disabled = true;
                } else {
                    // Enable buttons if profiles exist
                    loadProfileBtn.disabled = false;
                    deleteProfileBtn.disabled = false;
                    
                    data.profiles.forEach(profileName => {
                        const option = document.createElement('option');
                        option.value = profileName;
                        option.textContent = profileName;
                        profileListSelect.appendChild(option);
                    });
                }
            } else {
                console.error("Failed to parse profile list:", data.error || "Unknown error");
            }
        } catch (error) {
            console.error("Error fetching profile list:", error);
            profileListSelect.innerHTML = '<option disabled>Error loading profiles</option>';
            showStatusMessage(`Failed to load profiles: ${error.message}`, "error", 3000);
        }
    }

    // Function to handle saving a profile
    async function handleSaveProfile() {
        const profileName = profileNameInput.value.trim();
        if (!profileName) {
            showStatusMessage("Please enter a profile name", "error", 3000);
            return;
        }

        console.log(`Saving profile: ${profileName}`);
        saveProfileBtn.disabled = true;
        
        // Visual feedback
        const btnText = saveProfileBtn.innerHTML;
        saveProfileBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> Saving...';
        
        showStatusMessage(`Saving profile "${profileName}"...`, "info", 0);

        try {
            // Get current settings from UI
            const currentSettings = getCurrentSettingsFromUI();
            
            // Send both profile name and settings to server
            const response = await fetch('/save_profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    profile_name: profileName,
                    settings: currentSettings
                }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            showStatusMessage(result.message || "Profile saved successfully!", "success", 3000);
            profileNameInput.value = ''; // Clear input field
            fetchAndPopulateProfiles(); // Refresh the list

        } catch (error) {
            console.error("Error saving profile:", error);
            showStatusMessage(`Failed to save profile: ${error.message}`, "error", 5000);
        } finally {
             saveProfileBtn.disabled = false;
             saveProfileBtn.innerHTML = btnText;
        }
    }

    // Function to handle loading a profile
    async function handleLoadProfile() {
        const selectedProfile = profileListSelect.value;
        if (!selectedProfile || profileListSelect.options[profileListSelect.selectedIndex]?.disabled) {
            showStatusMessage("Please select a profile to load", "error", 3000);
            return;
        }

        console.log(`Loading profile: ${selectedProfile}`);
        loadProfileBtn.disabled = true;
        
        // Visual feedback
        const btnText = loadProfileBtn.innerHTML;
        loadProfileBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> Loading...';
        
        showStatusMessage(`Loading profile "${selectedProfile}"...`, "info", 0);

        try {
            // Use the proper URL format with profile name in the path
            const response = await fetch(`/load_profile/${encodeURIComponent(selectedProfile)}`);
            
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            // The server should return the settings object directly
            if (result) {
                currentAppSettings = result; // Update global state
                populateControls(currentAppSettings); // Update UI controls
                
                // Re-initialize number steppers after loading profile
                setTimeout(() => {
                    setupNumberSteppers();
                }, 100);
                
                showStatusMessage("Profile loaded successfully!", "success", 3000);
            } else {
                 throw new Error(result.error || "Failed to load settings from profile.");
            }

        } catch (error) {
            console.error("Error loading profile:", error);
            showStatusMessage(`Failed to load profile: ${error.message}`, "error", 5000);
        } finally {
             loadProfileBtn.disabled = false;
             loadProfileBtn.innerHTML = btnText;
        }
    }

    // Function to handle deleting a profile
    async function handleDeleteProfile() {
        const selectedProfile = profileListSelect.value;
        if (!selectedProfile || profileListSelect.options[profileListSelect.selectedIndex]?.disabled) {
            showStatusMessage("Please select a profile to delete", "error", 3000);
            return;
        }

        if (!confirm(`Are you sure you want to delete the profile "${selectedProfile}"?`)) {
            return;
        }

        console.log(`Deleting profile: ${selectedProfile}`);
        deleteProfileBtn.disabled = true;
        
        // Visual feedback
        const btnText = deleteProfileBtn.innerHTML;
        deleteProfileBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> Deleting...';
        
        showStatusMessage(`Deleting profile "${selectedProfile}"...`, "info", 0);
        
        try {
             // Use the proper URL format and DELETE method
             const response = await fetch(`/delete_profile/${encodeURIComponent(selectedProfile)}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            showStatusMessage(result.message || "Profile deleted successfully!", "success", 3000);
            fetchAndPopulateProfiles(); // Refresh the list

        } catch (error) {
            console.error("Error deleting profile:", error);
            showStatusMessage(`Failed to delete profile: ${error.message}`, "error", 5000);
        } finally {
             deleteProfileBtn.disabled = false;
             deleteProfileBtn.innerHTML = btnText;
        }
    }

    // --- Preset Loading and Pagination ---
    async function fetchGifPresets(page = 1) {
        console.log(`Fetching presets page: ${page}`);
        try {
            const response = await fetch(`/list_gif_presets?page=${page}&per_page=${presetsPerPage}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            if (data.success) {
                populatePresetGrid(data.presets);
                currentPresetPage = data.page;
                totalPresetPages = Math.ceil(data.total_presets / data.per_page);
                updatePaginationControls(data.total_presets);
            } else {
                console.error("Error fetching presets:", data.error);
                gifPresetGrid.innerHTML = '<p class="preset-empty">Could not load presets.</p>';
                updatePaginationControls(0);
            }
        } catch (error) {
            console.error('Error fetching presets:', error);
            gifPresetGrid.innerHTML = '<p class="preset-empty">Could not load presets.</p>';
            updatePaginationControls(0);
        }
    }
    
    function populatePresetGrid(presets) {
        gifPresetGrid.innerHTML = ''; // Clear previous presets
        if (!presets || presets.length === 0) {
            gifPresetGrid.innerHTML = '<p class="preset-empty">No presets found.</p>';
            return;
        }

        presets.forEach(preset => {
            const card = document.createElement('div');
            card.className = 'preset-card';
            card.dataset.filename = preset.filename;
            
            const img = document.createElement('img');
            // Use get_preset route for thumbnail/image source
            img.src = `/get_preset/${encodeURIComponent(preset.filename)}`; 
            img.alt = preset.name;
            img.loading = 'lazy'; // Lazy load images
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'preset-name';
            nameSpan.textContent = preset.name;
            
            const infoSpan = document.createElement('span');
            infoSpan.className = 'preset-info';
            infoSpan.textContent = `(${preset.extension}, ${preset.size_kb} KB)`;

            card.appendChild(img);
            card.appendChild(nameSpan);
            card.appendChild(infoSpan);
            
            card.addEventListener('click', () => {
                selectPresetCard(card);
            });
            
            card.addEventListener('dblclick', async () => {
                selectPresetCard(card);
                await applyPreset(preset.filename);
            });

            gifPresetGrid.appendChild(card);
        });
        
        updateSelectedPresetCard(); 
    }

    // Function to highlight the currently active preset card
    function updateSelectedPresetCard() {
        let currentFile = null;
        if (currentAppSettings?.type === 'static') {
            currentFile = currentAppSettings.static?.image_path;
        } else if (currentAppSettings?.type === 'animated') {
            currentFile = currentAppSettings.animated?.gif_path;
        }
        
        // Remove selection from previous card if it exists
        if (selectedPresetCard) {
             selectedPresetCard.classList.remove('selected');
             selectedPresetCard = null; // Reset tracked card
        }
        
        // Find and select the new card if a file is active
        if (currentFile) {
            const cards = gifPresetGrid.querySelectorAll('.preset-card');
            cards.forEach(card => {
                if (card.dataset.filename === currentFile) {
                    card.classList.add('selected');
                    selectedPresetCard = card; // Track the new selected card
                }
            });
        }
    }

    function updatePaginationControls(totalPresets) {
        if (totalPresets === 0) {
            presetPaginationDiv.style.display = 'none';
            return;
        }
        
        presetPaginationDiv.style.display = 'flex';
        presetPageInfo.textContent = `Page ${currentPresetPage} of ${totalPresetPages} (${totalPresets} items)`;
        
        presetPrevBtn.disabled = currentPresetPage <= 1;
        presetNextBtn.disabled = currentPresetPage >= totalPresetPages;
    }

    // Function to handle selecting a preset card by clicking
    function selectPresetCard(card) {
        if (selectedPresetCard) {
            selectedPresetCard.classList.remove('selected');
        }
        card.classList.add('selected');
        selectedPresetCard = card;
        // Optional: Automatically apply on single click?
        // applyPreset(card.dataset.filename);
    }
    
    // Function to apply the selected preset (e.g., on double-click or button)
    async function applyPreset(presetFilename) {
        if (!presetFilename) return;
        showStatusMessage(`Applying preset ${presetFilename}...`, "info", 0);
        try {
            const response = await fetch('/apply_gif_preset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ preset_filename: presetFilename }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            if (result.success && result.settings) {
                currentAppSettings = result.settings; // Update global state
                populateControls(currentAppSettings); // Update UI controls
                updateSelectedPresetCard(); // Update highlight
                showStatusMessage(`Preset applied!`, "success", 2000);
            } else {
                throw new Error(result.error || "Failed to apply preset.");
            }
        } catch (error) {
            console.error("Error applying preset:", error);
            showStatusMessage(`Failed to apply preset: ${error.message}`, "error", 5000);
            updateSelectedPresetCard(); // Resync selection with actual state
        }
    }

    // --- Event Listeners Setup Function --- 
    function setupControlListeners() {
        console.log("Setting up control listeners...");
        
        // Type selector change
        crosshairTypeSelect.addEventListener('change', () => { toggleControls(); sendUpdate(); });
        
        // Listeners for all parametric, static, and animated controls
        allControls.forEach(control => {
            if (control.id !== 'crosshairType' && control.type !== 'file') {
                const eventType = (control.type === 'range' || control.type === 'text' || control.type === 'number') ? 'input' : 'change';
                control.addEventListener(eventType, debouncedSendUpdate);
            }
        });
        
        // Image upload
        imageUploadInput.addEventListener('change', handleImageUpload);
        
        // Profile buttons
        saveProfileBtn.addEventListener('click', handleSaveProfile);
        loadProfileBtn.addEventListener('click', handleLoadProfile);
        deleteProfileBtn.addEventListener('click', handleDeleteProfile);
        
        // Profile name input (Enter key)
        profileNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleSaveProfile();
            }
        });
        
        // Pagination buttons (already set up earlier)
        
        console.log("Control listeners set up.");
    }

    // --- Initial Load --- 
    async function initializeApp() {
        console.log("Initializing app...");
        await fetchAndApplySettings();
        await fetchAndPopulateProfiles();
        fetchGifPresets(1); // Initial fetch for presets
        setupControlListeners(); // Call the listener setup function
        
        // Add Pagination Button Listeners here
        if (presetPrevBtn) {
            presetPrevBtn.addEventListener('click', () => {
                if (currentPresetPage > 1) {
                    fetchGifPresets(currentPresetPage - 1);
                }
            });
        }
    
        if (presetNextBtn) {
            presetNextBtn.addEventListener('click', () => {
                if (currentPresetPage < totalPresetPages) {
                    fetchGifPresets(currentPresetPage + 1);
                }
            });
        }
        
        console.log("App initialized.");
    }

    initializeApp();

}); 
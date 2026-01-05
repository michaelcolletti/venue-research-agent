// Venue Scout Setup Wizard - JavaScript
// Handles all wizard interactions, validation, and API calls

class WizardState {
    constructor() {
        this.currentStep = 1;
        this.locationData = null;
        this.selectedCities = [];
        this.acts = [];
    }
}

const state = new WizardState();

// Initialize wizard when page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeWizard();
});

function initializeWizard() {
    // Step 1: Location
    document.getElementById('lookup-btn').addEventListener('click', lookupZipCode);
    document.getElementById('zip-code').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') lookupZipCode();
    });
    document.getElementById('radius').addEventListener('input', (e) => {
        document.getElementById('radius-value').textContent = e.target.value;
        // Re-lookup if we already have location data
        if (state.locationData) {
            lookupZipCode();
        }
    });
    document.getElementById('select-all-cities').addEventListener('click', selectAllCities);
    document.getElementById('deselect-all-cities').addEventListener('click', deselectAllCities);
    document.getElementById('next-to-acts').addEventListener('click', () => goToStep(2));

    // Step 2: Acts
    document.getElementById('add-act-btn').addEventListener('click', addActForm);
    document.getElementById('back-to-location').addEventListener('click', () => goToStep(1));
    document.getElementById('next-to-review').addEventListener('click', () => goToStep(3));

    // Step 3: Review
    document.getElementById('back-to-acts').addEventListener('click', () => goToStep(2));
    document.getElementById('preview-config-btn').addEventListener('click', previewConfig);
    document.getElementById('save-config-btn').addEventListener('click', saveConfig);
    document.getElementById('close-preview').addEventListener('click', closePreviewModal);
    document.getElementById('close-preview-btn').addEventListener('click', closePreviewModal);

    // Add first act form by default
    addActForm();
}

// ============================================================================
// STEP NAVIGATION
// ============================================================================

function goToStep(stepNumber) {
    // Validate current step before moving forward
    if (stepNumber > state.currentStep) {
        if (!validateCurrentStep()) {
            return;
        }
    }

    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(step => {
        step.classList.remove('active');
    });

    // Show target step
    document.getElementById(`step-${stepNumber}`).classList.add('active');

    // Update progress bar
    document.querySelectorAll('.progress-step').forEach(step => {
        const num = parseInt(step.dataset.step);
        if (num <= stepNumber) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });

    // If going to review, populate review section
    if (stepNumber === 3) {
        populateReview();
    }

    state.currentStep = stepNumber;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function validateCurrentStep() {
    if (state.currentStep === 1) {
        return validateLocationStep();
    } else if (state.currentStep === 2) {
        return validateActsStep();
    }
    return true;
}

// ============================================================================
// STEP 1: LOCATION
// ============================================================================

async function lookupZipCode() {
    const zipInput = document.getElementById('zip-code');
    const zipCode = zipInput.value.trim();
    const radius = parseInt(document.getElementById('radius').value);
    const errorDiv = document.getElementById('zip-error');
    const lookupBtn = document.getElementById('lookup-btn');

    // Clear previous errors
    errorDiv.textContent = '';
    errorDiv.classList.remove('show');

    // Validate zip code format
    if (!/^\d{5}$/.test(zipCode)) {
        showError(errorDiv, 'Please enter a valid 5-digit zip code');
        return;
    }

    // Show loading
    lookupBtn.disabled = true;
    lookupBtn.textContent = 'Looking up...';

    try {
        const response = await fetch('/api/lookup-zip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ zipcode: zipCode, radius: radius })
        });

        const data = await response.json();

        if (!data.success) {
            showError(errorDiv, data.error);
            return;
        }

        // Store location data
        state.locationData = data;

        // Display location info
        document.getElementById('detected-city').textContent = data.city;
        document.getElementById('detected-county').textContent = data.county;
        document.getElementById('detected-region').textContent = getRegionName(data.county);

        // Populate cities list
        populateCities(data.nearby_cities);

        // Show results
        document.getElementById('location-results').classList.remove('hidden');

    } catch (error) {
        showError(errorDiv, 'Error looking up zip code: ' + error.message);
    } finally {
        lookupBtn.disabled = false;
        lookupBtn.textContent = 'Lookup';
    }
}

function populateCities(cities) {
    const citiesList = document.getElementById('cities-list');
    citiesList.innerHTML = '';

    cities.forEach((cityData, index) => {
        const label = document.createElement('label');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = index;
        checkbox.dataset.city = cityData.city;
        checkbox.dataset.county = cityData.county;

        // Pre-select first 10 cities
        if (index < 10) {
            checkbox.checked = true;
        }

        checkbox.addEventListener('change', updateCitySelection);

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(` ${cityData.city}`));
        citiesList.appendChild(label);
    });

    // Update city count
    updateCityCount();
}

function updateCitySelection() {
    updateCityCount();

    // Enable next button if at least one city selected
    const checkedCount = document.querySelectorAll('#cities-list input:checked').length;
    document.getElementById('next-to-acts').disabled = checkedCount === 0;
}

function updateCityCount() {
    const checkboxes = document.querySelectorAll('#cities-list input');
    const checkedCount = document.querySelectorAll('#cities-list input:checked').length;
    const total = checkboxes.length;

    document.getElementById('city-count').textContent = `${checkedCount} of ${total} selected`;
}

function selectAllCities() {
    document.querySelectorAll('#cities-list input').forEach(cb => {
        cb.checked = true;
    });
    updateCitySelection();
}

function deselectAllCities() {
    document.querySelectorAll('#cities-list input').forEach(cb => {
        cb.checked = false;
    });
    updateCitySelection();
}

function validateLocationStep() {
    const errorDiv = document.getElementById('cities-error');
    errorDiv.textContent = '';

    if (!state.locationData) {
        showError(document.getElementById('zip-error'), 'Please lookup a zip code first');
        return false;
    }

    const checkedCount = document.querySelectorAll('#cities-list input:checked').length;
    if (checkedCount === 0) {
        showError(errorDiv, 'Please select at least one city');
        return false;
    }

    // Store selected cities
    state.selectedCities = Array.from(document.querySelectorAll('#cities-list input:checked')).map(cb => ({
        city: cb.dataset.city,
        county: cb.dataset.county
    }));

    return true;
}

// ============================================================================
// STEP 2: ACTS
// ============================================================================

let actCounter = 0;

function addActForm() {
    const template = document.getElementById('act-template');
    const clone = template.content.cloneNode(true);

    actCounter++;

    // Update act number
    clone.querySelector('.act-number').textContent = actCounter;

    // Add remove button handler (except for first act)
    const removeBtn = clone.querySelector('.remove-act-btn');
    if (actCounter === 1) {
        removeBtn.style.visibility = 'hidden';
    } else {
        removeBtn.addEventListener('click', function() {
            this.closest('.act-form').remove();
            updateActNumbers();
        });
    }

    // Add to container
    document.getElementById('acts-container').appendChild(clone);
}

function updateActNumbers() {
    document.querySelectorAll('.act-form').forEach((form, index) => {
        form.querySelector('.act-number').textContent = index + 1;

        // Hide remove button for first act
        const removeBtn = form.querySelector('.remove-act-btn');
        if (index === 0) {
            removeBtn.style.visibility = 'hidden';
        } else {
            removeBtn.style.visibility = 'visible';
        }
    });
}

function validateActsStep() {
    const actForms = document.querySelectorAll('.act-form');

    if (actForms.length === 0) {
        alert('Please add at least one act profile');
        return false;
    }

    // Validate each act form
    for (let form of actForms) {
        const name = form.querySelector('.act-name').value.trim();
        if (!name) {
            alert('Please enter a name for all acts');
            form.querySelector('.act-name').focus();
            return false;
        }

        const genres = form.querySelectorAll('input[type="checkbox"][value]:checked');
        const genreValues = Array.from(genres)
            .filter(cb => cb.closest('.form-group')?.querySelector('label')?.textContent.includes('Genres'))
            .map(cb => cb.value);

        if (genreValues.length === 0) {
            alert('Please select at least one genre for all acts');
            return false;
        }

        const days = form.querySelectorAll('input[type="checkbox"][value]:checked');
        const dayValues = Array.from(days)
            .filter(cb => cb.closest('.form-group')?.querySelector('label')?.textContent.includes('Available Days'))
            .map(cb => cb.value);

        if (dayValues.length === 0) {
            alert('Please select at least one available day for all acts');
            return false;
        }

        const venueTypes = form.querySelectorAll('input[type="checkbox"][value]:checked');
        const venueTypeValues = Array.from(venueTypes)
            .filter(cb => cb.closest('.form-group')?.querySelector('label')?.textContent.includes('Venue Types'))
            .map(cb => cb.value);

        if (venueTypeValues.length === 0) {
            alert('Please select at least one venue type for all acts');
            return false;
        }
    }

    // Store acts data
    state.acts = collectActsData();

    return true;
}

function collectActsData() {
    const actForms = document.querySelectorAll('.act-form');
    const acts = [];

    actForms.forEach(form => {
        const genres = Array.from(form.querySelectorAll('input[type="checkbox"]'))
            .filter(cb => {
                const label = cb.closest('.form-group')?.querySelector('label')?.textContent;
                return label && label.includes('Genres') && cb.checked;
            })
            .map(cb => cb.value);

        const days = Array.from(form.querySelectorAll('input[type="checkbox"]'))
            .filter(cb => {
                const label = cb.closest('.form-group')?.querySelector('label')?.textContent;
                return label && label.includes('Available Days') && cb.checked;
            })
            .map(cb => cb.value);

        const venueTypes = Array.from(form.querySelectorAll('input[type="checkbox"]'))
            .filter(cb => {
                const label = cb.closest('.form-group')?.querySelector('label')?.textContent;
                return label && label.includes('Venue Types') && cb.checked;
            })
            .map(cb => cb.value);

        acts.push({
            name: form.querySelector('.act-name').value.trim(),
            genres: genres,
            members: parseInt(form.querySelector('.act-members').value),
            min_capacity: parseInt(form.querySelector('.act-min-capacity').value),
            ideal_capacity: parseInt(form.querySelector('.act-ideal-capacity').value),
            max_capacity: parseInt(form.querySelector('.act-max-capacity').value),
            min_fee: parseInt(form.querySelector('.act-min-fee').value),
            max_fee: parseInt(form.querySelector('.act-max-fee').value),
            available_days: days,
            venue_types: venueTypes,
            notes: form.querySelector('.act-notes').value.trim(),
            requires_stage: true,
            requires_sound_system: true,
            set_length_hours: 2
        });
    });

    return acts;
}

// ============================================================================
// STEP 3: REVIEW
// ============================================================================

function populateReview() {
    // Location info
    document.getElementById('review-location').textContent =
        `${state.locationData.city}, NY (${document.getElementById('zip-code').value})`;

    document.getElementById('review-radius').textContent =
        `${document.getElementById('radius').value} miles`;

    document.getElementById('review-cities-count').textContent =
        `${state.selectedCities.length} cities`;

    // Acts info
    const reviewActs = document.getElementById('review-acts');
    reviewActs.innerHTML = '';

    state.acts.forEach((act, index) => {
        const actDiv = document.createElement('div');
        actDiv.className = 'review-act';
        actDiv.innerHTML = `
            <h4>${index + 1}. ${act.name}</h4>
            <p><strong>Genres:</strong> ${act.genres.join(', ')}</p>
            <p><strong>Members:</strong> ${act.members}</p>
            <p><strong>Capacity Range:</strong> ${act.min_capacity} - ${act.max_capacity} (ideal: ${act.ideal_capacity})</p>
            <p><strong>Fee Range:</strong> $${act.min_fee} - $${act.max_fee}</p>
            <p><strong>Available:</strong> ${act.available_days.join(', ')}</p>
        `;
        reviewActs.appendChild(actDiv);
    });
}

async function previewConfig() {
    const formData = collectFormData();

    showLoading('Generating preview...');

    try {
        const response = await fetch('/api/preview-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('preview-content').textContent = data.config;
            document.getElementById('preview-modal').classList.remove('hidden');
        } else {
            alert('Error generating preview: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        hideLoading();
    }
}

function closePreviewModal() {
    document.getElementById('preview-modal').classList.add('hidden');
}

async function saveConfig() {
    if (!confirm('Save configuration and initialize venue-scout?')) {
        return;
    }

    const formData = collectFormData();
    formData.init_db = document.getElementById('init-db-checkbox').checked;

    showLoading('Saving configuration...');

    try {
        const response = await fetch('/api/save-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            // Show success page
            document.getElementById('config-path-display').textContent = data.config_path;

            if (data.db_initialized) {
                document.getElementById('db-status').classList.remove('hidden');
            }

            if (data.backup_path) {
                document.getElementById('backup-info').classList.remove('hidden');
            }

            // Go to success step
            document.getElementById('step-3').classList.remove('active');
            document.getElementById('step-success').classList.add('active');
        } else {
            alert('Error saving configuration: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        hideLoading();
    }
}

function collectFormData() {
    return {
        zip_code: document.getElementById('zip-code').value.trim(),
        base_region: getRegionName(state.locationData.county),
        radius: parseInt(document.getElementById('radius').value),
        cities_with_counties: state.selectedCities,
        acts: state.acts
    };
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function getRegionName(county) {
    const regionMap = {
        'Ulster': 'Hudson Valley',
        'Dutchess': 'Hudson Valley',
        'Columbia': 'Hudson Valley',
        'Greene': 'Hudson Valley',
        'Orange': 'Hudson Valley',
        'Sullivan': 'Hudson Valley',
        'Albany': 'Capital District',
        'Schenectady': 'Capital District',
        'Rensselaer': 'Capital District',
        'Saratoga': 'Capital District',
        'Delaware': 'Catskills',
        'Westchester': 'NYC Metro',
        'Rockland': 'NYC Metro',
        'Putnam': 'NYC Metro'
    };

    return regionMap[county] || 'Custom Region';
}

function showError(element, message) {
    element.textContent = message;
    element.classList.add('show');
}

function showLoading(message) {
    document.getElementById('loading-text').textContent = message;
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

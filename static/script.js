// Theme functionality
document.addEventListener("DOMContentLoaded", () => {
    // Initialize theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Update toggle button icon based on current theme
    updateThemeToggleIcon(savedTheme);
});

// Toggle theme function
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    // Set the theme attribute on html element
    document.documentElement.setAttribute('data-theme', newTheme);
    
    // Save theme preference to localStorage
    localStorage.setItem('theme', newTheme);
    
    // Update toggle button icon
    updateThemeToggleIcon(newTheme);
}

// Update theme toggle icon based on current theme
function updateThemeToggleIcon(theme) {
    const themeToggles = document.querySelectorAll('.theme-toggle');
    themeToggles.forEach(toggle => {
        const moonIcon = toggle.querySelector('.fa-moon');
        const sunIcon = toggle.querySelector('.fa-sun');
        
        if (theme === 'dark') {
            moonIcon.style.opacity = '0';
            moonIcon.style.transform = 'translateY(-20px) rotate(-90deg)';
            sunIcon.style.opacity = '1';
            sunIcon.style.transform = 'translateY(0) rotate(0)';
        } else {
            moonIcon.style.opacity = '1';
            moonIcon.style.transform = 'translateY(0) rotate(0)';
            sunIcon.style.opacity = '0';
            sunIcon.style.transform = 'translateY(20px) rotate(90deg)';
        }
    });
}

// Form toggle functionality
const radioButtons = document.querySelectorAll('input[name="input-type"]');
const jobTextContainer = document.getElementById('jobTextContainer');
const jobFileContainer = document.getElementById('jobFileContainer');

radioButtons.forEach(radio => {
    radio.addEventListener('change', () => {
        if (radio.value === 'text') {
            jobTextContainer.style.display = 'block';
            jobFileContainer.style.display = 'none';
        } else {
            jobTextContainer.style.display = 'none';
            jobFileContainer.style.display = 'block';
        }
    });
});

// Modal logic
function confirmDelete(url) {
    const modal = document.getElementById('deleteModal');
    const form = document.getElementById('deleteForm');
    form.action = url;
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('deleteModal').style.display = 'none';
}

// Close modal if clicked outside content
window.onclick = function(event) {
    const modal = document.getElementById('deleteModal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}


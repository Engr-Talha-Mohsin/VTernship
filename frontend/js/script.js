/* ==========================================
   VTERNSHIP - INTERACTIVE JAVASCRIPT
   ========================================== */

// ==========================================
// GLOBAL VARIABLES
// ==========================================
let scrollPosition = 0;
let isScrolling = false;

// ==========================================
// NAVBAR FUNCTIONALITY
// ==========================================

/**
 * Handle navbar scroll effect
 * Adds shadow and background when scrolling
 */
function handleNavbarScroll() {
    const navbar = document.getElementById('navbar');
    
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
}

/**
 * Toggle mobile menu
 */
function toggleMobileMenu() {
    const navLinks = document.getElementById('navLinks');
    const mobileToggle = document.getElementById('mobileToggle');
    
    navLinks.classList.toggle('active');
    mobileToggle.classList.toggle('active');
}

/**
 * Close mobile menu when clicking outside
 */
function handleClickOutside(event) {
    const navLinks = document.getElementById('navLinks');
    const mobileToggle = document.getElementById('mobileToggle');
    
    if (!navLinks.contains(event.target) && !mobileToggle.contains(event.target)) {
        navLinks.classList.remove('active');
        mobileToggle.classList.remove('active');
    }
}

/**
 * Close mobile menu when clicking on a link
 */
function closeMobileMenuOnLinkClick() {
    const navLinks = document.querySelectorAll('.nav-links a');
    const navLinksContainer = document.getElementById('navLinks');
    const mobileToggle = document.getElementById('mobileToggle');
    
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navLinksContainer.classList.remove('active');
            mobileToggle.classList.remove('active');
        });
    });
}

// ==========================================
// COUNTER ANIMATION
// ==========================================

/**
 * Animate counter numbers on scroll
 * @param {HTMLElement} element - The element containing the counter
 * @param {number} target - Target number to count to
 * @param {number} duration - Animation duration in milliseconds
 */
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16); // 60 FPS
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        // Format number with commas for readability
        element.textContent = Math.floor(current).toLocaleString();
        
        // Add percentage symbol if target ends with it
        if (element.dataset.target.toString().includes('%') || target < 100) {
            element.textContent = Math.floor(current);
            if (element.textContent === target.toString()) {
                element.textContent += '%';
            }
        }
    }, 16); // ~60 FPS
}

/**
 * Initialize counter animations when elements come into view
 */
function initCounterAnimations() {
    const counters = document.querySelectorAll('.stat-number');
    
    if (counters.length === 0) return;
    
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                const target = parseInt(entry.target.dataset.target);
                animateCounter(entry.target, target);
                entry.target.classList.add('animated');
            }
        });
    }, observerOptions);
    
    counters.forEach(counter => observer.observe(counter));
}

// ==========================================
// SCROLL ANIMATIONS
// ==========================================

/**
 * Add fade-in animation to elements on scroll
 */
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll(
        '.feature-card, .skill-card, .stat-card, .problem-card, .benefit-item, .journey-step, .faq-item, .contact-card'
    );
    
    if (animatedElements.length === 0) return;
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Add staggered delay for multiple elements
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
            }
        });
    }, observerOptions);
    
    // Set initial state
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
}

// ==========================================
// SMOOTH SCROLLING
// ==========================================

/**
 * Enable smooth scrolling for anchor links
 */
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            
            // Skip if it's just "#"
            if (href === '#') {
                e.preventDefault();
                return;
            }
            
            const target = document.querySelector(href);
            
            if (target) {
                e.preventDefault();
                const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ==========================================
// FORM HANDLING
// ==========================================

/**
 * Handle contact form submission
 * @param {Event} e - Form submit event
 */
function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Get form values
    const firstName = formData.get('firstName');
    const lastName = formData.get('lastName');
    const email = formData.get('email');
    const subject = formData.get('subject');
    const message = formData.get('message');
    
    // Validate form (basic validation)
    if (!firstName || !lastName || !email || !subject || !message) {
        showNotification('Please fill in all fields', 'error');
        return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    // Simulate form submission
    showNotification('Sending message...', 'info');
    
    // Simulate API call with timeout
    setTimeout(() => {
        showNotification('Message sent successfully! We\'ll get back to you soon.', 'success');
        form.reset();
    }, 1500);
}

/**
 * Show notification message
 * @param {string} message - Message to display
 * @param {string} type - Notification type (success, error, info)
 */
function showNotification(message, type = 'info') {
    // Remove existing notification if any
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 300px;
        font-weight: 600;
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// ==========================================
// BUTTON INTERACTIONS
// ==========================================

/**
 * Add ripple effect to buttons
 * @param {Event} e - Click event
 */
function createRipple(e) {
    const button = e.currentTarget;
    const circle = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;
    
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${e.clientX - button.offsetLeft - radius}px`;
    circle.style.top = `${e.clientY - button.offsetTop - radius}px`;
    circle.classList.add('ripple');
    
    const ripple = button.getElementsByClassName('ripple')[0];
    if (ripple) {
        ripple.remove();
    }
    
    button.appendChild(circle);
}

/**
 * Initialize ripple effect on buttons
 */
function initRippleEffect() {
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary, .btn-signin');
    
    buttons.forEach(button => {
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        button.addEventListener('click', createRipple);
    });
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Check if element is in viewport
 * @param {HTMLElement} element - Element to check
 * @returns {boolean} - Whether element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Add CSS for animations
 */
function addAnimationStyles() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.5);
            transform: scale(0);
            animation: ripple-animation 0.6s ease-out;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// ==========================================
// PERFORMANCE OPTIMIZATION
// ==========================================

/**
 * Optimize scroll performance using requestAnimationFrame
 */
function optimizeScrollHandler() {
    let ticking = false;
    
    window.addEventListener('scroll', () => {
        scrollPosition = window.scrollY;
        
        if (!ticking) {
            window.requestAnimationFrame(() => {
                handleNavbarScroll();
                ticking = false;
            });
            
            ticking = true;
        }
    });
}

// ==========================================
// PAGE VISIBILITY
// ==========================================

/**
 * Handle page visibility changes
 * Pause animations when page is not visible
 */
function handleVisibilityChange() {
    if (document.hidden) {
        // Pause animations or reduce activity
        console.log('Page is hidden - reducing activity');
    } else {
        // Resume animations
        console.log('Page is visible - resuming activity');
    }
}

// ==========================================
// INITIALIZATION
// ==========================================

/**
 * Initialize all functionality when DOM is loaded
 */
function init() {
    console.log('VTernship Platform Initialized');
    
    // Add animation styles
    addAnimationStyles();
    
    // Initialize navbar
    const mobileToggle = document.getElementById('mobileToggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleMobileMenu);
    }
    
    // Close menu when clicking outside
    document.addEventListener('click', handleClickOutside);
    
    // Close menu on link click
    closeMobileMenuOnLinkClick();
    
    // Initialize scroll effects
    optimizeScrollHandler();
    handleNavbarScroll();
    
    // Initialize animations
    initScrollAnimations();
    initCounterAnimations();
    initSmoothScrolling();
    initRippleEffect();
    
    // Initialize form handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Handle page visibility
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Add resize listener with debounce
    window.addEventListener('resize', debounce(() => {
        console.log('Window resized');
        // Handle responsive adjustments if needed
    }, 250));
    
    // Log page load time
    window.addEventListener('load', () => {
        const loadTime = performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart;
        console.log(`Page loaded in ${loadTime}ms`);
    });
}

// ==========================================
// EVENT LISTENERS
// ==========================================

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Handle browser back/forward navigation
window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
        // Page was loaded from cache
        console.log('Page restored from cache');
        handleNavbarScroll();
    }
});

// ==========================================
// BROWSER COMPATIBILITY
// ==========================================

/**
 * Check for browser features and provide fallbacks
 */
function checkBrowserSupport() {
    // Check for IntersectionObserver support
    if (!('IntersectionObserver' in window)) {
        console.warn('IntersectionObserver not supported - animations may not work properly');
        // Could add a polyfill here
    }
    
    // Check for CSS Grid support
    if (!CSS.supports('display', 'grid')) {
        console.warn('CSS Grid not supported - layout may not display correctly');
    }
}

checkBrowserSupport();

// ==========================================
// EXPORT FUNCTIONS (for potential module use)
// ==========================================

// Make functions available globally if needed
window.VTernship = {
    showNotification,
    animateCounter,
    toggleMobileMenu
};

console.log('VTernship JavaScript loaded successfully ✓');

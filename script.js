// Wood Hudson Cancer Research Laboratory Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    initMobileMenu();
    
    // Smooth scrolling for anchor links
    initSmoothScrolling();
    
    // Newsletter form handling
    initNewsletterForm();
    
    // Donation form handling
    initDonationForm();
    
    // Contact form handling
    initContactForm();
    
    // Active navigation highlighting
    initNavigationHighlighting();
    
    // Animation on scroll
    initScrollAnimations();
});

// Mobile Menu Toggle
function initMobileMenu() {
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            mobileToggle.classList.toggle('active');
        });
        
        // Close mobile menu when clicking on a link
        const navLinkItems = document.querySelectorAll('.nav-link');
        navLinkItems.forEach(link => {
            link.addEventListener('click', function() {
                navLinks.classList.remove('active');
                mobileToggle.classList.remove('active');
            });
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileToggle.contains(e.target) && !navLinks.contains(e.target)) {
                navLinks.classList.remove('active');
                mobileToggle.classList.remove('active');
            }
        });
    }
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetSection.offsetTop - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Newsletter form handling
function initNewsletterForm() {
    const newsletterForm = document.querySelector('.newsletter-form');
    
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = this.querySelector('input[type="email"]').value;
            
            if (validateEmail(email)) {
                // Simulate newsletter signup
                showMessage('Thank you for subscribing to our newsletter!', 'success');
                this.reset();
            } else {
                showMessage('Please enter a valid email address.', 'error');
            }
        });
    }
}

// Donation form handling
function initDonationForm() {
    const amountButtons = document.querySelectorAll('.amount-btn');
    const customAmountInput = document.querySelector('.custom-amount');
    const donateSubmit = document.querySelector('.donate-submit');
    
    // Amount button selection
    amountButtons.forEach(button => {
        button.addEventListener('click', function() {
            amountButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            if (customAmountInput) {
                customAmountInput.value = '';
            }
        });
    });
    
    // Custom amount input
    if (customAmountInput) {
        customAmountInput.addEventListener('input', function() {
            amountButtons.forEach(btn => btn.classList.remove('active'));
        });
    }
    
    // Donation submission
    if (donateSubmit) {
        donateSubmit.addEventListener('click', function(e) {
            e.preventDefault();
            
            const selectedAmount = document.querySelector('.amount-btn.active');
            const customAmount = customAmountInput ? customAmountInput.value : '';
            const frequency = document.querySelector('input[name="frequency"]:checked');
            
            let amount = 0;
            
            if (selectedAmount) {
                amount = selectedAmount.dataset.amount;
            } else if (customAmount && parseFloat(customAmount) > 0) {
                amount = parseFloat(customAmount);
            }
            
            if (amount > 0 && frequency) {
                // In a real implementation, this would integrate with a payment processor
                showMessage(`Thank you for your ${frequency.value} donation of $${amount}! Redirecting to secure payment...`, 'success');
                
                // Simulate redirect delay
                setTimeout(() => {
                    showMessage('In a production site, you would be redirected to a secure payment processor.', 'info');
                }, 2000);
            } else {
                showMessage('Please select or enter a donation amount and frequency.', 'error');
            }
        });
    }
}

// Contact form handling
function initContactForm() {
    const contactForm = document.querySelector('.contact-form form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const name = formData.get('name');
            const email = formData.get('email');
            const subject = formData.get('subject');
            const message = formData.get('message');
            
            if (name && email && subject && message) {
                if (validateEmail(email)) {
                    // Simulate form submission
                    showMessage('Thank you for your message! We will get back to you soon.', 'success');
                    this.reset();
                } else {
                    showMessage('Please enter a valid email address.', 'error');
                }
            } else {
                showMessage('Please fill in all required fields.', 'error');
            }
        });
    }
}

// Navigation highlighting based on scroll position
function initNavigationHighlighting() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    if (sections.length === 0) return;
    
    function highlightNavigation() {
        let current = '';
        const scrollPosition = window.scrollY + 150;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    }
    
    window.addEventListener('scroll', highlightNavigation);
    highlightNavigation(); // Initial call
}

// Animation on scroll
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.highlight-card, .program-card, .benefit-card, .testimonial-card, .leader-card, .value-card');
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
}

// Utility functions
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showMessage(message, type = 'info') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.message-popup');
    existingMessages.forEach(msg => msg.remove());
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-popup message-${type}`;
    messageDiv.textContent = message;
    
    // Style the message
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        max-width: 400px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    // Set background color based on type
    const colors = {
        success: '#2d7d4a',
        error: '#dc3545',
        info: '#17a2b8'
    };
    messageDiv.style.backgroundColor = colors[type] || colors.info;
    
    // Add to DOM
    document.body.appendChild(messageDiv);
    
    // Animate in
    setTimeout(() => {
        messageDiv.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after delay
    setTimeout(() => {
        messageDiv.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 300);
    }, 4000);
}

// Header scroll behavior
window.addEventListener('scroll', function() {
    const header = document.querySelector('.header');
    if (window.scrollY > 100) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});

// Add CSS for mobile menu and scroll effects
const additionalStyles = `
    .nav-links.active {
        display: flex !important;
        flex-direction: column;
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background-color: var(--white);
        box-shadow: var(--shadow);
        padding: 1rem;
        gap: 1rem;
    }
    
    .mobile-menu-toggle.active span:nth-child(1) {
        transform: rotate(45deg) translate(6px, 6px);
    }
    
    .mobile-menu-toggle.active span:nth-child(2) {
        opacity: 0;
    }
    
    .mobile-menu-toggle.active span:nth-child(3) {
        transform: rotate(-45deg) translate(6px, -6px);
    }
    
    .header.scrolled {
        background-color: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }
    
    @media (max-width: 768px) {
        .nav-links {
            display: none;
        }
        
        .mobile-menu-toggle {
            display: flex !important;
        }
    }
`;

// Add the styles to the document
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);
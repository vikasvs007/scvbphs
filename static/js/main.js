document.addEventListener('DOMContentLoaded', function() {
    // Admission bar close functionality
    const closeBtn = document.querySelector('.admission-bar .close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            const admissionBar = document.querySelector('.admission-bar');
            admissionBar.style.height = '0';
            admissionBar.style.padding = '0';
            admissionBar.style.overflow = 'hidden';
            setTimeout(() => {
                admissionBar.style.display = 'none';
            }, 300);
        });
    }

    // Flash Messages
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);

        // Manual dismiss
        const closeBtn = message.querySelector('.close-flash');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            });
        }
    });

    // Mobile Navigation
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');

    hamburger.addEventListener('click', function() {
        navLinks.classList.toggle('active');
        hamburger.classList.toggle('active');
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!hamburger.contains(event.target) && !navLinks.contains(event.target)) {
            navLinks.classList.remove('active');
            hamburger.classList.remove('active');
        }
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Close mobile menu after clicking a link
                navLinks.classList.remove('active');
                hamburger.classList.remove('active');
            }
        });
    });

    // Scroll to top button
    const scrollBtn = document.createElement('button');
    scrollBtn.innerHTML = '↑';
    scrollBtn.className = 'scroll-top';
    scrollBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 40px;
        height: 40px;
        background: #4527a0;
        color: white;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        display: none;
        font-size: 20px;
        z-index: 1000;
    `;
    document.body.appendChild(scrollBtn);

    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollBtn.style.display = 'block';
        } else {
            scrollBtn.style.display = 'none';
        }
    });

    scrollBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

    // Form validation
    const admissionForm = document.getElementById('admissionForm');
    if (admissionForm) {
        admissionForm.addEventListener('submit', function(e) {
            const phoneInput = this.querySelector('input[name="phone"]');
            const phonePattern = /^[0-9]{10}$/;
            
            if (!phonePattern.test(phoneInput.value)) {
                e.preventDefault();
                alert('Please enter a valid 10-digit phone number');
                phoneInput.focus();
            }
        });
    }

    // Image lazy loading
    const images = document.querySelectorAll('img[data-src]');
    const imageOptions = {
        threshold: 0,
        rootMargin: '0px 0px 50px 0px'
    };

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('fade-in');
                observer.unobserve(img);
            }
        });
    }, imageOptions);

    images.forEach(img => imageObserver.observe(img));

    // Add animation class to elements when they come into view
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    const elementObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
            }
        });
    }, {
        threshold: 0.1
    });

    animatedElements.forEach(element => elementObserver.observe(element));
}); 
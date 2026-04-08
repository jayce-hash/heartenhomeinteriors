// Navbar scroll effect
window.addEventListener('scroll', function () {
    const navbar = document.getElementById('navbar');
    if (navbar) {
        navbar.classList.toggle('scrolled', window.scrollY > 50);
    }
});

// Mobile menu toggle
const mobileMenu = document.getElementById('mobile-menu');
const navLinks = document.getElementById('nav-links');

if (mobileMenu && navLinks) {
    mobileMenu.addEventListener('click', () => {
        navLinks.classList.toggle('open');
        mobileMenu.classList.toggle('open');
    });

    document.querySelectorAll('.nav-links a').forEach(item => {
        item.addEventListener('click', () => {
            navLinks.classList.remove('open');
            mobileMenu.classList.remove('open');
        });
    });
}

// Reveal elements on scroll
function reveal() {
    document.querySelectorAll('.reveal').forEach(el => {
        if (el.getBoundingClientRect().top < window.innerHeight - 90) {
            el.classList.add('active');
        }
    });
}
window.addEventListener('scroll', reveal);
// Trigger on initial load
document.addEventListener('DOMContentLoaded', reveal);

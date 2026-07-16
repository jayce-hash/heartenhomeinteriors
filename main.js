document.addEventListener('DOMContentLoaded', () => {
    // 1. Navbar transparent-to-solid scroll effect
    const navbar = document.getElementById('navbar');
    
    window.addEventListener('scroll', () => {
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    });

    // 2. Mobile Menu Toggle
    const mobileMenu = document.getElementById('mobile-menu');
    const navLinks = document.getElementById('nav-links');

    if (mobileMenu && navLinks) {
        mobileMenu.addEventListener('click', () => {
            navLinks.classList.toggle('open');
        });

        // Close menu when clicking a link
        document.querySelectorAll('.nav-links a').forEach(item => {
            item.addEventListener('click', () => {
                navLinks.classList.remove('open');
            });
        });
    }

    // 3. Reveal elements on scroll
    function reveal() {
        const reveals = document.querySelectorAll('.reveal');
        const windowHeight = window.innerHeight;
        const elementVisible = 100;

        reveals.forEach(el => {
            const elementTop = el.getBoundingClientRect().top;
            if (elementTop < windowHeight - elementVisible) {
                el.classList.add('active');
            }
        });
    }
    
    window.addEventListener('scroll', reveal);
    reveal(); // Trigger on initial load

    // 4. Gallery lightbox (project pages only)
    const masonry = document.querySelector('.gallery-masonry');
    if (masonry) {
        const shots = Array.from(masonry.querySelectorAll('img'));
        let idx = 0;

        const box = document.createElement('div');
        box.className = 'lightbox';
        box.innerHTML =
            '<button class="lb-close" type="button" aria-label="Close">&times;</button>' +
            '<button class="lb-prev" type="button" aria-label="Previous photo">&#8249;</button>' +
            '<figure class="lb-stage"><img alt=""></figure>' +
            '<button class="lb-next" type="button" aria-label="Next photo">&#8250;</button>' +
            '<div class="lb-count"></div>';
        document.body.appendChild(box);

        const bigImg = box.querySelector('.lb-stage img');
        const counter = box.querySelector('.lb-count');

        function show(n) {
            idx = (n + shots.length) % shots.length;
            bigImg.src = shots[idx].currentSrc || shots[idx].src;
            bigImg.alt = shots[idx].alt || '';
            counter.textContent = (idx + 1) + ' / ' + shots.length;
        }
        function open(n) {
            show(n);
            box.classList.add('open');
            document.body.style.overflow = 'hidden';
        }
        function close() {
            box.classList.remove('open');
            document.body.style.overflow = '';
        }

        shots.forEach((img, i) => {
            img.style.cursor = 'zoom-in';
            img.addEventListener('click', () => open(i));
        });

        box.querySelector('.lb-close').addEventListener('click', close);
        box.querySelector('.lb-prev').addEventListener('click', e => { e.stopPropagation(); show(idx - 1); });
        box.querySelector('.lb-next').addEventListener('click', e => { e.stopPropagation(); show(idx + 1); });
        box.addEventListener('click', e => { if (e.target === box || e.target.classList.contains('lb-stage')) close(); });

        document.addEventListener('keydown', e => {
            if (!box.classList.contains('open')) return;
            if (e.key === 'Escape') close();
            if (e.key === 'ArrowLeft') show(idx - 1);
            if (e.key === 'ArrowRight') show(idx + 1);
        });
    }
});

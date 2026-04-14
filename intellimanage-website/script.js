// Nav scroll behavior
const navbar = document.querySelector('.navbar');

window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.style.padding = '10px 0';
        navbar.style.boxShadow = 'var(--shadow-md)';
    } else {
        navbar.style.padding = '15px 0';
        navbar.style.boxShadow = 'var(--shadow-sm)';
    }
});

// Modal Logic
const modal = document.getElementById('planModal');
const closeBtn = document.querySelector('.close-btn');
const planBtns = document.querySelectorAll('.plan-btn');
const selectedPlanName = document.getElementById('selectedPlanName');

planBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        const plan = e.target.getAttribute('data-plan');
        selectedPlanName.textContent = plan;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    });
});

const closeModal = () => {
    modal.classList.remove('active');
    document.body.style.overflow = 'auto'; // Restore scrolling
};

closeBtn.addEventListener('click', closeModal);

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        closeModal();
    }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        const targetId = this.getAttribute('href');
        if (targetId === '#') return;

        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            const navHeight = navbar.offsetHeight;
            const targetPosition = targetElement.getBoundingClientRect().top + window.scrollY - navHeight;

            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Animation on scroll for feature cards
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.querySelectorAll('.feature-card').forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(30px)';
    card.style.transition = `all 0.6s cubic-bezier(0.25, 0.8, 0.25, 1) ${index * 0.1}s`;
    observer.observe(card);
});

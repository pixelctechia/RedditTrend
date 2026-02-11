/**
 * RedditPulse — Landing Page Interactive Logic
 *
 * Features:
 *  - Animated floating particles in the hero background
 *  - Smooth scroll-reveal for sections
 *  - Subreddit tab switching in the mockup
 *  - Typing effect on post titles
 */

document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initScrollReveal();
    initMockupInteraction();
});

/* =============================================
   PARTICLES — Floating dots in the hero bg
   ============================================= */
function initParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    const PARTICLE_COUNT = 30;
    const colors = ['#ff4500', '#00d2ff', '#a855f7', '#ff6b35', '#3fb950'];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        const particle = document.createElement('span');
        const size = Math.random() * 4 + 2;
        const color = colors[Math.floor(Math.random() * colors.length)];
        const left = Math.random() * 100;
        const top = Math.random() * 100;
        const duration = Math.random() * 6 + 4;
        const delay = Math.random() * 4;

        Object.assign(particle.style, {
            position: 'absolute',
            width: `${size}px`,
            height: `${size}px`,
            borderRadius: '50%',
            background: color,
            opacity: `${Math.random() * 0.4 + 0.1}`,
            left: `${left}%`,
            top: `${top}%`,
            animation: `float ${duration}s ease-in-out ${delay}s infinite`,
            pointerEvents: 'none',
        });

        container.appendChild(particle);
    }
}

/* =============================================
   SCROLL REVEAL — Animate sections on scroll
   ============================================= */
function initScrollReveal() {
    const sections = document.querySelectorAll(
        '.features, .quickstart, .formula, .feature-card, .step'
    );

    if (!sections.length) return;

    // Set initial hidden state
    sections.forEach((el) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    sections.forEach((el) => observer.observe(el));
}

/* =============================================
   MOCKUP INTERACTION — Tab switching
   ============================================= */
function initMockupInteraction() {
    const subs = document.querySelectorAll('.mockup__sub');
    const posts = document.querySelectorAll('.mockup__card');

    if (!subs.length) return;

    // Sample data per subreddit for the mockup
    const mockData = {
        Python: [
            { title: 'Python 3.14 released with...', up: '2.5k', comments: '420' },
            { title: 'Best async frameworks in 2026', up: '1.8k', comments: '312' },
            { title: 'I built an AI agent that codes', up: '1.2k', comments: '287' },
        ],
        JavaScript: [
            { title: 'Deno vs Bun vs Node benchmark', up: '3.1k', comments: '520' },
            { title: 'React Server Components guide', up: '2.2k', comments: '380' },
            { title: 'TypeScript 6.0 is here!', up: '1.9k', comments: '295' },
        ],
        DevOps: [
            { title: 'K8s vs Docker Swarm in 2026', up: '1.8k', comments: '340' },
            { title: 'Terraform best practices', up: '1.4k', comments: '210' },
            { title: 'GitOps workflow with ArgoCD', up: '1.1k', comments: '185' },
        ],
        Linux: [
            { title: 'Linux 7.0 kernel changelog', up: '4.2k', comments: '680' },
            { title: 'NixOS for beginners guide', up: '2.0k', comments: '350' },
            { title: 'Best tiling WMs ranked', up: '1.6k', comments: '290' },
        ],
        AI: [
            { title: 'GPT-5 leaked benchmarks', up: '5.8k', comments: '1.2k' },
            { title: 'Open-source LLM comparison', up: '3.4k', comments: '520' },
            { title: 'RAG vs fine-tuning debate', up: '2.1k', comments: '410' },
        ],
    };

    const subNames = Object.keys(mockData);

    subs.forEach((sub, index) => {
        sub.addEventListener('click', () => {
            // Update active state
            subs.forEach((s) => s.classList.remove('mockup__sub--active'));
            sub.classList.add('mockup__sub--active');

            // Update post cards
            const name = subNames[index] || subNames[0];
            const data = mockData[name] || mockData.Python;

            posts.forEach((post, i) => {
                if (!data[i]) return;

                const titleEl = post.querySelector('.mockup__post-title');
                const metaEl = post.querySelector('.mockup__meta');

                if (titleEl) titleEl.textContent = data[i].title;
                if (metaEl) metaEl.textContent = `🔼 ${data[i].up}  💬 ${data[i].comments}`;

                // Re-trigger animation
                post.style.animation = 'none';
                post.offsetHeight; // force reflow
                post.style.animation = `slideInLeft 0.4s ease ${i * 0.1}s backwards`;
            });
        });
    });
}

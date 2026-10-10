// assets/js/footer.js
// Injects the site-wide footer into #footer-placeholder
(function() {
    const footerHTML = `
    <footer class="site-footer">
        <div class="site-footer-inner">
            <a href="/index.html" class="footer-item active">
                <i class="fa-solid fa-house"></i>
                <span>Home</span>
            </a>
            <a href="/courses/index.html" class="footer-item">
                <i class="fa-solid fa-book-open"></i>
                <span>Courses</span>
            </a>
            <a href="/contact.html" class="footer-item">
                <i class="fa-solid fa-envelope"></i>
                <span>Contact</span>
            </a>
            <div class="footer-item">
                <i class="fa-solid fa-circle-user"></i>
                <span>Profile</span>
            </div>
        </div>
    </footer>
    `;

    const placeholder = document.getElementById('footer-placeholder');
    if (placeholder) {
        placeholder.innerHTML = footerHTML;
    }
})();

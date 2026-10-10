// assets/js/footer.js
// Injects the site-wide footer into #footer-placeholder
(function() {
    const footerHTML = `
    <footer class="fixed bottom-0 left-0 right-0 bg-slate-950 border-t border-slate-800 px-8 py-4" style="background: #020617; border-color: #1e293b;">
        <div class="flex justify-between items-center max-w-md mx-auto" style="display: flex; justify-content: space-between; align-items: center; max-width: 28rem; margin: 0 auto;">
            <div class="flex flex-col items-center gap-1 text-blue-500" style="display: flex; flex-direction: column; align-items: center; gap: 0.25rem; color: #3b82f6;">
                <i class="fa-solid fa-house text-xl" style="font-size: 1.25rem;"></i>
                <a href="/index.html"><span class="text-[10px] font-bold uppercase" style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #3b82f6;">Home</span></a>
            </div>
            <div class="flex flex-col items-center gap-1 text-slate-500" style="display: flex; flex-direction: column; align-items: center; gap: 0.25rem; color: #64748b;">
                <i class="fa-solid fa-book-open text-xl" style="font-size: 1.25rem;"></i>
                <a href="/courses/index.html"><span class="text-[10px] font-bold uppercase" style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b;">Courses</span></a>
            </div>
            <div class="flex flex-col items-center gap-1 text-slate-500" style="display: flex; flex-direction: column; align-items: center; gap: 0.25rem; color: #64748b;">
                <i class="fa-solid fa-envelope text-xl" style="font-size: 1.25rem;"></i>
                <a href="/contact.html"><span class="text-[10px] font-bold uppercase" style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b;">Contact</span></a>
            </div>
            <div class="flex flex-col items-center gap-1 text-slate-500" style="display: flex; flex-direction: column; align-items: center; gap: 0.25rem; color: #64748b;">
                <i class="fa-solid fa-circle-user text-xl" style="font-size: 1.25rem;"></i>
                <span class="text-[10px] font-bold uppercase" style="font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b;">Profile</span>
            </div>
        </div>
    </footer>
    `;

    const placeholder = document.getElementById('footer-placeholder');
    if (placeholder) {
        placeholder.innerHTML = footerHTML;
    }
})();

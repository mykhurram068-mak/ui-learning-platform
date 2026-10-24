/* =============================================================
courses.js — shared behavior for /courses/ pages
============================================================= */

/**
• Copy the text content of an element to the clipboard.
• Assumes the button click target has a sibling element with
• the given ID containing the code.
*/
function copyCode(codeId, button) {
var code = document.getElementById(codeId);
if (!code) return;
var text = code.innerText;
navigator.clipboard.writeText(text).then(function() {
var original = button.innerHTML;
button.innerHTML = '✅ Copied';
button.classList.add('copied');
setTimeout(function() {
button.innerHTML = original;
button.classList.remove('copied');
}, 2000);
}).catch(function(err) {
console.error('Copy failed:', err);
});
}

/**
• Switch between OS tab panels (install guide).
• Usage: <button onclick="switchOS('win', this)">Windows</button>
• <div id="os-win" class="os-panel active">...</div>
*/
function switchOS(os, btn) {
document.querySelectorAll('.os-panel').forEach(function(p) {
p.classList.remove('active');
});
document.querySelectorAll('.os-tab').forEach(function(b) {
b.classList.remove('active');
});
var panel = document.getElementById('os-' + os);
if (panel) panel.classList.add('active');
if (btn) btn.classList.add('active');
}
/****************** Toggle Preview Button **************************/
function togglePreview(button) {
var codeBlock = button.closest('.code-block');
if (!codeBlock) return;
var panel = codeBlock.querySelector('.preview-panel');
if (!panel) return;

var isHidden = panel.hasAttribute('hidden');
if (isHidden) {
panel.removeAttribute('hidden');
button.textContent = 'Hide preview';
button.classList.add('active');
} else {
panel.setAttribute('hidden', '');
button.textContent = 'Preview';
button.classList.remove('active');
}
}

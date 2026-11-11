// Android supplies a clipboard and app launcher for the bundled local document.
const send = document.querySelector('a.btn');
send.textContent = '복사하고 ChatGPT 열기 ↗';
send.removeAttribute('target');
send.classList.add('primary');
function handoff(open) {
  if (!Object.keys(templates[active].fields).some(key => drafts[active][key]?.trim())) {
    byId('status').textContent = '내용을 입력하거나 예시를 불러오세요.';
    byId('fields').querySelector('textarea').focus();
    return;
  }
  MobileStudio.handoff(brief(), open);
}
send.onclick = event => { event.preventDefault(); handoff(true); };
byId('copy').onclick = () => handoff(false);
const chosen = Number(localStorage.getItem('studio.lastType') || 0);
if (Number.isInteger(chosen) && templates[chosen]) { active = chosen; show(); }
document.querySelector('nav').addEventListener('click', () => localStorage.setItem('studio.lastType', String(active)));

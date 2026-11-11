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

const clearInputs = document.createElement('button');
clearInputs.type = 'button';
clearInputs.textContent = '내용 다 지우기';
const example = byId('example');
const toolsRow = document.createElement('div');
toolsRow.className = 'actions';
toolsRow.style.margin = '8px 0 14px';
byId('title').after(toolsRow);
toolsRow.append(example, clearInputs);
clearInputs.onclick = () => {
  if (!Object.keys(templates[active].fields).some(key => drafts[active][key])) {
    byId('fields').querySelector('textarea').focus();
    return;
  }
  if (!confirm(templates[active].name + '에 입력한 내용을 모두 지울까요?')) return;
  drafts[active] = {ratio: drafts[active].ratio};
  show();
  byId('fields').querySelector('textarea').focus();
};

const driveHint = document.createElement('p');
driveHint.textContent = '완성 이미지는 ChatGPT에서 이미지 공유 → Drive → 저장을 누르세요.';
byId('brief').parentElement.after(driveHint);

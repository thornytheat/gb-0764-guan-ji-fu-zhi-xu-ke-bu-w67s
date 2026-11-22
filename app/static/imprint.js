const note = document.querySelector('#note');

async function send(address, body) {
  const reply = await fetch(address, {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body),
  });
  const data = await reply.json();
  if (!reply.ok) throw new Error(data.message || '无法保存卷宗');
  return data;
}

function bind(form, work) {
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const trigger = form.querySelector('button');
    trigger.disabled = true;
    note.textContent = '正在核对卷宗…';
    try { await work(form); }
    catch (error) { note.textContent = error.message; }
    finally { trigger.disabled = false; }
  });
}

bind(document.querySelector('#deposit'), async form => {
  const csv = document.querySelector('#rows').value;
  const sample = form.dataset.sample;
  const result = await send('/api/volumes', csv ? {csv} : {sample});
  location.assign('/folio/stamp?' + new URLSearchParams({run:result.run_id, sample}));
});

const select = document.querySelector('#volume');
const output = document.querySelector('#imprint-value');
const file = document.querySelector('#certificate');
const mark = document.querySelector('#paper-stamp');
select?.addEventListener('change', () => {
  if (output) output.value = '';
  if (file) file.hidden = true;
  mark.textContent = '待盖印';
});
bind(document.querySelector('#stamp'), async () => {
  const selected = select.value;
  const record = await send(`/api/volumes/${selected}/stamp`, {});
  if (select.value !== selected) return;
  output.value = record.imprint;
  file.href = `/api/volumes/${selected}/export`;
  file.hidden = false;
  mark.textContent = '已签发';
  note.textContent = record.reused ? '已取回原凭证' : '复制许可凭证已落印';
});
document.querySelector('#print-slip')?.addEventListener('click', () => window.print());

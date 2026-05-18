/**
 * Galgame Studio v0.2.0 - 前端应用逻辑
 * 新增: 模板、i18n、预览、素材扫描、UI提示词、分支选项
 */

const API = {
  async upload(file) {
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch('/api/upload-novel', { method: 'POST', body: fd });
    return res.json();
  },
  async analyze(apiKey, apiBase, model) {
    const fd = new FormData();
    fd.append('api_key', apiKey); fd.append('api_base', apiBase); fd.append('model', model);
    const res = await fetch('/api/analyze', { method: 'POST', body: fd });
    return res.json();
  },
  async generatePrompts(style, templateId) {
    const fd = new FormData();
    fd.append('style', style); fd.append('template_id', templateId || 'none');
    const res = await fetch('/api/generate-prompts', { method: 'POST', body: fd });
    return res.json();
  },
  async exportPrompts() {
    const res = await fetch('/api/export-prompts', { method: 'POST' });
    return res.json();
  },
  async pack(name) {
    const fd = new FormData(); fd.append('project_name', name);
    const res = await fetch('/api/pack', { method: 'POST', body: fd });
    return res.json();
  },
  async getTemplates() {
    const res = await fetch('/api/templates'); return res.json();
  },
  async getI18n(lang) {
    const res = await fetch(`/api/i18n?lang=${lang}`); return res.json();
  },
  async getPreview(sceneIndex) {
    const res = await fetch(`/api/preview?scene_index=${sceneIndex}`); return res.json();
  },
  async scanAssets() {
    const res = await fetch('/api/scan-assets'); return res.json();
  },
  async getStyles() {
    const res = await fetch('/api/styles'); return res.json();
  },
};

// ====== State ======
let currentStep = 1, currentLang = 'zh', scenesData = null, promptsData = null;
let projectDir = null;

// ====== Init ======
document.addEventListener('DOMContentLoaded', () => {
  setupUpload();
  setupAnalyze();
  setupPrompts();
  setupPack();
  setupLang();
  setupStepNav();
  loadTemplates();
  showStep(1);
});

// ====== Clickable Step Navigation ======
function setupStepNav() {
  document.querySelectorAll('.step-indicator').forEach(el => {
    el.style.cursor = 'pointer';
    el.addEventListener('click', () => {
      const step = parseInt(el.dataset.step);
      if (step <= maxAccessibleStep()) {
        showStep(step);
      }
    });
  });
}

function maxAccessibleStep() {
  if (scenesData) return 4;
  if (promptsData) return 4;
  const preview = document.getElementById('novel-preview');
  if (preview && preview.style.display === 'block') return 2;
  return 1;
}

// ====== Step Navigation ======
function showStep(n) {
  currentStep = n;
  document.querySelectorAll('.step-panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.step-indicator').forEach(el => {
    const s = parseInt(el.dataset.step);
    el.classList.remove('active', 'done');
    if (s === n) el.classList.add('active');
    if (s < n) el.classList.add('done');
  });
  const target = document.querySelector(`#step-${stepToId(n)}`);
  if (target) target.classList.add('active');
}
function stepToId(n) { const map = { 1: 'upload', 2: 'analyze', 3: 'prompts', 4: 'pack' }; return map[n] || 'upload'; }

// ====== Toast ======
let toastTimer;
function showToast(msg, duration = 2500) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg; el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), duration);
}
function setStatus(id, type, msg) {
  const el = document.getElementById(id); if (!el) return;
  el.style.display = 'block'; el.className = `status-msg ${type}`;
  el.innerHTML = (type === 'loading') ? `<span class="spinner"></span> ${msg}` : msg;
}
function hideStatus(id) { const el = document.getElementById(id); if (el) el.style.display = 'none'; }

// ====== Language ======
function setupLang() {
  const sel = document.getElementById('lang-select');
  sel.addEventListener('change', () => {
    currentLang = sel.value;
    applyI18n();
  });
}
async function applyI18n() {
  try {
    const res = await API.getI18n(currentLang);
    const s = res.strings;
    // Only apply translations exposed through data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.dataset.i18n;
      if (s[key]) el.textContent = s[key];
    });
  } catch(e) { console.warn('i18n load failed', e); }
}

// ====== Templates ======
async function loadTemplates() {
  try {
    const res = await API.getTemplates();
    if (!res.templates || !res.templates.length) {
      console.warn('Templates: empty response', res);
      return;
    }
    const sel = document.getElementById('template-select');
    if (!sel) { console.warn('Templates: select not found'); return; }
    res.templates.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = t.icon + ' ' + t.name_cn + ' - ' + t.description_cn;
      sel.appendChild(opt);
    });
    console.log('Templates loaded:', res.templates.length);
  } catch(e) {
    console.error('Template load error:', e);
    const sel = document.getElementById('template-select');
    if (sel) {
      const opt = document.createElement('option');
      opt.value = 'error';
      opt.textContent = '⚠️ 模板加载失败 - 检查服务器';
      sel.appendChild(opt);
    }
  }
}

// ====== STEP 1: Upload ======
function setupUpload() {
  const area = document.getElementById('upload-area');
  const input = document.getElementById('file-input');
  area.addEventListener('click', () => input.click());
  area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('drag-over'); });
  area.addEventListener('dragleave', () => area.classList.remove('drag-over'));
  area.addEventListener('drop', e => {
    e.preventDefault(); area.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });
  input.addEventListener('change', () => { if (input.files[0]) handleFile(input.files[0]); });
}

async function handleFile(file) {
  setStatus('upload-status', 'loading', '正在读取小说...');
  try {
    const res = await API.upload(file);
    if (!res.success) throw new Error(res.detail || '上传失败');
    const preview = document.getElementById('novel-preview');
    document.getElementById('preview-title').textContent = res.novel.title;
    document.getElementById('preview-info').textContent = `${res.novel.word_count}字 · ${res.novel.chapter_count}章`;
    document.getElementById('preview-text').textContent = res.novel.preview;
    document.getElementById('preview-stats').textContent =
      `📄 ${res.novel.filename}  |  📝 ${res.novel.word_count.toLocaleString()} 字  |  📑 ${res.novel.chapter_count} 个章节`;
    preview.style.display = 'block';
    setStatus('upload-status', 'success', '✅ 小说已就绪，进入下一步');
    document.getElementById('upload-area').style.display = 'none';
    setTimeout(() => showStep(2), 300);
  } catch (err) { setStatus('upload-status', 'error', `❌ ${err.message}`); }
}

// ====== STEP 2: Analyze ======
function setupAnalyze() {
  document.getElementById('btn-analyze').addEventListener('click', doAnalyze);

  const modelSelect = document.getElementById('model-select');
  const apiBaseInput = document.getElementById('api-base');
  const customField = document.getElementById('custom-model-field');

  // API地址自动切换
  modelSelect.addEventListener('change', function() {
    const selected = this.options[this.selectedIndex];
    const apiBase = selected.dataset.apiBase;
    customField.style.display = this.value === 'custom' ? 'flex' : 'none';
    if (apiBase) {
      apiBaseInput.value = apiBase;
    }
  });
}

async function doAnalyze() {
  const apiKey = document.getElementById('api-key').value.trim();
  const apiBase = document.getElementById('api-base').value.trim();
  let model = document.getElementById('model-select').value;
  if (model === 'custom') {
    model = document.getElementById('custom-model').value.trim();
    if (!model) { setStatus('analyze-status', 'error', '❌ 请输入自定义模型名称'); return; }
  }
  if (!apiKey) { setStatus('analyze-status', 'error', '❌ 请输入 API Key'); return; }

  const btn = document.getElementById('btn-analyze'); btn.disabled = true;
  setStatus('analyze-status', 'loading', 'AI正在分析小说，大段文本可能需要1-3分钟...');

  try {
    const res = await API.analyze(apiKey, apiBase, model);
    if (!res.success) throw new Error(res.detail || '分析失败');
    scenesData = res.scenes;
    const choiceCount = res.choice_scene_count || 0;
    setStatus('analyze-status', 'success',
      `✅ 分析完成！${res.scene_count}个场景 · ${res.summary.character_count}个角色${choiceCount>0 ? ' · '+choiceCount+'个分支点' : ''}`);
    renderSceneList(res.scenes);
    showStep(3);
  } catch (err) { setStatus('analyze-status', 'error', `❌ ${err.message}`); }
  finally { btn.disabled = false; }
}

function renderSceneList(scenes) {
  const container = document.getElementById('scene-list-container');
  const list = document.getElementById('scene-list');
  const count = document.getElementById('scene-count');
  container.style.display = 'block';
  count.textContent = `${scenes.length} 个场景`;

  list.innerHTML = scenes.map(s => {
    const hasChoices = s.choices && s.choices.length > 0;
    return `
    <div class="scene-card">
      <div class="scene-card-header">
        <span class="scene-card-id">${s.scene_id}</span>
        <span class="scene-card-title">${s.scene_title}</span>
        <span class="scene-card-meta-right">
          ${hasChoices ? '<span class="choice-badge">🔀 ' + s.choices.length + '选项</span>' : ''}
          <span style="font-size:0.75rem;color:var(--text-muted);margin-left:0.5rem;">${s.lines?.length || 0}句</span>
        </span>
      </div>
      <div class="scene-card-meta">
        <span>📍 ${s.location}</span>
        <span>🕐 ${s.time}</span>
        <span>🎭 ${s.mood}</span>
      </div>
    </div>`;
  }).join('');
}

// ====== STEP 3: Prompts ======
function setupPrompts() {
  document.getElementById('btn-generate-prompts').addEventListener('click', doGeneratePrompts);
  document.getElementById('btn-export-prompts').addEventListener('click', doExportPrompts);

  // Step 3 里的打包按钮
  const packBtn3 = document.getElementById('btn-pack-from-step3');
  if (packBtn3) packBtn3.addEventListener('click', () => doPackFromStep3());
  const scanBtn = document.getElementById('btn-scan-dir');
  if (scanBtn) scanBtn.addEventListener('click', () => doScanAssetDir());
  const clearBtn = document.getElementById('btn-clear-staging');
  if (clearBtn) clearBtn.addEventListener('click', () => doClearStaging());

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    });
  });
}

async function doGeneratePrompts() {
  const style = document.getElementById('style-select').value;
  const templateId = document.getElementById('template-select').value;
  const btn = document.getElementById('btn-generate-prompts'); btn.disabled = true;
  setStatus('prompts-status', 'loading', '正在生成提示词...');

  try {
    const res = await API.generatePrompts(style, templateId);
    if (!res.success) throw new Error(res.detail || '生成失败');
    promptsData = res.prompts;
    setStatus('prompts-status', 'success', `✅ 提示词已生成！画风：${res.style_name}`);
    document.getElementById('btn-export-prompts').style.display = 'inline-flex';
    document.getElementById('prompts-container').style.display = 'block';
    renderPrompts(res.prompts);
    // 刷新导入状态
    setTimeout(refreshImportStatus, 500);
    // 停留在第3步，用户可以查看提示词；手动点击到第4步
  } catch (err) { setStatus('prompts-status', 'error', `❌ ${err.message}`); }
  finally { btn.disabled = false; }
}

function renderPrompts(prompts) {
  renderCharacters(prompts.characters);
  renderBackgrounds(prompts.backgrounds);
  renderCGs(prompts.cgs);
  renderUI(prompts.ui);
  renderBGM(prompts.bgm);
  renderVoice(prompts.voice);
  renderTools(prompts.tool_recommendations);
}

function renderCharacters(chars) {
  const el = document.getElementById('tab-characters');
  const html = chars.map(c => `
    <div class="prompt-card">
      <div class="prompt-card-header" onclick="this.parentElement.classList.toggle('expanded')">
        <div>
          <div class="prompt-card-title">${c.character_name} <span style="font-size:0.75rem;color:var(--text-muted);">${c.role}</span></div>
          <div class="prompt-card-detail">${escHtml(c.appearance.substring(0, 60))}${c.appearance.length > 60 ? '...' : ''}</div>
        </div>
        <span style="font-size:0.85rem;">${c.total_sprites} 个表情</span>
      </div>
      <div class="prompt-card-body">
        ${c.sprites.map(s => `
          <div class="prompt-field">
            <label>${s.expression} — ${s.filename_template}</label>
            <textarea readonly>${escHtml(s.prompt)}</textarea>
            <div class="prompt-actions">
              <button class="copy-btn" onclick="copyPrompt(this, '${escapeAttr(s.prompt)}'); return false;">📋 复制提示词</button>
              <button class="import-btn" data-type="character_sprite" data-label="${escapeAttr(c.character_name + '_' + s.expression)}" data-filename="${s.filename_template}">📤 导入素材</button>
              <input type="file" accept=".png,.jpg,.jpeg,.webp" class="import-input" style="display:none;"
                data-type="character_sprite" data-label="${escapeAttr(c.character_name + '_' + s.expression)}" data-filename="${s.filename_template}">
            </div>
          </div>
        `).join('')}
      </div>
    </div>`).join('');
  el.innerHTML = html;
  attachImportHandlers(el);
}

function renderBackgrounds(bgs) {
  const el = document.getElementById('tab-backgrounds');
  const html = bgs.map(bg => `
    <div class="prompt-card">
      <div class="prompt-card-header" onclick="this.parentElement.classList.toggle('expanded')">
        <div><div class="prompt-card-title">${bg.location}</div><div class="prompt-card-detail">用于 ${bg.used_in_scenes.length} 个场景</div></div>
      </div>
      <div class="prompt-card-body">
        <div class="prompt-field"><label>正面提示词 — ${bg.filename_template}</label><textarea readonly>${escHtml(bg.prompt)}</textarea>
          <div class="prompt-actions">
            <button class="copy-btn" onclick="copyPrompt(this, '${escapeAttr(bg.prompt)}'); return false;">📋 复制提示词</button>
            <button class="import-btn" data-type="background" data-label="${escapeAttr(bg.location)}" data-filename="${bg.filename_template}">📤 导入素材</button>
            <input type="file" accept=".png,.jpg,.jpeg,.webp" class="import-input" style="display:none;"
              data-type="background" data-label="${escapeAttr(bg.location)}" data-filename="${bg.filename_template}">
          </div></div>
        <div class="prompt-field"><label>负面提示词</label><textarea readonly>${escHtml(bg.negative_prompt)}</textarea>
          <button class="copy-btn" onclick="copyPrompt(this, '${escapeAttr(bg.negative_prompt)}'); return false;">📋 复制负面词</button></div>
      </div>
    </div>`).join('');
  el.innerHTML = html;
  attachImportHandlers(el);
}

function renderCGs(cgs) {
  const el = document.getElementById('tab-cgs');
  if (!cgs || cgs.length === 0) {
    el.innerHTML = '<p style="color:var(--text-muted);padding:1rem;">暂无事件CG建议</p>'; return;
  }
  const html = cgs.map(cg => `
    <div class="prompt-card">
      <div class="prompt-card-header" onclick="this.parentElement.classList.toggle('expanded')">
        <div><div class="prompt-card-title">${cg.cg_id} — ${cg.scene_title}</div><div class="prompt-card-detail">${escHtml(cg.description.substring(0, 80))}...</div></div>
      </div>
      <div class="prompt-card-body">
        <div class="prompt-field"><label>CG提示词 — ${cg.filename_template}</label><textarea readonly>${escHtml(cg.prompt)}</textarea>
          <div class="prompt-actions">
            <button class="copy-btn" onclick="copyPrompt(this, '${escapeAttr(cg.prompt)}'); return false;">📋 复制提示词</button>
            <button class="import-btn" data-type="cg" data-label="${escapeAttr(cg.cg_id)}" data-filename="${cg.filename_template}">📤 导入素材</button>
            <input type="file" accept=".png,.jpg,.jpeg,.webp" class="import-input" style="display:none;"
              data-type="cg" data-label="${escapeAttr(cg.cg_id)}" data-filename="${cg.filename_template}">
          </div></div>
      </div>
    </div>`).join('');
  el.innerHTML = html;
  attachImportHandlers(el);
}

function renderUI(ui) {
  const el = document.getElementById('tab-ui');
  if (!ui) { el.innerHTML = '<p style="color:var(--text-muted);padding:1rem;">暂无UI提示词</p>'; return; }

  let html = '';
  if (ui.guide) html += `<div class="guide-content" style="margin-bottom:1.5rem;">${ui.guide.replace(/\n/g, '<br>')}</div>`;

  const sections = ['title_screen', 'game_logo', 'textbox', 'namebox', 'choice_buttons'];
  const labels = { title_screen: '标题画面背景', game_logo: '游戏Logo', textbox: '对话框', namebox: '名字框', choice_buttons: '选项按钮' };
  const icons = { title_screen: '🖼️', game_logo: '✨', textbox: '💬', namebox: '🏷️', choice_buttons: '🔘' };

  sections.forEach(key => {
    const item = ui[key];
    if (!item) return;
    html += `
    <div class="prompt-card expanded">
      <div class="prompt-card-header">
        <div class="prompt-card-title">${icons[key] || ''} ${labels[key] || key} — ${item.filename}</div>
      </div>
      <div class="prompt-card-body">
        ${item.notes ? `<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:0.5rem;">${item.notes}</p>` : ''}
        <div class="prompt-field"><label>提示词</label><textarea readonly>${escHtml(item.prompt)}</textarea>
          <div class="prompt-actions">
            <button class="copy-btn" onclick="copyPrompt(this, '${escapeAttr(item.prompt)}'); return false;">📋 复制提示词</button>
            <button class="import-btn" data-type="ui" data-label="${escapeAttr(key)}" data-filename="${item.filename}">📤 导入素材</button>
            <input type="file" accept=".png,.jpg,.jpeg,.webp" class="import-input" style="display:none;"
              data-type="ui" data-label="${escapeAttr(key)}" data-filename="${item.filename}">
          </div></div>
        ${item.guide ? `<div class="guide-content" style="margin-top:0.5rem;">${item.guide.replace(/\n/g, '<br>')}</div>` : ''}
      </div>
    </div>`;
  });

  el.innerHTML = html;
  attachImportHandlers(el);
}

function renderBGM(bgm) {
  const el = document.getElementById('tab-bgm');
  let html = '';
  if (bgm.guide) html += `<div class="guide-content" style="margin-bottom:1.5rem;">${bgm.guide.replace(/\n/g, '<br>')}</div>`;
  html += bgm.bgm_tracks.map(t => `
    <div class="guide-card">
      <h4>${t.style_cn} <span style="font-size:0.75rem;color:var(--text-muted);">${t.mood}</span></h4>
      <div class="meta">用于 ${t.scene_count} 个场景 | Suno风格: ${t.suno_genre}</div>
      <div class="prompt-box">${t.ai_prompt}</div>
      <div class="prompt-actions">
        <button class="copy-btn" onclick="copyPrompt(this, '${escapeAttr(t.ai_prompt)}'); return false;">📋 复制到Suno</button>
        <button class="import-btn" data-type="bgm" data-label="${escapeAttr(t.mood)}" data-filename="${t.filename_template}">📤 导入BGM</button>
        <input type="file" accept=".mp3,.ogg,.wav,.opus" class="import-input" style="display:none;"
          data-type="bgm" data-label="${escapeAttr(t.mood)}" data-filename="${t.filename_template}">
      </div>
      <div style="margin-top:0.5rem;font-size:0.8rem;color:var(--text-muted);">${t.recommendation}</div>
    </div>`).join('');
  el.innerHTML = html;
  attachImportHandlers(el);
}

function renderVoice(voice) {
  const el = document.getElementById('tab-voice');
  let html = '';
  if (voice.guide) html += `<div class="guide-content" style="margin-bottom:1.5rem;">${voice.guide.replace(/\n/g, '<br>')}</div>`;
  html += voice.characters.map(c => `
    <div class="guide-card">
      <h4>${c.name} (${c.role})</h4><div class="meta">${c.character_traits}</div>
      <div style="margin:0.5rem 0;">
        <strong style="color:var(--accent-teal);">方案A: ${c.solution_a.name}</strong>
        <ol class="steps" style="margin-top:0.25rem;">${c.solution_a.steps.map(s => `<li>${s}</li>`).join('')}</ol>
      </div>
      <div style="margin:0.5rem 0;">
        <strong style="color:var(--accent-blue);">方案B: ${c.solution_b.name}</strong>
        <ol class="steps" style="margin-top:0.25rem;">${c.solution_b.steps.map(s => `<li>${s}</li>`).join('')}</ol>
      </div>
    </div>`).join('');
  el.innerHTML = html;
}

function renderTools(tools) {
  const el = document.getElementById('tab-tools');
  if (!tools) { el.innerHTML = '<p style="color:var(--text-muted);padding:1rem;">暂无工具推荐</p>'; return; }

  let html = '<div class="guide-content" style="margin-bottom:1.5rem;">## 每个类别的AI工具推荐，付费和免费方案都有</div>';

  const categories = ['image_generation', 'bgm_generation', 'voice_generation'];

  categories.forEach(cat => {
    const data = tools[cat];
    if (!data) return;
    html += `<h3 style="color:var(--accent-gold);margin-bottom:0.75rem;">${data.title}</h3>`;

    // 付费
    if (data.paid && data.paid.length) {
      html += '<div style="margin-bottom:0.5rem;"><strong style="color:var(--warning);">💰 付费方案</strong></div>';
      data.paid.forEach(t => {
        html += `<div class="guide-card" style="border-left:3px solid var(--warning);">
          <h4>${t.name} <span style="font-size:0.75rem;color:var(--warning);">${t.price}</span></h4>
          <div class="meta">最适合: ${t.best_for}</div>
          <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.3rem;">${t.pros || ''} ${t.cons ? '| ⚠ '+ t.cons : ''}</div>
          ${t.url ? `<div style="font-size:0.75rem;color:var(--accent-blue);margin-top:0.2rem;">🔗 ${t.url}</div>` : ''}
        </div>`;
      });
    }

    // 免费
    if (data.free && data.free.length) {
      html += '<div style="margin-bottom:0.5rem;margin-top:1rem;"><strong style="color:var(--success);">🆓 免费方案</strong></div>';
      data.free.forEach(t => {
        html += `<div class="guide-card" style="border-left:3px solid var(--success);">
          <h4>${t.name} <span style="font-size:0.75rem;color:var(--success);">${t.price}</span></h4>
          <div class="meta">最适合: ${t.best_for}</div>
          <div style="font-size:0.8rem;color:var(--text-secondary);margin-top:0.3rem;">${t.pros || ''} ${t.cons ? '| ⚠ '+ t.cons : ''}</div>
          ${t.guide ? `<div style="font-size:0.8rem;color:var(--accent-teal);margin-top:0.2rem;">💡 ${t.guide}</div>` : ''}
          ${t.url ? `<div style="font-size:0.75rem;color:var(--accent-blue);margin-top:0.2rem;">🔗 ${t.url}</div>` : ''}
        </div>`;
      });
    }

    // 总建议
    if (data.guide) {
      html += `<div class="status-msg loading" style="margin-top:0.75rem;">💡 ${data.guide}</div>`;
    }

    // 背景去除工具 (特殊处理)
    if (data.bg_removal && data.bg_removal.length) {
      html += '<div style="margin-bottom:0.5rem;margin-top:1rem;"><strong style="color:var(--accent-rose);">🔪 背景去除工具（立绘透明化必备！）</strong></div>';
      data.bg_removal.forEach(t => {
        html += `<div class="guide-card" style="border-left:3px solid var(--accent-rose);">
          <h4>${t.name} <span style="font-size:0.75rem;color:var(--accent-rose);">${t.price}</span></h4>
          <div class="meta">${t.best_for}</div>
          ${t.guide ? `<div style="font-size:0.8rem;color:var(--accent-teal);margin-top:0.2rem;">💡 ${t.guide}</div>` : ''}
          ${t.url ? `<div style="font-size:0.75rem;color:var(--accent-blue);margin-top:0.2rem;">🔗 ${t.url}</div>` : ''}
        </div>`;
      });
    }
  });

  el.innerHTML = html;
}

async function doExportPrompts() {
  try {
    const res = await API.exportPrompts();
    if (res.success) showToast('✅ 提示词已导出为 Markdown 文件到 output 目录');
  } catch (err) { showToast('❌ 导出失败'); }
}

async function doPackFromStep3() {
  // 打包并跳到第4步
  const name = document.getElementById('project-name-v3').value.trim() || 'MyVisualNovel';
  const assetDir = document.getElementById('asset-dir').value.trim();

  showStep(4);
  document.getElementById('project-name').value = name;
  if (assetDir) {
    // 先复制素材
    setStatus('pack-status', 'loading', '正在复制素材并打包...');
  }
  
  try {
    const fd = new FormData();
    fd.append('project_name', name);
    const res = await fetch('/api/pack', { method: 'POST', body: fd });
    const data = await res.json();
    if (!data.success) throw new Error(data.detail || '打包失败');
    projectDir = data.project_dir;
    setStatus('pack-status', 'success', `✅ Ren'Py 项目已生成！\n📂 ${data.project_dir}`);
    document.getElementById('btn-scan-assets').style.display = 'inline-flex';
    showToast('🎮 Ren\'Py 项目生成成功！', 4000);
  } catch (err) {
    setStatus('pack-status', 'error', `❌ ${err.message}`);
  }
}

async function doScanAssetDir() {
  const dir = document.getElementById('asset-dir').value.trim();
  if (!dir) { showToast('⚠️ 先输入素材目录路径'); return; }

  try {
    const fd = new FormData(); fd.append('path', dir);
    const res = await fetch('/api/scan-directory', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
      showToast(`📊 找到 ${data.scan.total_images} 张图 + ${data.scan.total_audio} 个音频`, 3000);
    }
  } catch (err) { showToast('❌ 扫描失败'); }
}

async function doClearStaging() {
  if (!confirm('确定清空所有已导入的素材？此操作不可撤销。')) return;
  try {
    const res = await fetch('/api/clear-staging', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      // 重置所有导入按钮
      document.querySelectorAll('.import-btn.imported').forEach(btn => {
        btn.textContent = '📤 导入素材';
        btn.className = 'import-btn';
      });
      showToast('🗑️ 已清空所有导入素材', 2000);
    }
  } catch (err) { showToast('❌ 清理失败'); }
}

// ====== STEP 4: Pack ======
function setupPack() {
  document.getElementById('btn-pack').addEventListener('click', doPack);
  document.getElementById('btn-preview').addEventListener('click', openPreview);
  document.getElementById('btn-scan-assets').addEventListener('click', doScanAssets);
  document.getElementById('btn-auto-sort').addEventListener('click', doAutoSort);
  document.getElementById('btn-refresh-assets').addEventListener('click', refreshAssetPanel);
}

async function doPack() {
  const name = document.getElementById('project-name').value.trim() || 'MyVisualNovel';
  const btn = document.getElementById('btn-pack'); btn.disabled = true;
  setStatus('pack-status', 'loading', '正在生成Ren\'Py项目...');

  try {
    const res = await API.pack(name);
    if (!res.success) throw new Error(res.detail || '打包失败');
    projectDir = res.project_dir;
    setStatus('pack-status', 'success', `✅ Ren'Py 项目已生成！\n📂 ${res.project_dir}`);
    document.getElementById('btn-scan-assets').style.display = 'inline-flex';
    showToast('🎮 Ren\'Py 项目生成成功！', 4000);
    // 显示素材管理面板
    setTimeout(() => refreshAssetPanel(), 500);
  } catch (err) { setStatus('pack-status', 'error', `❌ ${err.message}`); }
  finally { btn.disabled = false; }
}

function openPreview() {
  if (!scenesData) { showToast('⚠️ 请先完成场景分析'); return; }
  window.open('/preview', '_blank');
}

async function doScanAssets() {
  const resultDiv = document.getElementById('asset-scan-result');
  resultDiv.style.display = 'block';
  resultDiv.innerHTML = '<div class="status-msg loading"><span class="spinner"></span> 正在扫描素材...</div>';

  try {
    const res = await API.scanAssets();
    const scan = res.scan;
    const pct = scan.completion_pct || 0;

    let html = `<div class="status-msg ${pct >= 100 ? 'success' : pct > 0 ? 'loading' : 'error'}">`;
    html += `📊 素材完整度: <strong>${pct}%</strong> (${scan.present}/${scan.total_required})</div>`;

    // Progress bar
    html += `<div class="progress-bar"><div class="progress-fill" style="width:${pct}%;background:${pct>=100?'var(--success)':pct>50?'var(--warning)':'var(--error)'};"></div></div>`;

    if (scan.missing_list && scan.missing_list.length > 0) {
      html += '<div style="margin-top:0.75rem;"><strong style="color:var(--error);">缺失素材:</strong>';
      html += '<ul style="font-size:0.8rem;color:var(--text-muted);margin-top:0.25rem;padding-left:1.2rem;">';
      scan.missing_list.slice(0, 20).forEach(m => { html += `<li>${m}</li>`; });
      if (scan.missing_list.length > 20) html += `<li>...还有 ${scan.missing_list.length - 20} 项</li>`;
      html += '</ul></div>';
    }

    resultDiv.innerHTML = html;
  } catch (err) { resultDiv.innerHTML = `<div class="status-msg error">❌ ${err.message}</div>`; }
}

// ====== Utilities ======
function copyPrompt(btn, text) {
  navigator.clipboard.writeText(text).then(() => {
    btn.classList.add('copied'); btn.innerHTML = '✅ 已复制';
    setTimeout(() => { btn.classList.remove('copied'); btn.innerHTML = '📋 复制提示词'; }, 1500);
  }).catch(() => {
    const ta = document.createElement('textarea'); ta.value = text;
    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
    btn.classList.add('copied'); btn.innerHTML = '✅ 已复制';
    setTimeout(() => { btn.classList.remove('copied'); btn.innerHTML = '📋 复制提示词'; }, 1500);
  });
}
function escapeAttr(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\n/g, '\\n');
}

function escHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ====== 素材导入按钮 ======

function attachImportHandlers(container) {
  if (!container) return;
  container.querySelectorAll('.import-btn').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      const input = this.parentElement.querySelector('.import-input');
      if (input) input.click();
    });
  });
  container.querySelectorAll('.import-input').forEach(input => {
    input.addEventListener('change', async function() {
      if (!this.files || !this.files[0]) return;
      const file = this.files[0];
      const btn = this.parentElement.querySelector('.import-btn');
      const type = this.dataset.type;
      const label = this.dataset.label;
      const filename = this.dataset.filename;

      if (btn) {
        btn.textContent = '⏳ 导入中...';
        btn.disabled = true;
      }

      try {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('asset_type', type);
        fd.append('asset_label', label);
        fd.append('filename', filename);
        const res = await fetch('/api/import-asset', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
          const msg = data.overwritten ? `🔄 已覆盖: ${data.filename}` : `✅ 已导入: ${data.filename}`;
          if (btn) {
            btn.textContent = '✅ 已导入';
            btn.className = 'import-btn imported';
          }
          showToast(msg, 2000);
        } else {
          throw new Error(data.detail || '导入失败');
        }
      } catch (err) {
        if (btn) {
          btn.textContent = '📤 导入素材';
          btn.className = 'import-btn';
          btn.disabled = false;
        }
        showToast(`❌ ${err.message}`, 3000);
      }
    });
  });
}

// 页面加载时，检查已导入素材并标记
async function refreshImportStatus() {
  try {
    const res = await fetch('/api/imported-assets');
    const data = await res.json();
    if (!data.success) return;
    const assets = data.assets;
    // 遍历所有已导入的素材，标记对应按钮
    document.querySelectorAll('.import-btn').forEach(btn => {
      const type = btn.dataset.type;
      const filename = btn.dataset.filename;
      const typeAssets = assets[type] || [];
      if (typeAssets.some(f => f.startsWith(filename.replace(/\.[^.]+$/, '')))) {
        btn.textContent = '✅ 已导入';
        btn.className = 'import-btn imported';
      }
    });
  } catch (e) { /* ignore */ }
}

// ====== 素材管理面板 ======

const CATEGORY_ICONS = {
  background: '🖼️', character_sprite: '👤', cg: '🎬', ui: '🖥️', bgm: '🎵', sfx: '🔊', voice: '🎙️',
};
const CATEGORY_NAMES = {
  background: '背景', character_sprite: '角色立绘', cg: '事件CG', ui: 'UI素材', bgm: 'BGM', sfx: '音效', voice: '配音',
};

async function refreshAssetPanel() {
  const panel = document.getElementById('asset-manager');
  const grid = document.getElementById('asset-category-grid');
  const count = document.getElementById('asset-count');
  if (!panel || !grid) return;

  try {
    const res = await fetch('/api/imported-assets');
    const data = await res.json();
    if (!data.success) return;

    const assets = data.assets;
    let total = 0;
    const categories = Object.entries(assets).filter(([_, files]) => files.length > 0);
    categories.forEach(([_, files]) => total += files.length);

    if (total === 0) {
      panel.style.display = 'none';
      return;
    }

    panel.style.display = 'block';
    count.textContent = `${total} 个文件`;

    let html = '';
    categories.forEach(([type, files]) => {
      const icon = CATEGORY_ICONS[type] || '📁';
      const name = CATEGORY_NAMES[type] || type;
      html += `<div class="asset-category">
        <div class="asset-category-header">
          <span>${icon} ${name}</span>
          <span class="badge">${files.length}</span>
        </div>
        <div class="asset-file-list">`;
      files.forEach(f => {
        html += `<span class="asset-tag" title="${escHtml(f)}">${escHtml(f.length > 28 ? f.substring(0, 25) + '...' : f)}</span>`;
      });
      html += `</div></div>`;
    });
    grid.innerHTML = html;
  } catch (e) {
    console.warn('Asset panel refresh failed', e);
  }
}

async function doAutoSort() {
  const name = document.getElementById('project-name').value.trim() || 'MyVisualNovel';
  const btn = document.getElementById('btn-auto-sort');
  const resultDiv = document.getElementById('sort-result');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 归类中...';

  try {
    const fd = new FormData();
    fd.append('project_name', name);
    const res = await fetch('/api/auto-sort', { method: 'POST', body: fd });
    const data = await res.json();
    if (!data.success) throw new Error(data.message || '归类失败');

    // 显示归类树
    let html = `<div class="status-msg success">✅ ${data.message}</div>`;
    if (data.tree) {
      html += '<div class="tree-view" style="margin-top:0.75rem;">';
      data.tree.forEach(node => {
        if (node.count > 0) {
          html += `<details><summary><strong>📂 ${node.dir}/</strong> <span class="badge">${node.count} 文件</span></summary>`;
          html += '<ul style="font-size:0.78rem;color:var(--text-muted);margin:0.3rem 0 0 1rem;padding:0;">';
          node.files.forEach(f => { html += `<li>${escHtml(f)}</li>`; });
          html += '</ul></details>';
        }
      });
      html += '</div>';
    }
    resultDiv.innerHTML = html;
    showToast(`✅ 已归类 ${data.sorted} 个文件`, 3000);
  } catch (err) {
    resultDiv.innerHTML = `<div class="status-msg error">❌ ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🔄</span> 一键归类到项目';
  }
}

document.addEventListener('DOMContentLoaded', () => {
    const sendButton = document.getElementById('sendButton');
    const rulesContent = document.getElementById('rulesContent');
    const resultBody = document.getElementById('resultBody');
    const statusBadge = document.getElementById('statusBadge');
    const statusIcon = document.getElementById('statusIcon');
    const buttonText = document.getElementById('buttonText');
    const buttonIcon = document.getElementById('buttonIcon');

    // File upload elements
    const uploadRulesBtn = document.getElementById('uploadRulesBtn');
    const rulesFileInput = document.getElementById('rulesFileInput');
    const uploadDataBtn = document.getElementById('uploadDataBtn');
    const dataFileInput = document.getElementById('dataFileInput');
    const savedPlansSelect = document.getElementById('savedPlansSelect');
    const loadPlanBtn = document.getElementById('loadPlanBtn');
    const runCheckBtn = document.getElementById('runCheckBtn');
    const addFieldBtn = document.getElementById('addFieldBtn');
    const dataFieldsContainer = document.getElementById('dataFields');

    // Modal elements
    const approvalModal = document.getElementById('approvalModal');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const planEditor = document.getElementById('planEditor');
    const planBlocksContainer = document.getElementById('planBlocksContainer');
    const savePlanAsBtn = document.getElementById('savePlanAsBtn');
    const proceedToMappingBtn = document.getElementById('proceedToMappingBtn');

    // Mapping Modal elements
    const mappingModal = document.getElementById('mappingModal');
    const closeMappingModalBtn = document.getElementById('closeMappingModalBtn');
    const mappingContainer = document.getElementById('mappingContainer');
    const confirmMappingBtn = document.getElementById('confirmMappingBtn');

    let currentPlan = null;
    let currentMapping = null;

    // --- Init Default Fields (Dữ liệu mẫu từ VanbanA.txt) ---
    const defaultFields = {
        "Số hợp đồng": "NH-2026-XDF",
        "Ngày ký": "02-04-2026",
        "Tên khách hàng": "Lê Minh",
        "Ngày tháng năm sinh": "15-11-1999",
        "CCCD ": "001095000123",
        "Trạng thái": "Đang duyệt",
        "Ngày hết hạn": "02-06-2026",
        "Lãi suất": "10.5",
        "Người đại diện": "Nguyễn Văn A",
        "Cơ quan ban hành": "Ngân hàng Việt Nam",
        "Chữ ký": "ABC",
        "Phương thức giải ngân": "Giải ngân một lần"
    };

    // Định nghĩa hàm trước khi gọi
    function fillDataFields(data) {
        dataFieldsContainer.innerHTML = '';
        Object.entries(data).forEach(([key, value]) => {
            dataFieldsContainer.appendChild(createDataRow(key, value));
        });
    }

    function createDataRow(key, value) {
        const index = dataFieldsContainer.querySelectorAll('.data-row').length + 1;
        const row = document.createElement('div');
        row.className = 'grid grid-cols-[1fr,1fr,40px] gap-3 group relative data-row items-center';
        row.innerHTML = `
            <div class="absolute -left-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-muted-foreground/30 opacity-0 group-hover:opacity-100 transition-opacity">${index.toString().padStart(2, '0')}</div>
            <input placeholder="Tên trường..." class="field-key w-full bg-background border border-border/50 rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50 transition-all" value="${key}">
            <input placeholder="Giá trị..." class="field-value w-full bg-background border border-border/50 rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 focus:border-emerald-500/50 transition-all" value="${value}">
            <button class="remove-row-btn p-1.5 rounded-lg hover:bg-rose-500/10 text-rose-500/50 hover:text-rose-500 transition-all opacity-0 group-hover:opacity-100" title="Xóa trường này">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
            </button>
        `;
        row.querySelector('.remove-row-btn').addEventListener('click', () => { row.remove(); updateRowIndices(); });
        return row;
    }

    function updateRowIndices() {
        document.querySelectorAll('.data-row').forEach((r, i) => {
            const idxDiv = r.querySelector('div');
            if (idxDiv) idxDiv.innerText = (i + 1).toString().padStart(2, '0');
        });
    }

    // Nạp dữ liệu mẫu ngay lập tức
    fillDataFields(defaultFields);
    statusBadge.innerText = 'Dữ liệu mẫu đã sẵn sàng';

    // --- UI Helper Functions ---
    function renderPlanBlocks(plan, metadata = {}) {
        planBlocksContainer.innerHTML = '';

        if (!plan || Object.keys(plan).length === 0) {
            planBlocksContainer.innerHTML = '<p class="text-sm text-muted-foreground italic text-center py-4">Không có quy tắc nào được định nghĩa.</p>';
            return;
        }

        Object.entries(plan).forEach(([field, rules]) => {
            const rulesArray = Array.isArray(rules) ? rules : [rules];
            const hasRules = rulesArray.length > 0;

            const block = document.createElement('div');
            block.className = `plan-block p-4 border rounded-xl flex flex-col gap-3 transition-all hover:bg-white/[0.07] ${hasRules ? 'bg-white/5 border-white/10' : 'bg-blue-500/[0.03] border-blue-500/20'}`;
            block.dataset.field = field;

            let rulesHtml = '';
            if (hasRules) {
                rulesArray.forEach(rule => {
                    rulesHtml += `
                        <div class="rule-item flex items-center gap-2 group/rule">
                            <div class="w-1.5 h-1.5 rounded-full bg-emerald-500/40 group-hover/rule:bg-emerald-500 transition-colors"></div>
                            <input type="text" class="rule-input flex-1 bg-black/20 border border-white/5 rounded-lg px-3 py-1.5 text-xs font-mono text-emerald-400 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all" value="${rule.replace(/"/g, '&quot;')}" placeholder="Tên hàm helper...">
                        </div>
                    `;
                });
            } else {
                rulesHtml = `
                    <div class="p-3 rounded-lg bg-blue-500/5 border border-blue-500/10 text-[11px] text-blue-400/70 italic flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                        Trường dữ liệu đầu vào (Biến phụ thuộc)
                    </div>
                `;
            }

            const fieldMetadata = metadata[field] || { description: "Đang tải mô tả...", sample_value: "" };

            block.innerHTML = `
                <div class="flex items-center justify-between border-b border-white/[0.05] pb-2 mb-1">
                    <div class="flex items-center gap-2 flex-1">
                        <div class="p-1.5 rounded-md ${hasRules ? 'bg-emerald-500/10 text-emerald-400' : 'bg-blue-500/10 text-blue-400'}">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path><path d="m9 12 2 2 4-4"></path></svg>
                        </div>
                        <input type="text" class="block-field-name bg-transparent font-semibold text-sm text-foreground/90 focus:outline-none border-b border-transparent focus:border-primary/50 transition-colors w-full" value="${field}" placeholder="Tên trường">
                    </div>
                    <div class="flex items-center gap-2">
                        <button class="regenerate-block-btn p-1.5 rounded-lg hover:bg-primary/10 text-primary/50 hover:text-primary transition-all" title="Tạo lại logic cho trường này">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3.5 h-3.5"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path><path d="M8 16H3v5"></path></svg>
                        </button>
                        <div class="test-result-indicator hidden items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider">
                            <span class="indicator-icon"></span>
                            <span class="indicator-text"></span>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="rules-list flex flex-col gap-2">
                        <p class="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">${hasRules ? 'Quy tắc áp dụng' : 'Vai trò'}</p>
                        ${rulesHtml}
                    </div>
                    <div class="flex flex-col gap-3">
                        <div class="flex flex-col gap-1">
                            <p class="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">Mô tả</p>
                            <p class="field-description text-xs text-foreground/60 italic leading-relaxed">${fieldMetadata.description}</p>
                        </div>
                        <div class="flex flex-col gap-2">
                            <p class="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">Dữ liệu mẫu ${hasRules ? '& Chạy thử' : ''}</p>
                            <div class="flex gap-2">
                                <input type="text" class="sample-input flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-primary focus:outline-none focus:ring-1 focus:ring-primary/50" value="${fieldMetadata.sample_value}" placeholder="Nhập giá trị test...">
                                ${hasRules ? `
                                <button class="run-block-test-btn px-3 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg text-[10px] font-bold uppercase transition-all flex items-center gap-1.5 shadow-sm">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                                    Chạy thử
                                </button>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;

            const testBtn = block.querySelector('.run-block-test-btn');
            if (testBtn) testBtn.addEventListener('click', () => runSingleBlockCheck(block));

            const regenBtn = block.querySelector('.regenerate-block-btn');
            if (regenBtn) regenBtn.addEventListener('click', () => regenerateFieldLogic(block));

            planBlocksContainer.appendChild(block);
        });
    }

    async function regenerateFieldLogic(block) {
        const field = block.querySelector('.block-field-name').value.trim();
        const rulesText = rulesContent.value.trim();
        const rulesListContainer = block.querySelector('.rules-list');
        const regenBtn = block.querySelector('.regenerate-block-btn');

        if (!field || !rulesText) return;

        regenBtn.classList.add('animate-spin');
        try {
            const response = await fetch('/regenerate-field-logic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field_name: field, rules_text: rulesText })
            });
            const result = await response.json();
            if (result.success) {
                let rulesHtml = '<p class="text-[10px] uppercase tracking-wider text-muted-foreground font-bold">Quy tắc áp dụng</p>';
                result.rules.forEach(rule => {
                    rulesHtml += `
                        <div class="rule-item flex items-center gap-2 group/rule">
                            <div class="w-1.5 h-1.5 rounded-full bg-emerald-500/40 group-hover/rule:bg-emerald-500 transition-colors"></div>
                            <input type="text" class="rule-input flex-1 bg-black/20 border border-white/5 rounded-lg px-3 py-1.5 text-xs font-mono text-emerald-400 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all" value="${rule.replace(/"/g, '&quot;')}" placeholder="Tên hàm helper...">
                        </div>
                    `;
                });
                rulesListContainer.innerHTML = rulesHtml;

                await updatePlanMetadata(getPlanFromBlocks());
            } else {
                alert(result.error);
            }
        } catch (e) {
            alert('Lỗi kết nối khi tạo lại logic.');
        } finally {
            regenBtn.classList.remove('animate-spin');
        }
    }

    async function runSingleBlockCheck(block) {
        const field = block.querySelector('.block-field-name').value.trim();
        const ruleInputs = block.querySelectorAll('.rule-input');
        const indicator = block.querySelector('.test-result-indicator');
        const indicatorIcon = indicator.querySelector('.indicator-icon');
        const indicatorText = indicator.querySelector('.indicator-text');

        const rulesArray = [];
        ruleInputs.forEach(input => {
            const val = input.value.trim();
            if (val) rulesArray.push(val);
        });

        if (!field || rulesArray.length === 0) return;

        const allSampleData = {};
        document.querySelectorAll('.plan-block').forEach(b => {
            const f = b.querySelector('.block-field-name').value.trim();
            const v = b.querySelector('.sample-input').value.trim();
            if (f) allSampleData[f] = v;
        });

        indicator.classList.remove('hidden', 'bg-emerald-500/20', 'text-emerald-400', 'bg-rose-500/20', 'text-rose-400');
        indicator.classList.add('flex', 'bg-white/5', 'text-muted-foreground');
        indicatorIcon.innerHTML = '<svg class="animate-spin h-3 w-3" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
        indicatorText.innerText = 'Đang check...';

        try {
            const response = await fetch('/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: allSampleData,
                    execution_plan: { [field]: rulesArray }
                })
            });
            const result = await response.json();

            indicator.classList.remove('bg-white/5', 'text-muted-foreground');
            if (result.success && result.is_valid) {
                indicator.classList.add('bg-emerald-500/20', 'text-emerald-400');
                indicatorIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><path d="M20 6 9 17l-5-5"></path></svg>';
                indicatorText.innerText = 'Hợp lệ';
            } else {
                indicator.classList.add('bg-rose-500/20', 'text-rose-400');
                indicatorIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-3 h-3"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>';
                indicatorText.innerText = 'Lỗi';
            }
        } catch (e) {
            indicator.classList.add('bg-rose-500/20', 'text-rose-400');
            indicatorText.innerText = 'Lỗi hệ thống';
        }
    }

    function getPlanFromBlocks() {
        const newPlan = {};
        const blocks = planBlocksContainer.querySelectorAll('.plan-block');

        blocks.forEach(block => {
            const fieldName = block.querySelector('.block-field-name').value.trim();
            const ruleInputs = block.querySelectorAll('.rule-input');

            if (fieldName) {
                const rulesArray = [];
                ruleInputs.forEach(input => {
                    const val = input.value.trim();
                    if (val) rulesArray.push(val);
                });
                newPlan[fieldName] = rulesArray;
            }
        });

        return newPlan;
    }

    function createMappingRow(requiredField, mappedField, allDataKeys) {
        const row = document.createElement('div');
        row.className = 'grid grid-cols-[1fr,40px,1.2fr] gap-3 items-center p-3 bg-white/5 rounded-xl border border-white/5';

        let optionsHtml = `<option value="">-- Không ánh xạ --</option>`;
        allDataKeys.forEach(key => {
            optionsHtml += `<option value="${key}" ${key === mappedField ? 'selected' : ''}>${key}</option>`;
        });

        row.innerHTML = `
            <div class="text-sm font-medium text-foreground/80">${requiredField}</div>
            <div class="flex justify-center text-muted-foreground">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>
            </div>
            <div class="flex flex-col gap-1">
                <div class="flex gap-2">
                    <select class="mapping-select flex-1 bg-background border border-border/50 rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all" data-required="${requiredField}">
                        ${optionsHtml}
                        <option value="CUSTOM" ${mappedField.includes('(') ? 'selected' : ''}>-- Tùy chỉnh biểu thức --</option>
                    </select>
                    <button class="calc-btn p-2 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-all" title="Tự động tạo logic tính toán">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-4 h-4"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path><path d="M5 3v4"></path><path d="M19 17v4"></path><path d="M3 5h4"></path><path d="M17 19h4"></path></svg>
                    </button>
                </div>
                <input class="custom-mapping-input ${mappedField.includes('(') || mappedField === 'CUSTOM' ? '' : 'hidden'} w-full bg-background border border-border/50 rounded-lg px-3 py-1.5 text-xs text-foreground mt-1" placeholder="Ví dụ: calculate_age(birth_date)" value="${mappedField.includes('(') ? mappedField : ''}">
            </div>
        `;

        const select = row.querySelector('.mapping-select');
        const customInput = row.querySelector('.custom-mapping-input');
        const calcBtn = row.querySelector('.calc-btn');

        select.addEventListener('change', (e) => {
            if (e.target.value === 'CUSTOM') customInput.classList.remove('hidden');
            else customInput.classList.add('hidden');
        });

        calcBtn.addEventListener('click', async () => {
            const instruction = prompt(`Bạn muốn tính toán trường "${requiredField}" như thế nào?\n(Ví dụ: Tính tuổi từ năm sinh)`, "");
            if (!instruction) return;

            setLoading(true, 'Đang tạo logic tính toán...', true);
            try {
                const data_keys = Object.keys(getFieldData());
                const response = await fetch('/generate-calculation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target_field: requiredField, data_keys, instruction }),
                });
                const result = await response.json();
                if (result.success) {
                    select.value = 'CUSTOM';
                    customInput.classList.remove('hidden');
                    customInput.value = result.logic;
                } else { alert(result.error || 'Không thể tạo logic.'); }
            } catch (e) { alert('Lỗi kết nối.'); } finally { setLoading(false); }
        });

        return row;
    }

    // --- Event Listeners ---
    addFieldBtn.addEventListener('click', () => { dataFieldsContainer.appendChild(createDataRow("", "")); });
    closeModalBtn.addEventListener('click', () => { approvalModal.classList.add('hidden'); });
    closeMappingModalBtn.addEventListener('click', () => { mappingModal.classList.add('hidden'); });

    proceedToMappingBtn.addEventListener('click', () => {
        try {
            currentPlan = getPlanFromBlocks();
            planEditor.value = JSON.stringify(currentPlan, null, 2);
            approvalModal.classList.add('hidden');
            const data = getFieldData();
            if (Object.keys(data).length > 0) {
                initiateMapping(currentPlan, data);
            } else {
                alert('Kế hoạch đã được xác nhận. Vui lòng upload dữ liệu để thực hiện ánh xạ.');
                statusBadge.innerText = 'Chờ dữ liệu';
            }
        } catch (e) { alert('Lỗi khi đọc kế hoạch từ giao diện.'); }
    });

    async function initiateMapping(plan, data) {
        const required_fields = Object.keys(plan);
        const data_keys = Object.keys(data);

        setLoading(true, 'Đang phân tích ánh xạ dữ liệu...', true);
        try {
            const response = await fetch('/generate-mapping', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ required_fields, data_keys }),
            });
            const result = await response.json();
            if (result.success) {
                displayMappingModal(result.mapping, data_keys);
            } else { alert('Không thể tạo ánh xạ tự động. Vui lòng chọn thủ công.'); displayMappingModal({}, data_keys); }
        } catch (error) { alert('Lỗi kết nối khi tạo ánh xạ.'); } finally { setLoading(false); }
    }

    function displayMappingModal(mapping, dataKeys) {
        mappingContainer.innerHTML = '';
        const requiredFields = Object.keys(currentPlan);
        requiredFields.forEach(rf => {
            mappingContainer.appendChild(createMappingRow(rf, mapping[rf] || "", dataKeys));
        });
        mappingModal.classList.remove('hidden');
    }

    confirmMappingBtn.addEventListener('click', () => {
        const mapping = {};
        document.querySelectorAll('.mapping-select').forEach(select => {
            const rf = select.dataset.required;
            if (select.value === 'CUSTOM') {
                const container = select.closest('.flex-col');
                const customInput = container.querySelector('.custom-mapping-input');
                const customVal = customInput ? customInput.value.trim() : "";
                mapping[rf] = customVal || "";
            } else {
                mapping[rf] = select.value;
            }
        });
        currentMapping = mapping;
        mappingModal.classList.add('hidden');
        runCheckBtn.classList.remove('hidden');
        executeFinalCheck(currentPlan, currentMapping);
    });

    runCheckBtn.addEventListener('click', () => {
        if (currentPlan && currentMapping) {
            executeFinalCheck(currentPlan, currentMapping);
        } else {
            alert('Vui lòng chọn mẫu và thực hiện ánh xạ trước.');
        }
    });

    savePlanAsBtn.addEventListener('click', async () => {
        const name = prompt('Nhập tên mẫu mới:');
        if (!name) return;
        try {
            const planToSave = getPlanFromBlocks();
            planEditor.value = JSON.stringify(planToSave, null, 2);
            const resp = await fetch('/plans/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, plan: planToSave })
            });
            if ((await resp.json()).success) {
                alert('Đã lưu mẫu mới!');
                fetchSavedPlans();
            }
        } catch (e) { alert('Lỗi khi lưu.'); }
    });

    async function fetchSavedPlans() {
        try {
            const response = await fetch('/plans');
            const result = await response.json();
            if (result.success) {
                const currentVal = savedPlansSelect.value;
                savedPlansSelect.innerHTML = '<option value="">-- Chọn mẫu đã lưu --</option>';
                result.plans.forEach(planName => {
                    const option = document.createElement('option');
                    option.value = planName;
                    option.textContent = planName;
                    if (planName === currentVal) option.selected = true;
                    savedPlansSelect.appendChild(option);
                });
            }
        } catch (error) { console.error('Failed to fetch plans:', error); }
    }
    fetchSavedPlans();

    loadPlanBtn.addEventListener('click', async () => {
        const planName = savedPlansSelect.value;
        if (!planName) { alert('Vui lòng chọn một mẫu từ danh sách!'); return; }
        try {
            const response = await fetch(`/plans/${planName}`);
            const result = await response.json();
            if (result.success) {
                currentPlan = result.plan;
                displayPlanForApproval(result.plan);
            } else { alert(result.error); }
        } catch (error) { console.error('Failed to load plan:', error); }
    });

    uploadRulesBtn.addEventListener('click', () => rulesFileInput.click());
    rulesFileInput.addEventListener('change', (e) => handleFileUpload(e, rulesContent));

    uploadDataBtn.addEventListener('click', () => dataFileInput.click());
    dataFileInput.addEventListener('change', (e) => handleDataUpload(e));

    async function handleFileUpload(event, targetElement) {
        const file = event.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/upload', { method: 'POST', body: formData });
            const result = await response.json();
            if (result.success) targetElement.value = result.content;
            else alert(result.error);
        } catch (error) { alert('Lỗi khi upload file.'); }
    }

    async function handleDataUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        if (file.name.endsWith('.json')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                try { fillDataFields(JSON.parse(e.target.result)); statusBadge.innerText = 'Đã tải dữ liệu'; }
                catch (err) { alert('File JSON không hợp lệ.'); }
            };
            reader.readAsText(file);
        } else {
            const formData = new FormData();
            formData.append('file', file);
            setLoading(true, 'Đang trích xuất dữ liệu...', false);
            try {
                const uploadResp = await fetch('/upload', { method: 'POST', body: formData });
                const uploadResult = await uploadResp.json();
                if (uploadResult.success) {
                    const currentFields = [];
                    document.querySelectorAll('.field-key').forEach(input => {
                        if (input.value.trim()) currentFields.push(input.value.trim());
                    });
                    const extractResp = await fetch('/extract-data', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: uploadResult.content, fields: currentFields })
                    });
                    const extractResult = await extractResp.json();
                    if (extractResult.success) {
                        fillDataFields(extractResult.data);
                        statusBadge.innerText = 'Đã trích xuất xong';
                    } else alert(extractResult.error);
                } else alert(uploadResult.error);
            } catch (error) { alert('Lỗi khi trích xuất.'); } finally { setLoading(false); }
        }
    }

    sendButton.addEventListener('click', async () => {
        const content = rulesContent.value.trim();
        if (!content) { alert('Vui lòng nhập nội dung quy tắc!'); return; }
        setLoading(true, 'LLM đang phân tích luật...', true);
        try {
            const response = await fetch('/generate-plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rules: content }),
            });
            const result = await response.json();
            if (result.success) {
                currentPlan = result.plan;
                displayPlanForApproval(result.plan, true);
            } else displayError(result.error);
        } catch (error) { displayError('Lỗi kết nối server.'); } finally { setLoading(false); }
    });

    function getFieldData() {
        const data = {};
        document.querySelectorAll('.data-row').forEach(row => {
            const key = row.querySelector('.field-key').value.trim();
            const value = row.querySelector('.field-value').value.trim();
            if (key) data[key] = value;
        });
        return data;
    }

    function setLoading(isLoading, text = 'Đang xử lý...', updateResultBody = true) {
        sendButton.disabled = isLoading;
        buttonText.innerText = isLoading ? 'Đang xử lý...' : 'Trích xuất luật';
        if (isLoading) {
            statusBadge.innerText = 'Đang xử lý...';
            if (updateResultBody) setResultLoading(text);
        }
    }

    function setResultLoading(text) {
        resultBody.innerHTML = `
            <div class="flex flex-col items-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
                <p class="text-foreground/70">${text}</p>
            </div>
        `;
    }

    async function displayPlanForApproval(plan, isFromExtraction = false) {
        statusBadge.innerText = 'Chờ phê duyệt';
        statusBadge.className = 'ml-4 text-xs font-medium px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-400';
        planEditor.value = JSON.stringify(plan, null, 2);
        renderPlanBlocks(plan);

        if (isFromExtraction) {
            proceedToMappingBtn.classList.add('hidden');
            savePlanAsBtn.classList.remove('hidden');
            savePlanAsBtn.classList.add('flex-1');
        } else {
            proceedToMappingBtn.classList.remove('hidden');
            proceedToMappingBtn.classList.add('flex-1');
            savePlanAsBtn.classList.add('hidden');
        }

        approvalModal.classList.remove('hidden');
        await updatePlanMetadata(plan);
    }

    async function updatePlanMetadata(plan) {
        try {
            const response = await fetch('/generate-plan-metadata', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ execution_plan: plan })
            });
            const result = await response.json();
            if (result.success) {
                Object.entries(result.metadata).forEach(([field, meta]) => {
                    const block = document.querySelector(`.plan-block[data-field="${field}"]`);
                    if (block) {
                        const descEl = block.querySelector('.field-description');
                        const inputEl = block.querySelector('.sample-input');
                        if (descEl) descEl.innerText = meta.description;
                        if (inputEl && !inputEl.value) inputEl.value = meta.sample_value;
                    }
                });
            }
        } catch (e) { console.error("Lỗi khi tải metadata:", e); }
    }

    async function executeFinalCheck(plan, mapping) {
        const data = getFieldData();
        setLoading(true, 'Đang thực thi kiểm tra...', true);
        try {
            const response = await fetch('/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data, execution_plan: plan, mapping: mapping }),
            });
            const result = await response.json();
            if (result.success) displayFinalResult(result, plan, mapping);
            else displayError(result.error);
        } catch (error) { displayError('Lỗi kết nối.'); } finally { setLoading(false); }
    }

    function displayFinalResult(result, plan, mapping) {
        const { is_valid, results } = result;
        if (is_valid) {
            statusBadge.innerText = 'Hợp lệ';
            statusBadge.className = 'ml-4 text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400';
            statusIcon.className = 'p-2 rounded-lg bg-emerald-500/20 text-emerald-400 transition-colors duration-500';
        } else {
            statusBadge.innerText = 'Không hợp lệ';
            statusBadge.className = 'ml-4 text-xs font-medium px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400';
            statusIcon.className = 'p-2 rounded-lg bg-rose-500/20 text-rose-400 transition-colors duration-500';
        }
        let resultsHtml = results.length === 0 && is_valid
            ? `<div class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 mb-4">Tất cả quy tắc đều thỏa mãn!</div>`
            : results.map(res => {
                const isError = res.startsWith('INVALID') || res.includes('ERROR') || res.startsWith('MISSING');
                const colorClass = isError ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' : 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
                return `<div class="p-3 rounded-lg border ${colorClass} text-sm font-mono mb-2">${res}</div>`;
            }).join('');
        resultBody.innerHTML = `
            <div class="w-full">
                <div class="mb-6">
                    <h3 class="text-sm font-semibold text-foreground/80 mb-3 flex items-center gap-2">
                        <div class="w-1 h-4 bg-primary rounded-full"></div> Kết quả chi tiết
                    </h3>
                    ${resultsHtml}
                </div>
                <div class="flex gap-4">
                    <button id="reapproveBtn" class="text-xs text-primary hover:underline">Sửa lại kế hoạch thực thi</button>
                    <button id="remappingBtn" class="text-xs text-emerald-400 hover:underline">Sửa lại ánh xạ dữ liệu</button>
                </div>
            </div>
        `;
        document.getElementById('reapproveBtn').addEventListener('click', () => displayPlanForApproval(plan));
        document.getElementById('remappingBtn').addEventListener('click', () => displayMappingModal(mapping, Object.keys(getFieldData())));
    }

    function displayError(message) {
        statusBadge.innerText = 'Lỗi';
        statusBadge.className = 'ml-4 text-xs font-medium px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400';
        resultBody.innerHTML = `
            <div class="flex flex-col items-center text-rose-400">
                <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mb-4"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                <p class="font-medium text-lg">${message}</p>
            </div>
        `;
    }
});

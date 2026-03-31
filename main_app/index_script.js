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
        const savePlanAsBtn = document.getElementById('savePlanAsBtn');
        const proceedToMappingBtn = document.getElementById('proceedToMappingBtn');

        // Mapping Modal elements
        const mappingModal = document.getElementById('mappingModal');
        const closeMappingModalBtn = document.getElementById('closeMappingModalBtn');
        const mappingContainer = document.getElementById('mappingContainer');
        const confirmMappingBtn = document.getElementById('confirmMappingBtn');

        let currentPlan = null;
        let currentMapping = null;

        // --- Init Default Fields ---
        const defaultFields = { "": "" };
        fillDataFields(defaultFields);

        // --- UI Helper Functions ---
        function createDataRow(key, value) {
            const index = dataFieldsContainer.children.length + 1;
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

        function fillDataFields(data) {
            dataFieldsContainer.innerHTML = '';
            Object.entries(data).forEach(([key, value]) => {
                dataFieldsContainer.appendChild(createDataRow(key, value));
            });
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
                currentPlan = JSON.parse(planEditor.value);
                approvalModal.classList.add('hidden');
                const data = getFieldData();
                if (Object.keys(data).length > 0) {
                    initiateMapping(currentPlan, data);
                } else {
                    alert('Kế hoạch đã được xác nhận. Vui lòng upload dữ liệu để thực hiện ánh xạ.');
                    statusBadge.innerText = 'Chờ dữ liệu';
                }
            } catch (e) { alert('JSON không hợp lệ.'); }
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
                    // Sửa lại: Tìm input trong cùng container cha
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
            runCheckBtn.classList.remove('hidden'); // Hiện nút chạy sau khi mapping xong
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
                const planToSave = JSON.parse(planEditor.value);
                const resp = await fetch('/plans/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, plan: planToSave })
                });
                if ((await resp.json()).success) {
                    alert('Đã lưu mẫu mới!');
                    fetchSavedPlans(); // Update real-time
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
                    displayPlanForApproval(result.plan, true); // isFromExtraction = true
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

        function displayPlanForApproval(plan, isFromExtraction = false) {
            statusBadge.innerText = 'Chờ phê duyệt';
            statusBadge.className = 'ml-4 text-xs font-medium px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-400';
            planEditor.value = JSON.stringify(plan, null, 2);
            
            // Nếu là từ trích xuất luật mới, chỉ cho phép lưu, không cho mapping ngay
            if (isFromExtraction) {
                proceedToMappingBtn.classList.add('hidden');
                savePlanAsBtn.classList.remove('hidden');
                savePlanAsBtn.classList.add('flex-1'); // Làm cho nút lưu rộng ra
            } else {
                proceedToMappingBtn.classList.remove('hidden');
                savePlanAsBtn.classList.remove('hidden');
                savePlanAsBtn.classList.remove('flex-1');
            }
            
            approvalModal.classList.remove('hidden');
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



const state = {
    user: { id: null, phone: '', resendAttempts: 0 },
    isOtpSent: false,
    intakeStep: 1,
    profile: {
        name: '', age: '', relationship: 'Self', otherRelationship: '',
        allergies: [], chronic_conditions: [], 
        medications: [], surgical_history: ''
    },
    emergencyData: {
        type: '',
        searchAddress: '', // Human readable address string
        lat: 17.3875, lng: 78.4870, // Default center
        hospital_id: null
    },
    hospitals: []
};

// Persistence Logic
const saveState = () => {
    localStorage.setItem('resqnow_v2', JSON.stringify(state));
};

const loadState = () => {
    try {
        const saved = localStorage.getItem('resqnow_v2');
        if (saved) {
            const parsed = JSON.parse(saved);
            state.user = { ...state.user, ...parsed.user };
            state.profile = { ...state.profile, ...parsed.profile };
            state.emergencyData = { ...state.emergencyData, ...parsed.emergencyData };
            // Always clear OTP state on refresh — login screen always resets to phone input
            state.isOtpSent = false;
            // Never restore hospitals — always fetch fresh
            state.hospitals = [];
            // Don't pre-fill name/age — user must type fresh each session
            state.profile.name = '';
            state.profile.age = '';
        }
    } catch(e) {
        console.error("State parse error", e);
        localStorage.removeItem('resqnow_v2');
    }
};

loadState();
window.state = state;

const router = {
    currentPath: window.location.hash.slice(1) || '/',
    navigate: function(path) {
        this.currentPath = path;
        window.location.hash = path;
        saveState();
        render();
        window.scrollTo(0,0);
    }
};

window.addEventListener('hashchange', () => {
    router.currentPath = window.location.hash.slice(1) || '/';
    render();
});
window.router = router;

const api = {
    auth: async (phone) => {
        const res = await fetch('/api/auth/send-otp', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phone})
        });
        return res.json();
    },
    verify: async (phone, otp) => {
        const res = await fetch('/api/auth/verify', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phone, otp})
        });
        return res.json();
    },
    saveProfile: async () => {
        const res = await fetch(`/api/profile/${state.user.id}`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                name: state.profile.name,
                age: state.profile.age,
                relationship: state.profile.relationship,
                allergies: state.profile.allergies.join(','),
                chronic_conditions: state.profile.chronic_conditions.join(','),
                medications: JSON.stringify(state.profile.medications),
                surgical_history: state.profile.surgical_history
            })
        });
        return res.json();
    },
    getHospitals: async () => {
        const res = await fetch('/api/hospitals');
        return res.json();
    },
    dispatch: async () => {
        const res = await fetch('/api/dispatch', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                user_id: state.user.id,
                emergency_type: state.emergencyData.type,
                lat: state.emergencyData.lat,
                lng: state.emergencyData.lng,
                hospital_id: state.emergencyData.hospital_id
            })
        });
        return res.json();
    }
}

// Global Help functions for Discovery
window.fetchRoadData = async (lat, lng, targetHospitals) => {
    if (!targetHospitals.length) return;
    const coords = `${lng},${lat};` + targetHospitals.map(h => `${h.lng},${h.lat}`).join(';');
    try {
        const res = await fetch(`https://router.project-osrm.org/table/v1/driving/${coords}?sources=0`);
        const data = await res.json();
        if (data.code === 'Ok') {
            data.durations[0].slice(1).forEach((dur, i) => {
                if (dur !== null) {
                    targetHospitals[i].drive_time_mins = Math.round((dur / 60) * 1.5); // Peak traffic multiplier
                    targetHospitals[i].distance_km = (dur / 40).toFixed(1); // Rough conversion
                }
            });
        }
    } catch (e) {
        console.warn("OSRM routing failed", e);
    }
};

window.fetchLiveHospitals = async (currentLat, currentLng, combinedQuery = '') => {
    try {
        // Call our backend which proxies Google Places Text Search
        const res = await fetch(`/api/places?query=${encodeURIComponent(combinedQuery)}&lat=${currentLat}&lng=${currentLng}`);
        const places = await res.json();

        if (!places || places.error || places.length === 0) {
            throw new Error(places?.error || 'No results');
        }

        // Attach driving times from user's current GPS location via OSRM
        await fetchRoadData(currentLat, currentLng, places);
        return places;

    } catch (err) {
        console.error('Google Places Error:', err);
        // Fallback to OSM if Google Places fails
        return await structuralScan(currentLat, currentLng);
    }
};

async function structuralScan(lat, lng) {
    try {
        const query = `[out:json][timeout:20];(node["amenity"~"hospital|clinic"](around:8000,${lat},${lng});way["amenity"~"hospital|clinic"](around:8000,${lat},${lng}););out center 10;`;
        const res = await fetch('https://overpass-api.de/api/interpreter', { method: 'POST', body: query });
        const data = await res.json();
        const results = (data.elements || []).map(el => ({
            id: el.id,
            name: el.tags?.name || 'Medical Facility',
            lat: el.lat ?? el.center?.lat,
            lng: el.lon ?? el.center?.lon,
            rating: (3.5 + Math.random() * 1.4).toFixed(1),
            reviews: Math.floor(Math.random() * 300) + 30,
            isOpen: true, status: 'Open 24 hours',
            type: 'Hospital',
            address: el.tags?.['addr:street'] || '',
            specialist_on_call: 'On-Duty Team'
        }));
        const top5 = results.slice(0, 5);
        await fetchRoadData(lat, lng, top5);
        return top5;
    } catch(e) { return []; }
}

// Views

const LoginView = () => {
    return `
        <div class="login-page">
            <div class="login-card">
                <div class="logo-area">
                    <div class="brand"><i class="ph-fill ph-plus-circle"></i> RESQNOW</div>
                    <div class="tagline">INDIA'S FASTEST EMERGENCY RESPONSE</div>
                </div>
                
                ${state.isOtpSent ? `
                    <h2 class="login-title">Verify Mobile Number</h2>
                    <div class="phone-display">
                        <span>+91 ${(state.user && state.user.phone && state.user.phone.replace('+91','')) || ''}</span>
                        <div class="edit-icon" onclick="resetLogin()"><i class="ph-fill ph-pencil"></i></div>
                    </div>
                    <div class="accent-line"></div>
                    
                    <label class="form-label" style="margin-top:0">Enter OTP</label>
                    <div class="otp-boxes" id="otp-container">
                        <input type="text" maxlength="1" inputmode="numeric" data-index="0" />
                        <input type="text" maxlength="1" inputmode="numeric" data-index="1" />
                        <input type="text" maxlength="1" inputmode="numeric" data-index="2" />
                        <input type="text" maxlength="1" inputmode="numeric" data-index="3" />
                        <input type="text" maxlength="1" inputmode="numeric" data-index="4" />
                        <input type="text" maxlength="1" inputmode="numeric" data-index="5" />
                    </div>
                    <input type="hidden" id="login-otp" />
                    
                    <button id="btn-verify-otp" class="btn-primary" disabled onclick="verifyOTP()">Verify & Continue</button>
                    <div class="resend-timer" id="resend-timer">Resend OTP in 01:00</div>
                    
                    <div class="login-footer">
                        This site is protected by reCAPTCHA and the Google - <a href="#">Privacy Policy</a> and <a href="#">Terms of Service</a> apply.
                    </div>
                ` : `
                    <h2 class="login-title">Login / Sign Up</h2>
                    <div class="login-subtitle">Using OTP</div>
                    <div class="accent-line"></div>
                    
                    <div class="phone-input-wrap">
                        <div class="prefix">+91</div>
                        <input type="tel" id="login-phone" inputmode="numeric" maxlength="10" placeholder="Enter Phone number" value="${(state.user && state.user.phone && state.user.phone.replace('+91','')) || ''}" oninput="this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10); const btn = document.getElementById('btn-send-otp'); btn.disabled = this.value.length !== 10; if(btn.disabled) btn.classList.remove('active'); else btn.classList.add('active');" onkeydown="if(event.key==='Enter' && this.value.length===10) handleLogin();" />
                    </div>
                    
                    <button id="btn-send-otp" class="btn-primary" disabled onclick="handleLogin()">Continue</button>
                    
                    <div class="login-footer">
                        By continuing, I accept ResQNow's <a href="#">Terms and Conditions</a> & <a href="#">Privacy Policy</a>.<br>
                        This site is protected by reCAPTCHA and the Google - <a href="#">Privacy Policy</a> and <a href="#">Terms of Service</a> apply.
                    </div>
                `}
            </div>
        </div>
    `;
};

window.showToast = (msg, type="info") => {
    const toast = document.createElement('div');
    toast.className = `toast toast-top toast-center z-[100] animate-bounce`;
    toast.innerHTML = `<div class="alert alert-${type} shadow-2xl font-bold bg-white text-primary border border-primary"><span>${msg}</span></div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 6000);
}

window.handleLogin = async () => {
    let phoneInput = document.getElementById('login-phone').value.replace(/[^0-9]/g, '');
    if (!phoneInput || phoneInput.length !== 10) return alert("Please enter a valid 10-digit mobile number.");
    
    const phone = '+91' + phoneInput;
    state.user.phone = phone;
    
    const btn = document.getElementById('btn-send-otp');
    btn.disabled = true;
    btn.textContent = "Sending...";
    
    try {
        const res = await api.auth(phone);
        if (res.success) {
            state.isOtpSent = true;
            render();
            
            // Show mock hint if applicable
            if (!res.status || res.message.includes("Mock")) {
                setTimeout(() => {
                    window.showToast(`🧪 DEV MODE: Use OTP 123456 for testing`, "info");
                }, 800);
            }
            
            // Setup OTP box auto-focus logic
            setTimeout(() => {
                const boxes = document.querySelectorAll('.otp-boxes input');
                const hiddenOtp = document.getElementById('login-otp');
                const verifyBtn = document.getElementById('btn-verify-otp');
                
                const updateHidden = () => {
                    const val = Array.from(boxes).map(b => b.value).join('');
                    hiddenOtp.value = val;
                    verifyBtn.disabled = val.length !== 6;
                    if(verifyBtn.disabled) verifyBtn.classList.remove('active');
                    else verifyBtn.classList.add('active');
                };
                
                boxes.forEach((box, i) => {
                    box.addEventListener('input', (e) => {
                        box.value = box.value.replace(/[^0-9]/g,'').slice(0,1);
                        if (box.value && i < 5) boxes[i+1].focus();
                        updateHidden();
                    });
                    box.addEventListener('keydown', (e) => {
                        if (e.key === 'Backspace' && !box.value && i > 0) {
                            boxes[i-1].focus();
                            boxes[i-1].value = '';
                            updateHidden();
                        }
                    });
                    box.addEventListener('paste', (e) => {
                        e.preventDefault();
                        const data = (e.clipboardData.getData('text') || '').replace(/[^0-9]/g,'').slice(0,6);
                        data.split('').forEach((ch, j) => { if(boxes[j]) boxes[j].value = ch; });
                        if(boxes[Math.min(data.length, 5)]) boxes[Math.min(data.length, 5)].focus();
                        updateHidden();
                    });
                });
                if(boxes[0]) boxes[0].focus();
                
                // Resend countdown (60 seconds / Max 2 attempts)
                let seconds = 60;
                const timerEl = document.getElementById('resend-timer');
                
                if (state.user.resendAttempts >= 2) {
                    if (timerEl) {
                        timerEl.textContent = "Max attempts reached. Please try later.";
                        timerEl.style.color = "#DC2626";
                        timerEl.style.cursor = "default";
                        timerEl.onclick = null;
                    }
                    return;
                }

                const tick = setInterval(() => {
                    seconds--;
                    if(timerEl) {
                        if (seconds >= 0) {
                            const minLabel = Math.floor(seconds / 60);
                            const secLabel = seconds % 60;
                            timerEl.textContent = `Resend OTP in ${String(minLabel).padStart(2,'0')}:${String(secLabel).padStart(2,'0')}`;
                        } else {
                            timerEl.textContent = 'Resend OTP';
                            clearInterval(tick);
                            timerEl.style.cursor = 'pointer';
                            timerEl.onclick = () => { 
                                state.user.resendAttempts++;
                                handleLogin(); 
                            };
                        }
                    } else {
                        clearInterval(tick);
                    }
                }, 1000);
            }, 100);
        } else {
            alert((res.error || "Failed to send OTP") + (res.details ? ':\n' + res.details : ''));
            btn.disabled = false;
            btn.textContent = "Continue";
        }
    } catch (e) {
        alert("Server error. Please try again later.");
        btn.disabled = false;
        btn.textContent = "Continue";
    }
};

window.resetLogin = () => {
    state.isOtpSent = false;
    render();
};

window.verifyOTP = async () => {
    const otp = document.getElementById('login-otp').value;
    if (!otp || otp.length !== 6) return alert("Please enter a valid 6-digit OTP");
    
    // VERIFY via real API
    try {
        const res = await api.verify(state.user.phone, otp);
        if (res.success) {
            state.user.id = res.user_id;
            router.navigate('/identity');
        } else {
            alert(res.error || "Invalid OTP! Please check your mobile for the correct code.");
        }
    } catch (e) {
        alert("Verification failed. Please try again.");
    }
}

const Stepper = (step) => `
    <div class="stepper-container">
        <div class="step-bar-bg"></div>
        <div class="step-bar-fill" style="width: ${((step - 1) / 3) * 100}%"></div>
        <div class="step-item ${step >= 1 ? 'active' : ''}">
            <div class="step-dot"></div>
            <div class="step-label">Identity</div>
        </div>
        <div class="step-item ${step >= 2 ? 'active' : ''}">
            <div class="step-dot"></div>
            <div class="step-label">Health</div>
        </div>
        <div class="step-item ${step >= 3 ? 'active' : ''}">
            <div class="step-dot"></div>
            <div class="step-label">History</div>
        </div>
        <div class="step-item ${step >= 4 ? 'active' : ''}">
            <div class="step-dot"></div>
            <div class="step-label">Dispatch</div>
        </div>
    </div>
`;

const IdentityView = () => `
    <div class="quick-intake-card">
        <div class="step-header">
            <i class="ph ph-arrow-left" style="opacity:0; pointer-events:none;"></i>
            <span>Step 1 of 4</span>
            <span>Patient Identity</span>
        </div>
        ${Stepper(1)}
        
        <h1 class="intake-title">Who needs help?</h1>
        <p class="intake-subtitle">Please provide the patient's details so our responders can prepare the right care before arrival.</p>
        
        <label class="form-label">Patient's Full Name</label>
        <div class="form-input-wrapper">
            <input type="text" id="id-name" placeholder="e.g. Sarah Johnson" value="${state.profile.name || ''}" onkeydown="if(event.key==='Enter') saveIdentity();" />
        </div>

        <label class="form-label">Age</label>
        <div class="form-input-wrapper" style="width: max-content;">
            <input type="number" id="id-age" placeholder="--" min="1" max="99" maxlength="2"
                value="${state.profile.age || ''}"
                oninput="this.value = this.value.slice(0,2)"
                onkeydown="if(event.key==='Enter') saveIdentity();" />
        </div>

        <label class="form-label" style="margin-top:1.5rem;">Type of Emergency</label>
        <div style="display:flex; flex-wrap:wrap; gap:0.6rem; margin-bottom:0.75rem;">
            ${['Cardiac','Neuro','Trauma','Burns','Ortho','Pediatric','Other'].map(t => `
                <div onclick="setEmergencyType('${t}')" style="padding:0.55rem 1.1rem; border-radius:100px; border:2px solid ${(state.emergencyData.emergencyType===t||(!['Cardiac','Neuro','Trauma','Burns','Ortho','Pediatric'].includes(state.emergencyData.emergencyType)&&t==='Other'&&state.emergencyData.emergencyType&&state.emergencyData.emergencyType!=='')) ? 'var(--accent-red)' : '#E5E7EB'}; background:${(state.emergencyData.emergencyType===t) ? '#FEF2F2' : 'white'}; color:${(state.emergencyData.emergencyType===t) ? 'var(--accent-red)' : '#374151'}; font-weight:700; font-size:0.9rem; cursor:pointer; transition:all 0.15s;">
                    ${t}
                </div>
            `).join('')}
        </div>
        ${(state.emergencyData.emergencyType === 'Other' || (state.emergencyData.emergencyType && !['Cardiac','Neuro','Trauma','Burns','Ortho','Pediatric','Other',''].includes(state.emergencyData.emergencyType))) ? `
            <div class="form-input-wrapper" style="margin-bottom:1rem;">
                <input type="text" id="emergency-other" placeholder="Describe the emergency..." value="${!['Cardiac','Neuro','Trauma','Burns','Ortho','Pediatric','Other'].includes(state.emergencyData.emergencyType) ? state.emergencyData.emergencyType : ''}" oninput="state.emergencyData.emergencyType = this.value;" />
            </div>
        ` : ''}

        <label class="form-label" style="margin-top:1rem;">Relationship to you</label>
        <div class="relationship-grid">
            <div class="relationship-card ${state.profile.relationship === 'Self' ? 'active' : ''}" onclick="setRelationship('Self')">
                <i class="ph ph-user"></i>
                <span>Self</span>
            </div>
            <div class="relationship-card ${state.profile.relationship === 'Parent' ? 'active' : ''}" onclick="setRelationship('Parent')">
                <i class="ph ph-users-three"></i>
                <span>Parent</span>
            </div>
            <div class="relationship-card ${state.profile.relationship === 'Spouse' ? 'active' : ''}" onclick="setRelationship('Spouse')">
                <i class="ph ph-heart"></i>
                <span>Spouse</span>
            </div>
            <div class="relationship-card ${state.profile.relationship === 'Other' ? 'active' : ''}" onclick="setRelationship('Other')">
                <i class="ph ph-dots-three-circle"></i>
                <span>Other</span>
            </div>
        </div>
        
        ${state.profile.relationship === 'Other' ? `
            <div class="form-input-wrapper" style="margin-top:1rem;">
                <input type="text" id="id-other-rel" placeholder="Please specify" value="${state.profile.otherRelationship || ''}" />
            </div>
        ` : ''}

        <div style="margin-top:1.25rem; padding:1rem 1.25rem; background:#EFF6FF; border-radius:14px; display:flex; align-items:center; gap:0.75rem; border:1.5px solid #BFDBFE;">
            <i class="ph-fill ph-phone" style="color:#2563EB; font-size:1.2rem;"></i>
            <div>
                <div style="font-size:0.72rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.05em;">Primary Contact</div>
                <div style="font-size:1.05rem; font-weight:800; color:#1D4ED8;">+91 ${(state.user && state.user.phone && state.user.phone.replace('+91','')) || '—'}</div>
            </div>
        </div>

        <button class="btn-dark-cta" onclick="saveIdentity()">Continue to Health Info <i class="ph ph-arrow-right"></i></button>
        
        <div class="login-footer" style="margin-top: 1.5rem; text-align:center;">
            This information is shared only with certified medical responders via a secure link.
        </div>
    </div>
`;

window.setEmergencyType = (type) => {
    state.profile.name = document.getElementById('id-name')?.value || state.profile.name;
    state.profile.age = document.getElementById('id-age')?.value || state.profile.age;
    state.emergencyData.emergencyType = type;
    render();
};


window.setRelationship = (rel) => {
    state.profile.name = document.getElementById('id-name')?.value || state.profile.name;
    state.profile.age = document.getElementById('id-age')?.value || state.profile.age;
    state.profile.otherRelationship = document.getElementById('id-other-rel')?.value || state.profile.otherRelationship;
    state.profile.relationship = rel;
    render();
};

window.saveIdentity = () => {
    state.profile.name = document.getElementById('id-name').value;
    state.profile.age = document.getElementById('id-age').value;
    if(state.profile.relationship === 'Other') {
        state.profile.otherRelationship = document.getElementById('id-other-rel')?.value || '';
    }
    // Capture free-text emergency type if "Other" chip was selected
    const otherInput = document.getElementById('emergency-other');
    if (otherInput) state.emergencyData.emergencyType = otherInput.value;
    if(!state.profile.name) return alert("Please enter the patient's name.");
    if(!state.profile.age || state.profile.age <= 0) return alert("Please enter a valid age.");
    router.navigate('/health');
};

const HealthView = () => `
    <div class="quick-intake-card">
        <div class="step-header">
            <i class="ph ph-arrow-left cursor-pointer" onclick="router.navigate('/identity')"></i>
            <span>Step 2 of 4</span>
            <span>Health Baseline</span>
        </div>
        ${Stepper(2)}
        
        <h1 class="intake-title">Allergies &amp; Conditions</h1>
        <p class="intake-subtitle">Crucial baseline info for emergency care. This data helps paramedics prepare the correct medications.</p>

        <div class="section-card">
            <div class="section-header">
                <div class="section-icon icon-allergy"><i class="ph ph-warning-circle"></i></div>
                <div><h3 class="m-0" style="font-size: 1.1rem; font-weight: 800;">Severe Allergies</h3><p class="text-xs text-gray mb-0">Select all that apply</p></div>
            </div>
            <div class="checkbox-grid">
                ${['None', 'Peanuts', 'Latex', 'Penicillin', 'Sulfa Drugs', 'Aspirin'].map(a => `
                    <label class="checkbox-item">
                        <input type="checkbox" ${state.profile.allergies.includes(a) ? 'checked' : ''} onchange="toggleAllergy('${a}')">
                        <span>${a}</span>
                    </label>
                `).join('')}
            </div>
        </div>

        <div class="section-card">
            <div class="section-header">
                <div class="section-icon icon-chronic"><i class="ph ph-heartbeat"></i></div>
                <div><h3 class="m-0" style="font-size: 1.1rem; font-weight: 800;">Chronic Conditions</h3><p class="text-xs text-gray mb-0">Crucial for treatment</p></div>
            </div>
            <div class="checkbox-grid">
                ${['Diabetes', 'Asthma', 'Hypertension', 'COD', 'Heart Disease', 'Seizures'].map(c => `
                    <label class="checkbox-item">
                        <input type="checkbox" ${state.profile.chronic_conditions.includes(c) ? 'checked' : ''} onchange="toggleCondition('${c}')">
                        <span>${c}</span>
                    </label>
                `).join('')}
            </div>
        </div>

        <button class="btn-dark-cta" onclick="saveHealthAndContinue()">Continue to Medications <i class="ph ph-arrow-right"></i></button>
    </div>
`;

const HistoryView = () => `
    <div class="quick-intake-card">
        <div class="step-header">
            <i class="ph ph-arrow-left cursor-pointer" onclick="router.navigate('/health')"></i>
            <span>Step 3 of 4</span>
            <span>Medical History</span>
        </div>
        ${Stepper(3)}
        
        <h1 class="intake-title">Meds &amp; Surgical History</h1>
        <p class="intake-subtitle">Accurate medication history prevents dangerous drug interactions in the ER.</p>

        <div class="section-card">
            <div class="section-header" style="margin-bottom:1.5rem">
                <div class="section-icon" style="background:#FFF7ED; color:#EA580C"><i class="ph ph-pill"></i></div>
                <div><h3 class="m-0" style="font-size: 1.1rem; font-weight: 800;">Active Medications</h3><p class="text-xs text-gray mb-0">List current dosages</p></div>
            </div>
            <div class="flex gap-3 mb-6">
                <input type="text" id="med-name" placeholder="Drug Name" style="flex:2; padding:1rem; border-radius:12px; border:1.5px solid #EEE;" />
                <input type="text" id="med-dose" placeholder="Dose" style="flex:1; padding:1rem; border-radius:12px; border:1.5px solid #EEE;" />
                <button class="btn-primary" style="width:50px; height:50px; padding:0; border-radius:12px; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center;" onclick="addMedication()"><i class="ph ph-plus"></i></button>
            </div>
            <div id="med-list">
                ${state.profile.medications.map((m, i) => `
                    <div class="flex justify-between items-center bg-gray-50 p-3 rounded-lg mb-2">
                        <span class="font-bold">${m.name} <span class="text-sm font-normal text-gray">(${m.dose})</span></span>
                        <i class="ph ph-trash text-red-500 cursor-pointer" onclick="removeMedication(${i})"></i>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="section-card">
            <div class="section-header" style="margin-bottom:1.5rem">
                <div class="section-icon" style="background:#F5F3FF; color:#7C3AED"><i class="ph ph-scissors"></i></div>
                <div><h3 class="m-0" style="font-size: 1.1rem; font-weight: 800;">Surgical History</h3><p class="text-xs text-gray mb-0">Past major operations</p></div>
            </div>
            <textarea id="surgical-history" oninput="state.profile.surgical_history = this.value" placeholder="e.g. Coronary Artery Bypass (2020)..." style="width:100%; height:120px; border-radius:12px; border:1.5px solid #EEE; padding:1rem; resize:none;">${state.profile.surgical_history || ''}</textarea>
        </div>

        <button class="btn-dark-cta" onclick="saveMedicalHistory()">Find My Location <i class="ph ph-arrow-right"></i></button>
    </div>
`;

window.saveHealthAndContinue = () => {
    // Only update emergencyType if the input exists (it's been moved to Identity screen)
    const etInput = document.getElementById('emergency-type');
    if (etInput && etInput.value) state.emergencyData.emergencyType = etInput.value;
    router.navigate('/history');
};

window.saveMedicalHistory = async () => {
    state.profile.surgical_history = document.getElementById('surgical-history')?.value || state.profile.surgical_history;
    await api.saveProfile();
    router.navigate('/location');
};

window.toggleAllergy = (allergy) => {
    const idx = state.profile.allergies.indexOf(allergy);
    if (idx > -1) state.profile.allergies.splice(idx, 1);
    else state.profile.allergies.push(allergy);
    saveState();
    const sideAllergies = document.getElementById('side-allergies-count');
    if (sideAllergies) sideAllergies.textContent = `${state.profile.allergies.length} Allergies identified`;
    render();
};

window.toggleCondition = (condition) => {
    const idx = state.profile.chronic_conditions.indexOf(condition);
    if (idx > -1) state.profile.chronic_conditions.splice(idx, 1);
    else state.profile.chronic_conditions.push(condition);
    saveState();
    render();
};

window.addMedication = () => {
    const name = document.getElementById('med-name').value;
    const dose = document.getElementById('med-dose').value;
    if(name) {
        state.profile.medications.push({name, dose});
        render();
    }
};

window.removeMedication = (i) => {
    state.profile.medications.splice(i, 1);
    render();
};

const LocationView = () => {
    setTimeout(() => {
        const mapEl = document.getElementById('resq-map');
        if (!mapEl || mapEl._leaflet_id) return;

        let lat = state.emergencyData.lat || 17.3850;
        let lng = state.emergencyData.lng || 78.4867;

        // Use colorful CartoDB Voyager tiles
        const map = L.map('resq-map', { zoomControl: false, attributionControl: false }).setView([lat, lng], 14);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
            maxZoom: 19
        }).addTo(map);
        L.control.zoom({ position: 'bottomright' }).addTo(map);

        // Custom pulsing red marker
        const pulseIcon = L.divIcon({
            className: '',
            html: `<div style="
                width:24px; height:24px; background:#DC2626; border-radius:50%;
                border:3px solid white; box-shadow:0 0 0 4px rgba(220,38,38,0.3);
                animation: pulse-dot 1.5s ease-in-out infinite;
            "></div>
            <style>@keyframes pulse-dot {
                0%,100%{box-shadow:0 0 0 4px rgba(220,38,38,0.3);}
                50%{box-shadow:0 0 0 10px rgba(220,38,38,0.1);}
            }</style>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        const marker = L.marker([lat, lng], { icon: pulseIcon }).addTo(map);

        const statusEl = document.getElementById('location-status');
        const addrEl = document.getElementById('location-addr');

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((pos) => {
                lat = pos.coords.latitude;
                lng = pos.coords.longitude;
                state.emergencyData.lat = lat;
                state.emergencyData.lng = lng;
                map.flyTo([lat, lng], 17, { animate: true, duration: 1.5 });
                marker.setLatLng([lat, lng]);
                if (statusEl) statusEl.innerHTML =
                    '<span style="display:inline-flex;align-items:center;gap:0.5rem;background:#DCFCE7;color:#16A34A;padding:0.5rem 1.1rem;border-radius:100px;font-weight:800;font-size:0.9rem;">' +
                    '<i class="ph-fill ph-check-circle"></i> Location locked</span>';
                // Show address AFTER zoom animation ends
                map.once('moveend', function() {
                    fetch('https://nominatim.openstreetmap.org/reverse?lat=' + lat + '&lon=' + lng + '&format=json')
                        .then(function(r){ return r.json(); })
                        .then(function(d){
                            if (d.display_name) {
                                var addr = d.display_name.split(',').slice(0, 4).join(', ');
                                var addrEl = document.getElementById('location-addr');
                                if (addrEl) {
                                    addrEl.innerHTML =
                                        '<div style="display:flex;align-items:flex-start;gap:0.6rem;background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:14px;padding:0.9rem 1.1rem;margin-top:0.5rem;">' +
                                        '<i class="ph-fill ph-map-pin" style="color:#DC2626;font-size:1.2rem;flex-shrink:0;margin-top:2px;"></i>' +
                                        '<span style="font-weight:700;font-size:0.95rem;color:#111;line-height:1.4;">' + addr + '</span>' +
                                        '</div>';
                                }
                            }
                        }).catch(function(){});
                });
            }, () => {
                if (statusEl) statusEl.innerHTML =
                    '<span style="display:inline-flex;align-items:center;gap:0.5rem;background:#FEE2E2;color:#DC2626;padding:0.5rem 1.1rem;border-radius:100px;font-weight:800;font-size:0.9rem;">' +
                    '<i class="ph-fill ph-warning-circle"></i> Using approximate location</span>';
            }, { enableHighAccuracy: true, timeout: 10000 });
        }
    }, 100);

    const emergencyType = state.emergencyData.emergencyType || 'General';
    const emergencyColors = { Cardiac:'#DC2626', Neuro:'#7C3AED', Trauma:'#EA580C', Burns:'#D97706', Ortho:'#0891B2', Pediatric:'#059669' };
    const eColor = emergencyColors[emergencyType] || '#DC2626';

    return `
    <div class="quick-intake-card">
        <div class="step-header">
            <i class="ph ph-arrow-left cursor-pointer" onclick="router.navigate('/history')"></i>
            <span>Step 4 of 4</span>
            <span>Emergency Dispatch</span>
        </div>
        ${Stepper(4)}

        <h1 class="intake-title">Confirm Your Location</h1>

        <!-- Emergency type badge -->
        <div style="display:inline-flex;align-items:center;gap:0.5rem;background:${eColor}18;border:1.5px solid ${eColor}40;padding:0.45rem 1rem;border-radius:100px;margin-bottom:1.25rem;">
            <i class="ph-fill ph-siren" style="color:${eColor};"></i>
            <span style="font-weight:800;font-size:0.9rem;color:${eColor};">${emergencyType} Emergency</span>
        </div>

        <!-- Map -->
        <div style="position:relative; border-radius:20px; overflow:hidden; box-shadow:0 8px 30px rgba(0,0,0,0.12); margin-bottom:1rem;">
            <div id="resq-map" style="height:380px; width:100%;"></div>
        </div>

        <!-- Status -->
        <div id="location-status" style="text-align:center; margin-bottom:0.5rem; font-size:0.9rem;">
            <span style="display:inline-flex;align-items:center;gap:0.5rem;background:#F3F4F6;color:#6B7280;padding:0.5rem 1.1rem;border-radius:100px;font-weight:700;font-size:0.85rem;">
                <span style="width:8px;height:8px;background:#F59E0B;border-radius:50%;display:inline-block;animation:blink 1s ease-in-out infinite;"></span>
                Requesting location...
            </span>
        </div>
        <div id="location-addr" style="text-align:center;font-size:0.8rem;color:#9CA3AF;margin-bottom:1.5rem;min-height:1.2rem;"></div>
        <style>@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}</style>

        <button class="btn-dark-cta" style="background:var(--accent-red);box-shadow:0 10px 30px rgba(220,38,38,0.35);font-size:1.05rem;" onclick="dispatchEmergency()">
            <i class="ph ph-ambulance"></i> &nbsp;Find Nearest ${emergencyType} Hospital
        </button>
    </div>
    `;
};

window.dispatchEmergency = async () => {
    // Use the emergency type already selected on Identity screen
    const combinedQuery = state.emergencyData.emergencyType || 'hospital';
    state.emergencyData.searchAddress = combinedQuery;

    document.getElementById('app').innerHTML = `
        <div style="height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:white;">
            <div style="width:80px;height:80px;border:4px solid #fef2f2;border-top:4px solid #ef4444;border-radius:50%;animation:spin 1s linear infinite;"></div>
            <h2 style="margin-top:2rem;font-weight:900;color:#111;">SEARCHING</h2>
            <p style="color:#ef4444;font-weight:800;font-size:1.1rem;">${combinedQuery.toUpperCase()}</p>
            <p style="color:#64748b;font-weight:600;">Finding top 5 hospitals via Google Places...</p>
        </div>
        <style>@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}</style>
    `;

    const lat = state.emergencyData.lat || 17.3875;
    const lng = state.emergencyData.lng || 78.4870;

    try {
        const liveHospitals = await fetchLiveHospitals(lat, lng, combinedQuery);
        if (liveHospitals && liveHospitals.length > 0) {
            const _surgeons = [
                { name: 'Dr. Priya Reddy',    exp: 14 },
                { name: 'Dr. Suresh Naidu',   exp: 9  },
                { name: 'Dr. Anand Rao',      exp: 17 },
                { name: 'Dr. Meena Sharma',   exp: 11 },
                { name: 'Dr. Kiran Babu',     exp: 22 },
                { name: 'Dr. Ramesh Krishna', exp: 7  },
                { name: 'Dr. Lakshmi Devi',   exp: 19 },
            ];
            liveHospitals.forEach(h => {
                if (!h.surgeon) h.surgeon = _surgeons[Math.floor(Math.random() * _surgeons.length)];
            });
            state.hospitals = liveHospitals;
        } else {
            throw new Error('No facilities found');
        }
    } catch (e) {
        console.warn('Search failed:', e);
        alert('Could not find hospitals. Please check your internet connection.');

        router.navigate('/location');
        return;
    }

    await api.saveProfile();
    router.navigate('/matching');
};
const MatchingView = () => {
    // Guard: if no real search results, send back to intake
    if (!state.hospitals || state.hospitals.length === 0 || !state.hospitals[0]?.name) {
        setTimeout(() => router.navigate('/intake'), 0);
        return `<div style="height:100vh;display:flex;align-items:center;justify-content:center;"><p style="font-weight:700;color:#6B7280;">Redirecting to search...</p></div>`;
    }
    return `
    <div class="quick-intake-card" style="max-width: 1200px;">
        <div class="step-header">
            <i class="ph ph-arrow-left cursor-pointer" onclick="router.navigate('/intake')"></i>
            <span>Step 4</span>
            <span>Hospital Matching</span>
        </div>
        
        <h1 class="intake-title">Matching Results</h1>
        <p class="intake-subtitle">We've found the best emergency facilities near your current location with specialist availability.</p>
        
        <div class="flex gap-6">
            <!-- Left col -->
            <div style="flex: 2;">
                <h3 class="text-primary flex items-center gap-2 mb-4"><i class="ph ph-check-circle"></i> BEST MATCH FOR YOU</h3>
                <div class="hospital-card best-match mb-8">
                    <div class="header-image p-4 flex justify-between items-start">
                        <div class="flex items-center gap-1 bg-white px-2 py-1 rounded shadow-sm">
                            <i class="ph-fill ph-star" style="color:#F59E0B;"></i>
                            <span class="font-bold text-sm">${state.hospitals[0]?.rating}</span>
                            <span style="color:#6B7280; font-size:0.8rem;">(${state.hospitals[0]?.reviews})</span>
                            <span style="color:#6B7280; font-size:0.8rem;"> · ${state.hospitals[0]?.type || 'Hospital'}</span>
                        </div>
                        <span class="badge badge-green" style="font-size:0.75rem;"><i class="ph ph-circle" style="color:#22c55e;"></i> ${state.hospitals[0]?.status || 'Open 24 hours'}</span>
                    </div>
                    <div class="p-6">
                        <h2 style="font-size: 1.4rem; margin-bottom:0.5rem;">${state.hospitals[0]?.name || 'Medical Center'}</h2>
                        <p class="text-gray flex items-center gap-2 mb-2" style="font-size:0.85rem;">
                            <i class="ph ph-map-pin"></i>
                            ${state.hospitals[0]?.distance_km} km away · ${state.hospitals[0]?.drive_time_mins} min drive
                        </p>
                        ${state.hospitals[0]?.address ? `<p class="text-gray mb-4" style="font-size:0.8rem;">${state.hospitals[0].address}</p>` : ''}
                        ${state.hospitals[0]?.surgeon ? `
                        <div style="display:flex;align-items:center;gap:0.5rem;background:#F5F3FF;border-radius:10px;padding:0.6rem 0.85rem;margin-bottom:0.75rem;">
                            <i class="ph-fill ph-user-circle" style="color:#7C3AED;font-size:1.1rem;"></i>
                            <span style="font-size:0.82rem;font-weight:700;color:#5B21B6;">${state.hospitals[0].surgeon.name}</span>
                            <span style="font-size:0.75rem;color:#9CA3AF;margin-left:auto;">${state.hospitals[0].surgeon.exp} yrs exp</span>
                        </div>` : ''}
                        <div class="flex gap-3 mt-4">
                            <button class="btn btn-primary" style="width:100%;" onclick="confirmDispatch('${state.hospitals[0]?.id}')"><i class="ph ph-siren"></i> BOOK AMBULANCE NOW</button>
                        </div>
                    </div>
                </div>
                
                <div class="flex justify-between items-center mb-4">
                    <h3 class="flex items-center gap-2"><i class="ph ph-list-dashes"></i> Top 5 Recommendations</h3>
                    <a href="#" class="text-primary font-semibold text-sm">Compare All Facilities</a>
                </div>
                
                <div class="grid-2">
                    ${state.hospitals.slice(1).map(h => `
                        <div class="hospital-card" style="padding:1.25rem;">
                            <div class="flex justify-between items-start mb-1">
                                <h4 class="font-bold" style="color:#111; font-size:1rem; margin:0;">${h.name}</h4>
                                <span style="font-size:0.65rem; font-weight:700; color:#22c55e; white-space:nowrap;">${h.status || 'Open'}</span>
                            </div>
                            <div class="flex items-center gap-1 mb-2">
                                <i class="ph-fill ph-star" style="color:#F59E0B; font-size:0.75rem;"></i>
                                <span class="font-bold" style="font-size:0.8rem; color:#111;">${h.rating}</span>
                                <span style="font-size:0.75rem; color:#6B7280;">(${h.reviews}) · ${h.type || 'Hospital'}</span>
                            </div>
                            <p style="font-size:0.75rem; color:#6B7280; font-weight:600; margin-bottom:0.5rem;">
                                <i class="ph ph-map-pin"></i> ${h.distance_km} km · ${h.drive_time_mins} min
                            </p>
                            ${h.surgeon ? `<div style="display:flex;align-items:center;gap:0.4rem;background:#F5F3FF;border-radius:8px;padding:0.4rem 0.6rem;margin-bottom:0.6rem;"><i class="ph-fill ph-user-circle" style="color:#7C3AED;font-size:0.9rem;"></i><span style="font-size:0.75rem;font-weight:700;color:#5B21B6;flex:1;">${h.surgeon.name}</span><span style="font-size:0.7rem;color:#9CA3AF;">${h.surgeon.exp}y</span></div>` : ''}
                            <button class="btn btn-primary btn-sm" onclick="confirmDispatch('${h.id}')" style="width:100%; font-size:0.8rem; border-radius:8px;">SELECT</button>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    </div>
`; };
window.confirmDispatch = (hid) => {
    // Find the selected hospital to get the drive time
    const hospital = state.hospitals.find(h => String(h.id) === String(hid)) || state.hospitals[0];
    state.emergencyData.hospital_id = hid;
    state.emergencyData.selectedHospital = hospital;

    // ── Generate surgeon + TS plate ──
    const surgeons = [
        { name: 'Dr. Priya Reddy',    exp: 14 },
        { name: 'Dr. Suresh Naidu',   exp: 9  },
        { name: 'Dr. Anand Rao',      exp: 17 },
        { name: 'Dr. Meena Sharma',   exp: 11 },
        { name: 'Dr. Kiran Babu',     exp: 22 },
        { name: 'Dr. Ramesh Krishna', exp: 7  },
        { name: 'Dr. Lakshmi Devi',   exp: 19 },
    ];
    if (!hospital.surgeon) hospital.surgeon = surgeons[Math.floor(Math.random() * surgeons.length)];
    const districts = ['09','10','11','13','16','02','07'];
    const letters = 'ABCDEFGHJKLMNPRSTUVWXY';
    const rL = () => letters[Math.floor(Math.random()*letters.length)];
    const rN = (n) => String(Math.floor(Math.random()*Math.pow(10,n))).padStart(n,'0');
    state.emergencyData.plateNumber = 'TS ' + districts[Math.floor(Math.random()*districts.length)] + ' ' + rL() + rL() + ' ' + rN(4);

    const app = document.getElementById('app');
    let seconds = 5;

    // ── Phase 1: 5-second loading ──
    const showLoading = () => {
        app.innerHTML =
            '<div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:white;padding:2rem;text-align:center;">' +
            '<div style="width:90px;height:90px;border:5px solid #FEE2E2;border-top:5px solid #DC2626;border-radius:50%;animation:spin 1s linear infinite;margin-bottom:2rem;"></div>' +
            '<h2 style="font-size:1.5rem;font-weight:900;color:#111;margin-bottom:0.5rem;">Booking Your Ambulance</h2>' +
            '<p style="color:#6B7280;font-weight:600;margin-bottom:2rem;">Contacting nearest ' + (hospital ? hospital.name : 'hospital') + '...</p>' +
            '<div id="countdown-ring" style="width:72px;height:72px;border-radius:50%;background:#FEF2F2;display:flex;align-items:center;justify-content:center;">' +
            '<span id="countdown-num" style="font-size:2rem;font-weight:900;color:#DC2626;">' + seconds + '</span>' +
            '</div>' +
            '<style>@keyframes spin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}</style>' +
            '</div>';

        const tick = setInterval(() => {
            seconds--;
            const el = document.getElementById('countdown-num');
            if (el) el.textContent = seconds;
            if (seconds <= 0) {
                clearInterval(tick);
                showBooked();
            }
        }, 1000);
    };

    // ── Phase 2: Booked confirmation ──
    const showBooked = () => {
        const reqId = 'RQ' + Math.floor(100000 + Math.random() * 900000);
        const drivers = [
            { name: 'Rajan Sharma',   phone: '9876501234' },
            { name: 'Suresh Yadav',   phone: '9845067890' },
            { name: 'Arjun Pillai',   phone: '9123456780' },
            { name: 'Mohd. Farrukh',  phone: '9988776655' },
            { name: 'Kiran Babu',     phone: '9765432109' },
        ];
        const driver = drivers[Math.floor(Math.random() * drivers.length)];
        state.emergencyData.bookingRef = reqId;
        state.emergencyData.driver = driver;

        app.innerHTML =
            '<div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:white;padding:2rem;text-align:center;">' +
            '<div style="width:80px;height:80px;border-radius:50%;background:#DCFCE7;display:flex;align-items:center;justify-content:center;margin-bottom:1.25rem;">' +
            '<i class="ph-fill ph-check-circle" style="font-size:3rem;color:#16A34A;"></i></div>' +
            '<h1 style="font-size:1.9rem;font-weight:900;color:#111;margin-bottom:0.25rem;">Ambulance Booked!</h1>' +
            '<p style="color:#6B7280;font-weight:600;margin-bottom:1.75rem;">Your emergency request has been confirmed.</p>' +

            '<div style="background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:16px;padding:1.25rem 1.5rem;width:100%;max-width:340px;text-align:left;margin-bottom:1rem;">' +
            '<div style="font-size:0.72rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem;">Request ID</div>' +
            '<div style="font-size:1.3rem;font-weight:900;color:#111;letter-spacing:0.04em;">' + reqId + '</div>' +
            '</div>' +

            '<div style="background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:16px;padding:1.25rem 1.5rem;width:100%;max-width:340px;text-align:left;margin-bottom:1.5rem;">' +
            '<div style="font-size:0.72rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.75rem;">Your Driver</div>' +
            '<div style="display:flex;align-items:center;gap:0.85rem;">' +
            '<div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#4F46E5,#7C3AED);display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
            '<i class="ph-fill ph-user" style="color:white;font-size:1.3rem;"></i></div>' +
            '<div style="flex:1;">' +
            '<div style="font-weight:800;font-size:1rem;color:#111;">' + driver.name + '</div>' +
            '<div style="font-size:0.85rem;color:#6B7280;font-weight:600;">+91 ' + driver.phone.substring(0,5) + '*****</div>' +
            '</div>' +
            '<a href="tel:+91' + driver.phone + '" style="background:#DCFCE7;color:#16A34A;border-radius:100px;padding:0.45rem 1rem;font-weight:800;font-size:0.85rem;text-decoration:none;border:1.5px solid #BBF7D0;">' +
            '<i class="ph ph-phone"></i> Call</a>' +
            '</div>' +
            '</div>' +

            '<p style="color:#9CA3AF;font-size:0.8rem;font-weight:600;">Redirecting to live tracking...</p>' +
            '</div>';
        setTimeout(() => { router.navigate('/tracking'); render(); }, 3000);
    };

    showLoading();
};

const EmergencyServicesView = () => `
    <div class="quick-intake-card" style="max-width: 440px; padding: 0; overflow: hidden; height: 100vh; display: flex; flex-direction: column;">
        <div class="step-header" style="background: white; border-bottom: 1px solid #EEE; padding: 1.5rem 1rem;">
            <i class="ph ph-arrow-left cursor-pointer" onclick="router.navigate('/matching')"></i>
            <h2 style="font-size: 1.25rem; margin: 0; font-weight: 700;">Service Details</h2>
            <i class="ph ph-headset text-xl ml-auto text-primary"></i>
        </div>
        
        <div style="padding: 1.5rem; flex: 1; overflow-y: auto;">
            <p style="font-weight: 600; margin-bottom: 1rem; color: #111; font-size: 0.95rem;">Service requested for</p>
            <div style="background: #F9FAFB; padding: 0.75rem 1rem; border-radius: 12px; margin-bottom: 2rem; font-weight: 700; color: var(--primary);">
                ${state.profile.relationship === 'Other' ? state.profile.otherRelationship : state.profile.relationship} (${state.profile.name})
            </div>
            
            <p style="font-weight: 600; margin-bottom: 1rem; color: #111; font-size: 0.95rem;">Current location</p>
            <div style="border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; margin-bottom: 2rem; display: flex; align-items: center; gap: 0.75rem; background: #FFF;">
                <i class="ph-fill ph-map-pin text-primary text-xl"></i>
                <div style="font-size: 0.9rem; font-weight: 600;">Pinned Emergency Location</div>
            </div>
            
            <p style="font-weight: 600; margin-bottom: 0.5rem; color: #111; font-size: 0.95rem;">Contact Number</p>
            <div style="border: 1px solid #E5E7EB; border-radius: 12px; padding: 1rem; margin-bottom: 2.5rem; font-weight: 700;">
                +91 ${state.user.phone.replace('+91','')}
            </div>
            
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 1.25rem; display: flex; gap: 0.75rem; align-items: start; margin-bottom: 2rem;">
                <i class="ph-fill ph-info text-green-600 text-xl"></i>
                <p style="font-size: 0.8rem; color: #166534; font-weight: 600; margin: 0; line-height: 1.5;">Our responders will call you in <span style="font-weight: 800;">5 seconds</span> to coordinate specialized care.</p>
            </div>
            
            <button class="btn-dark-cta" style="background: var(--primary); margin-top: 0; box-shadow: 0 10px 30px rgba(79, 70, 229, 0.3);" onclick="router.navigate('/connecting')">Get Quick Callback</button>
        </div>
    </div>
`;

const ConnectingView = () => {
    setTimeout(() => { if(router.currentPath === '/connecting') router.navigate('/tracking'); }, 5000);
    return `
    <div style="max-width:400px; margin:0 auto; background:var(--surface); min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 0 20px rgba(0,0,0,0.1);">
        <h1 style="font-size:3rem; font-weight:800; margin-bottom:3rem; letter-spacing:-0.05em; color:#111;">05 Sec</h1>
        
        <div class="pulse-ring" style="width:140px; height:140px; background:#EEF2FF; border-radius:50%; display:flex; align-items:center; justify-content:center; position:relative; margin-bottom:4rem;">
            <div style="width:70px; height:70px; background:#4F46E5; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:0 10px 25px rgba(79, 70, 229, 0.4); z-index:2;">
                <i class="ph-fill ph-ambulance text-white" style="font-size:2rem;"></i>
            </div>
        </div>
        
        <h2 style="font-size:1.5rem; font-weight:800; text-align:center; letter-spacing:-0.02em; color:#111;">Connecting with<br>nearby Ambulances..</h2>
        <p style="color:#6B7280; font-size:0.95rem; margin-top:0.75rem; font-weight:500;">Stay assured as we've got you covered</p>
    </div>
    `;
};

const TrackingView = () => {
    const hospital = state.emergencyData.selectedHospital;
    const driver   = state.emergencyData.driver || { name: 'Rajan Sharma', phone: '9876501234' };
    const rawMins  = (hospital && hospital.drive_time_mins != null) ? hospital.drive_time_mins : 8;
    const etaMins  = rawMins + 2;
    const distKm   = hospital?.distance_km || '—';

    setTimeout(() => {
        // ─── MAP ───
        const mapEl = document.getElementById('tracking-map');
        if (mapEl && !mapEl._leaflet_id) {
            const uLat = state.emergencyData.lat || 17.3850;
            const uLng = state.emergencyData.lng || 78.4867;
            const hLat = hospital?.lat || (uLat + 0.045);
            const hLng = hospital?.lng || (uLng + 0.030);
            const midLat = (uLat + hLat) / 2;
            const midLng = (uLng + hLng) / 2;

            const map = L.map('tracking-map', { zoomControl:false, attributionControl:false, dragging:false, scrollWheelZoom:false }).setView([midLat, midLng], 13);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { maxZoom:19 }).addTo(map);

            const userIcon = L.divIcon({ className:'', html:'<div style="width:18px;height:18px;background:#EA580C;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(234,88,12,0.5);"></div>', iconSize:[18,18], iconAnchor:[9,9] });
            const hospIcon = L.divIcon({ className:'', html:'<div style="width:36px;height:36px;background:#DC2626;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(220,38,38,0.4);display:flex;align-items:center;justify-content:center;"><i class=\'ph-fill ph-hospital\' style=\'color:white;font-size:1rem;\'></i></div>', iconSize:[36,36], iconAnchor:[18,18] });
            const ambIcon  = L.divIcon({ className:'', html:'<div style="width:38px;height:38px;background:white;border-radius:50%;border:2.5px solid #EA580C;box-shadow:0 3px 10px rgba(0,0,0,0.2);display:flex;align-items:center;justify-content:center;"><i class=\'ph-fill ph-ambulance\' style=\'color:#4F46E5;font-size:1.2rem;\'></i></div>', iconSize:[38,38], iconAnchor:[19,19] });

            const startAmbLat = uLat + (hLat-uLat)*0.75; // start near hospital
            const startAmbLng = uLng + (hLng-uLng)*0.75;
            L.marker([uLat,uLng], { icon:userIcon }).addTo(map);
            L.marker([hLat,hLng], { icon:hospIcon }).addTo(map);
            const ambMarker = L.marker([startAmbLat, startAmbLng], { icon:ambIcon }).addTo(map);
            L.polyline([[uLat,uLng],[uLat+(hLat-uLat)*0.35, uLng+(hLng-uLng)*0.15],[uLat+(hLat-uLat)*0.65,uLng+(hLng-uLng)*0.85],[hLat,hLng]], { color:'#EA580C', weight:4, opacity:0.9, dashArray:'8 4' }).addTo(map);

            // Animate ambulance toward user over etaMins * 60 steps
            const totalSteps = etaMins * 60;
            let step = 0;
            const ambInterval = setInterval(() => {
                step++;
                const t = Math.min(step / totalSteps, 1);
                const newLat = startAmbLat + (uLat - startAmbLat) * t;
                const newLng = startAmbLng + (uLng - startAmbLng) * t;
                ambMarker.setLatLng([newLat, newLng]);
                // Slowly pan map to follow ambulance
                if (step % 30 === 0) map.panTo([newLat, newLng], { animate: true, duration: 1 });
                if (t >= 1) clearInterval(ambInterval);
            }, 1000);
        }

        // ─── TIMERS ───
        const totalArriving  = etaMins * 60;
        const totalDispatch  = 2 * 60;
        let aSecs = totalArriving;
        let dSecs = totalDispatch;
        let dispatched = false;
        const fmt = s => { const m=Math.floor(s/60),sec=s%60; return m+':'+(sec<10?'0':'')+sec; };

        const tick = setInterval(() => {
            if (aSecs <= 0) {
                clearInterval(tick);
                // Persist so reload keeps this screen
                localStorage.setItem('rq_reached', state.emergencyData.bookingRef || 'RQ000000');
                const renderReached = (ref) => {
                    document.getElementById('app').innerHTML =
                        '<div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:white;padding:2rem;text-align:center;">' +
                        '<div style="width:100px;height:100px;border-radius:50%;background:#DCFCE7;display:flex;align-items:center;justify-content:center;margin-bottom:1.5rem;box-shadow:0 0 0 16px #F0FDF4;">' +
                        '<i class="ph-fill ph-ambulance" style="font-size:3.2rem;color:#16A34A;"></i></div>' +
                        '<h1 style="font-size:2rem;font-weight:900;color:#111;margin-bottom:0.5rem;">Ambulance Reached!</h1>' +
                        '<p style="color:#6B7280;font-weight:600;margin-bottom:2rem;">The ambulance has arrived at your location.<br>Please come out immediately.</p>' +
                        '<div style="background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:16px;padding:1.25rem 1.5rem;width:100%;max-width:320px;text-align:left;margin-bottom:1.5rem;">' +
                        '<p style="font-size:0.72rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 4px;">Booking ID</p>' +
                        '<p style="font-size:1.2rem;font-weight:900;color:#111;margin:0;">' + ref + '</p>' +
                        '</div>' +
                        '</div>';
                };
                window._renderReached = renderReached;
                renderReached(state.emergencyData.bookingRef || 'RQ000000');
                return;
            }
            aSecs--;
            if (dSecs > 0) { dSecs--; }
            // Update SMS bubble based on dispatch countdown
            const b = document.getElementById('sms-bubble');
            if (b && !dispatched) {
                if (dSecs === 1) {
                    b.textContent = '🚨 Ambulance dispatching in 1 second!';
                } else if (dSecs > 1 && dSecs <= 10) {
                    b.textContent = '🚑 Ambulance dispatching in ' + dSecs + ' seconds...';
                }
            }
            if (dSecs <= 0 && !dispatched) {
                dispatched = true;
                const bEl = document.getElementById('sms-bubble');
                if (bEl) bEl.textContent = '✅ Ambulance dispatched! En route to you.';

                // 📲 Fire dispatch SMS to patient
                const patientPhone = state.user?.phone || '+918790889527';
                fetch('/api/notify/dispatched', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        phone:       patientPhone,
                        hospital:    hospital?.name    || 'the hospital',
                        driver:      driver?.name      || 'your driver',
                        driverPhone: driver?.phone     || '',
                        bookingRef:  state.emergencyData.bookingRef || '',
                        eta:         etaMins
                    })
                })
                .then(r => r.json())
                .then(d => console.log('📲 Dispatch SMS:', d))
                .catch(e => console.warn('SMS error:', e));
            }
            const aEl = document.getElementById('timer-arrival');
            const dEl = document.getElementById('timer-dispatch');
            if (aEl) aEl.textContent = fmt(aSecs);
            if (dEl) dEl.textContent = dSecs > 0 ? fmt(dSecs) : '0:00';
        }, 1000);
    }, 150);

    return `
    <div style="max-width:420px;margin:0 auto;background:white;min-height:100vh;display:flex;flex-direction:column;box-shadow:0 0 20px rgba(0,0,0,0.1);position:relative;overflow:hidden;">

        <!-- Header -->
        <div style="background:white;padding:1.15rem 1.5rem;display:flex;align-items:center;gap:1rem;z-index:20;box-shadow:0 1px 10px rgba(0,0,0,0.06);">
            <i class="ph ph-arrow-left text-xl cursor-pointer" onclick="router.navigate('/matching')"></i>
            <h2 style="font-size:1.15rem;margin:0;font-weight:800;color:#111;">Active Tracking</h2>
            <i class="ph ph-headset text-xl ml-auto" style="color:#4F46E5;"></i>
        </div>

        <!-- Timers only (no bars) -->
        <div style="background:white;padding:0.85rem 1.5rem 0.9rem;z-index:20;border-bottom:1px solid #F3F4F6;display:flex;gap:1.5rem;">
            <div style="flex:1;display:flex;align-items:center;gap:0.5rem;">
                <i class="ph-fill ph-siren" style="color:#DC2626;font-size:1rem;"></i>
                <div>
                    <div style="font-size:0.7rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.04em;">Arriving in</div>
                    <div id="timer-arrival" style="color:#DC2626;font-weight:900;font-size:1.25rem;font-variant-numeric:tabular-nums;">${etaMins}:00</div>
                </div>
            </div>
            <div style="width:1px;background:#F3F4F6;"></div>
            <div style="flex:1;display:flex;align-items:center;gap:0.5rem;">
                <i class="ph-fill ph-ambulance" style="color:#4F46E5;font-size:1rem;"></i>
                <div>
                    <div style="font-size:0.7rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.04em;">Dispatching in</div>
                    <div id="timer-dispatch" style="color:#4F46E5;font-weight:900;font-size:1.25rem;font-variant-numeric:tabular-nums;">2:00</div>
                </div>
            </div>
        </div>

        <!-- SMS bubble -->
        <div style="padding:0.7rem 1.25rem;background:#F9FAFB;border-bottom:1px solid #F3F4F6;z-index:20;">
            <div style="display:inline-flex;align-items:center;gap:0.55rem;background:white;border:1.5px solid #E5E7EB;border-radius:16px 16px 16px 4px;padding:0.55rem 1rem;box-shadow:0 2px 6px rgba(0,0,0,0.05);max-width:95%;">
                <i class="ph-fill ph-chat-circle-text" style="color:#4F46E5;font-size:0.95rem;flex-shrink:0;"></i>
                <span id="sms-bubble" style="font-size:0.82rem;font-weight:600;color:#374151;">🚑 Ambulance will be dispatched in 2 mins</span>
            </div>
        </div>

        <!-- Map -->
        <div id="tracking-map" style="flex:1;min-height:300px;width:100%;z-index:1;"></div>

        <!-- Floating pill -->
        <div style="position:absolute;bottom:192px;left:50%;transform:translateX(-50%);z-index:20;background:white;border-radius:100px;padding:0.45rem 1.1rem;box-shadow:0 4px 14px rgba(0,0,0,0.12);white-space:nowrap;display:flex;align-items:center;gap:0.5rem;">
            <span style="width:7px;height:7px;background:#22c55e;border-radius:50%;display:inline-block;animation:blink 1s ease-in-out infinite;"></span>
            <span style="font-weight:700;font-size:0.82rem;color:#111;">Ambulance is on the way</span>
        </div>
        <style>@keyframes blink{0%,100%{opacity:1;}50%{opacity:0.3;}}</style>

        <!-- Bottom sheet -->
        <div style="background:white;padding:1.1rem 1.5rem 1.4rem;border-radius:20px 20px 0 0;z-index:20;box-shadow:0 -8px 24px rgba(0,0,0,0.07);">
            <div style="width:36px;height:4px;background:#E5E7EB;border-radius:2px;margin:0 auto 1rem;"></div>
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.9rem;">
                <div style="background:#EEF2FF;border-radius:10px;padding:0.4rem 0.65rem;">
                    <i class="ph-fill ph-ambulance" style="color:#4F46E5;font-size:1.05rem;"></i>
                </div>
                <span style="font-size:1.2rem;font-weight:900;color:#111;letter-spacing:0.06em;flex:1;">${state.emergencyData.plateNumber || 'TS 09 EA 4521'}</span>
                <i class="ph ph-x cursor-pointer" style="color:#9CA3AF;font-size:1.2rem;" onclick="router.navigate('/identity')"></i>
            </div>
            <div style="height:1px;background:#F3F4F6;margin-bottom:0.9rem;"></div>
            <div style="display:flex;align-items:center;gap:0.85rem;">
                <div style="width:44px;height:44px;border-radius:50%;background:linear-gradient(135deg,#4F46E5,#7C3AED);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <i class="ph-fill ph-user" style="color:white;font-size:1.2rem;"></i>
                </div>
                <div style="flex:1;">
                    <p style="font-size:0.72rem;color:#9CA3AF;font-weight:600;margin:0 0 2px;">Driver Details</p>
                    <h3 style="font-size:1rem;font-weight:800;color:#111;margin:0;">${driver.name}</h3>
                    <p style="font-size:0.8rem;color:#6B7280;font-weight:600;margin:2px 0 0;">+91 ${driver.phone.substring(0,5)}*****</p>
                </div>
                <a href="tel:+91${driver.phone}" style="width:46px;height:46px;border-radius:50%;background:#EEF2FF;display:flex;align-items:center;justify-content:center;text-decoration:none;">
                    <i class="ph-fill ph-phone" style="color:#4F46E5;font-size:1.25rem;"></i>
                </a>
            </div>
        </div>
    </div>
    `;
};



const RecentHistoryView = () => `
    <div style="max-width:400px; margin:0 auto; background:#F9FAFB; min-height:100vh; display:flex; flex-direction:column; box-shadow:0 0 20px rgba(0,0,0,0.1);">
        <div style="padding:1.5rem; background:white; display:flex; align-items:center; gap:1rem; box-shadow:0 2px 10px rgba(0,0,0,0.02); position:sticky; top:0; z-index:10;">
            <i class="ph ph-arrow-left text-xl cursor-pointer" onclick="router.navigate('/tracking')"></i>
            <h2 style="font-size:1.35rem; margin:0; font-weight:800; color:#111;">Booking History</h2>
        </div>
        
        <div style="padding:1.5rem;">
            <div style="text-align:center; padding:0.4rem 1rem; background:white; border-radius:100px; font-size:0.8rem; font-weight:700; color:#6B7280; width:max-content; margin:0 auto 1.5rem auto; border:1px solid #E5E7EB; box-shadow:0 2px 5px rgba(0,0,0,0.02);">Nov 2023</div>
            
            <div style="background:white; border-radius:16px; padding:1.5rem; box-shadow:0 4px 20px rgba(0,0,0,0.04); margin-bottom:2rem; border:1px solid #F3F4F6;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.5rem;">
                    <div style="display:flex; align-items:flex-start; gap:0.75rem;">
                        <i class="ph-fill ph-ambulance text-primary text-xl mt-1"></i>
                        <div>
                            <span style="font-weight:800; font-size:0.95rem; color:#111;">Nov 28 (2.7km | 18 min)</span><br>
                            <span style="color:#6B7280; font-weight:600; font-size:0.85rem; margin-top:2px; display:inline-block;">MH 04 1996</span>
                        </div>
                    </div>
                    <span style="background:#D1FAE5; color:#059669; padding:0.35rem 0.85rem; border-radius:100px; font-size:0.75rem; font-weight:800;">Completed</span>
                </div>
                
                <div style="position:relative; padding-left:1.75rem; border-left:2px dashed #E5E7EB; margin-left:0.5rem; padding-bottom:1.5rem;">
                    <div style="position:absolute; left:-6px; top:2px; width:10px; height:10px; background:#10B981; border-radius:50%;"></div>
                    <p style="font-size:0.85rem; font-weight:800; margin:0; color:#111;">1:10PM</p>
                    <p style="font-size:0.85rem; color:#6B7280; margin-top:4px; font-weight:500; line-height:1.4;">123 HK CHS, Opposite GT Fields, Chembur-71</p>
                </div>
                <div style="position:relative; padding-left:1.75rem; margin-left:0.5rem;">
                    <div style="position:absolute; left:-6px; top:2px; width:10px; height:10px; background:#EF4444; border-radius:50%;"></div>
                    <p style="font-size:0.85rem; font-weight:800; margin:0; color:#111;">1:40PM</p>
                    <p style="font-size:0.85rem; color:#6B7280; margin-top:4px; font-weight:500; line-height:1.4;">City Hospital, GES Road, Near SSG Park, Fort-01</p>
                </div>
            </div>
            
            <div style="text-align:center; padding:0.4rem 1rem; background:white; border-radius:100px; font-size:0.8rem; font-weight:700; color:#6B7280; width:max-content; margin:0 auto 1.5rem auto; border:1px solid #E5E7EB; box-shadow:0 2px 5px rgba(0,0,0,0.02);">Oct 2023</div>
            
            <div style="background:white; border-radius:16px; padding:1.5rem; box-shadow:0 4px 20px rgba(0,0,0,0.04); border:1px solid #F3F4F6;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="display:flex; align-items:flex-start; gap:0.75rem;">
                        <i class="ph-fill ph-ambulance text-gray text-xl mt-1 opacity-50"></i>
                        <div>
                            <span style="font-weight:800; font-size:0.95rem; color:#111; opacity:0.7;">Oct 01, 2.3km, 18 min</span><br>
                            <span style="color:#6B7280; font-weight:600; font-size:0.85rem; margin-top:2px; display:inline-block; opacity:0.7;">MH 03 1990</span>
                        </div>
                    </div>
                    <span style="background:#FEE2E2; color:#DC2626; padding:0.35rem 0.85rem; border-radius:100px; font-size:0.75rem; font-weight:800;">Cancelled</span>
                </div>
            </div>
        </div>
    </div>
`;

const render = () => {
    const app = document.getElementById('app');

    // ── If user freshly navigates to root (e.g. types localhost:5000), clear reached flag → go to login ──
    const navType = performance.getEntriesByType('navigation')[0]?.type;
    const hasHash = window.location.hash && window.location.hash.length > 1;
    if (navType === 'navigate' && !hasHash) {
        localStorage.removeItem('rq_reached');
    }

    // ── Persist the "Reached" screen across reloads (but not fresh visits) ──
    const reachedRef = localStorage.getItem('rq_reached');
    if (reachedRef) {
        app.innerHTML =
            '<div style="min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;background:white;padding:2rem;text-align:center;">' +
            '<div style="width:100px;height:100px;border-radius:50%;background:#DCFCE7;display:flex;align-items:center;justify-content:center;margin-bottom:1.5rem;box-shadow:0 0 0 16px #F0FDF4;">' +
            '<i class="ph-fill ph-ambulance" style="font-size:3.2rem;color:#16A34A;"></i></div>' +
            '<h1 style="font-size:2rem;font-weight:900;color:#111;margin-bottom:0.5rem;">Ambulance Reached!</h1>' +
            '<p style="color:#6B7280;font-weight:600;margin-bottom:2rem;">The ambulance has arrived at your location.<br>Please come out immediately.</p>' +
            '<div style="background:#F9FAFB;border:1.5px solid #E5E7EB;border-radius:16px;padding:1.25rem 1.5rem;width:100%;max-width:320px;text-align:left;margin-bottom:1.5rem;">' +
            '<p style="font-size:0.72rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 4px;">Booking ID</p>' +
            '<p style="font-size:1.2rem;font-weight:900;color:#111;margin:0;">' + reachedRef + '</p>' +
            '</div>' +
            '</div>';
        return;
    }

    if (router.currentPath === '/') {
        app.innerHTML = LoginView();
    } else if (router.currentPath === '/identity') {
        app.innerHTML = IdentityView();
    } else if (router.currentPath === '/health') {
        app.innerHTML = HealthView();
    } else if (router.currentPath === '/history') {
        app.innerHTML = HistoryView();
    } else if (router.currentPath === '/location') {
        app.innerHTML = LocationView();
    } else if (router.currentPath === '/intake') {
        app.innerHTML = LocationView(); // redirect old intake to new location view
    } else if (router.currentPath === '/matching') {
        app.innerHTML = MatchingView();
    } else if (router.currentPath === '/dispatch') {
        app.innerHTML = EmergencyServicesView();
    } else if (router.currentPath === '/connecting') {
        app.innerHTML = ConnectingView();
    } else if (router.currentPath === '/tracking') {
        app.innerHTML = TrackingView();
    } else if (router.currentPath === '/recent-history') {
        app.innerHTML = RecentHistoryView();
    }
};

// Initial render
document.addEventListener('DOMContentLoaded', () => {
    const path = router.currentPath;
    const isLoggedIn = state.user && state.user.id;
    const protectedRoutes = ['/identity','/health','/history','/location','/intake','/matching','/dispatch','/connecting','/tracking','/recent-history'];

    if (path === '/' || !path) {
        // Always show phone input on login screen (never OTP after refresh)
        router.currentPath = '/';
    } else if (protectedRoutes.includes(path)) {
        if (!isLoggedIn) {
            // Not logged in — send to login
            router.currentPath = '/';
        }
        // Else: stay on current path (refresh keeps you on same screen)
    }
    render();
});

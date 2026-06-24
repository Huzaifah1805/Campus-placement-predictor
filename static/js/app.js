// Global Variables
let currentSection = 'overview';
let isPredictionRun = false;
let radarChartInstance = null;
let quizAnswers = {};
let currentQuizQuestionIndex = 0;

// Mock Quiz Questions Definition
const QUIZ_QUESTIONS = [
    {
        category: 'DSA',
        text: 'What is the worst-case time complexity of searching in a balanced Binary Search Tree (BST)?',
        options: [
            { text: 'O(1) - Constant Time', score: { dsa: 30, coding: 10 } },
            { text: 'O(log N) - Logarithmic Time', score: { dsa: 100, coding: 70 } },
            { text: 'O(N) - Linear Time', score: { dsa: 60, coding: 40 } },
            { text: 'O(N log N)', score: { dsa: 20, coding: 10 } }
        ]
    },
    {
        category: 'Coding',
        text: 'In JavaScript/Python, what does the higher-order function "map" do?',
        options: [
            { text: 'Modifies the original array in place.', score: { coding: 30, dsa: 20 } },
            { text: 'Transforms each element in an array and returns a new array of the same length.', score: { coding: 100, dsa: 60 } },
            { text: 'Reduces an array to a single accumulator value.', score: { coding: 40, dsa: 30 } },
            { text: 'Filters out items that do not match a boolean test condition.', score: { coding: 50, dsa: 30 } }
        ]
    },
    {
        category: 'DSA',
        text: 'Which of the following data structures operates on a First-In-First-Out (FIFO) basis?',
        options: [
            { text: 'Stack', score: { dsa: 40, coding: 20 } },
            { text: 'Queue', score: { dsa: 100, coding: 60 } },
            { text: 'Binary Tree', score: { dsa: 50, coding: 30 } },
            { text: 'Hash Map', score: { dsa: 30, coding: 10 } }
        ]
    },
    {
        category: 'Coding',
        text: 'Which database command is NOT part of standard SQL operations for editing/retrieving data?',
        options: [
            { text: 'SELECT', score: { coding: 20 } },
            { text: 'UPDATE', score: { coding: 20 } },
            { text: 'PUSH', score: { coding: 100, webdev: 100 } },
            { text: 'DELETE', score: { coding: 20 } }
        ]
    },
    {
        category: 'Communication',
        text: 'What is the recommended, structured framework for answering behavioral interview questions?',
        options: [
            { text: 'FAST method (Focus, Action, Speak, Task)', score: { comm: 40 } },
            { text: 'STAR method (Situation, Task, Action, Result)', score: { comm: 100 } },
            { text: 'Waterfall model', score: { comm: 10 } },
            { text: 'PESTLE analysis', score: { comm: 30 } }
        ]
    }
];

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    initSliders();
    initNavigation();
    initForms();
    initTheme();
    
    // Fetch dynamic database stats & logs on startup
    fetchDashboardStats();
    fetchPredictionHistory();
});

// ==========================================
// FORM SLIDERS EVENT HANDLERS
// ==========================================
function initSliders() {
    const sliders = [
        { id: 'input-cgpa', valId: 'val-cgpa', suffix: '' },
        { id: 'input-coding', valId: 'val-coding', suffix: '%' },
        { id: 'input-dsa', valId: 'val-dsa', suffix: '%' },
        { id: 'input-webdev', valId: 'val-webdev', suffix: '%' },
        { id: 'input-comm', valId: 'val-comm', suffix: '%' }
    ];

    sliders.forEach(slider => {
        const inputEl = document.getElementById(slider.id);
        const valEl = document.getElementById(slider.valId);
        
        if (inputEl && valEl) {
            inputEl.addEventListener('input', (e) => {
                valEl.textContent = e.target.value + slider.suffix;
            });
        }
    });
}

// ==========================================
// NAVIGATION MANAGEMENT
// ==========================================
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetSection = item.getAttribute('data-section');
            
            // Check validation for disabled sections
            if (item.classList.contains('disabled')) {
                showToast('Please submit the placement predictor form to unlock this screen.', 'error');
                return;
            }
            
            switchSection(targetSection);
        });
    });
}

function switchSection(sectionId) {
    // Hide active screens, show target screen
    document.querySelectorAll('.screen-section').forEach(section => {
        section.classList.remove('active');
    });
    
    const targetSection = document.getElementById(`section-${sectionId}`);
    if (targetSection) {
        targetSection.classList.add('active');
    }

    // Update active nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('data-section') === sectionId) {
            item.classList.add('active');
        }
    });

    currentSection = sectionId;
    
    // Update Header title dynamically
    updateHeaderTitle(sectionId);
}

function updateHeaderTitle(sectionId) {
    const titleEl = document.getElementById('header-title');
    const subtitleEl = document.getElementById('header-subtitle');
    
    if (!titleEl || !subtitleEl) return;

    switch (sectionId) {
        case 'overview':
            titleEl.textContent = 'Welcome to PlacementPulse';
            subtitleEl.textContent = 'Evaluate your placement readiness and design your career path.';
            break;
        case 'predictor':
            titleEl.textContent = 'Placement Readiness Predictor';
            subtitleEl.textContent = 'Input your academic and skills parameters to run our classifier.';
            break;
        case 'analysis':
            titleEl.textContent = 'Your Placement Readiness Report';
            subtitleEl.textContent = 'Explore probability scores, mock scenario parameters, and skill gaps.';
            break;
        case 'mentor':
            titleEl.textContent = 'AI Career Mentor & Learning Portal';
            subtitleEl.textContent = 'Custom milestones, project recommendations, and mentor booking.';
            break;
        case 'mock-test':
            titleEl.textContent = 'Quick Skill Assessment Quiz';
            subtitleEl.textContent = 'Assess your technical skills instantly to pre-fill your profile.';
            break;
    }
}

// Enable Analysis and Mentor tabs once data is analyzed
function unlockReportScreens() {
    isPredictionRun = true;
    const navAnalysis = document.getElementById('nav-analysis');
    const navMentor = document.getElementById('nav-mentor');
    
    if (navAnalysis && navMentor) {
        navAnalysis.classList.remove('disabled');
        navAnalysis.removeAttribute('title');
        
        navMentor.classList.remove('disabled');
        navMentor.removeAttribute('title');
    }
}

// ==========================================
// FORM SUBMISSIONS & API INTERACTIONS
// ==========================================
function initForms() {
    const predForm = document.getElementById('prediction-form');
    if (predForm) {
        predForm.addEventListener('submit', handlePredictionSubmit);
    }

    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', handleBookingSubmit);
    }
}

async function handlePredictionSubmit(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('btn-submit-prediction');
    const btnText = document.getElementById('btn-text');
    const btnSpinner = document.getElementById('btn-spinner');
    
    // Toggle Loading State
    if (submitBtn) submitBtn.disabled = true;
    if (btnText) btnText.textContent = 'Analyzing Student Profile...';
    if (btnSpinner) btnSpinner.classList.remove('hidden');
    
    const formData = new FormData(e.target);
    const payload = {};
    formData.forEach((value, key) => {
        payload[key] = value;
    });

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            unlockReportScreens();
            populateReportData(data, payload);
            
            // Refresh prediction database stats and logs
            fetchDashboardStats();
            fetchPredictionHistory();
            
            showToast('Prediction successfully calculated!', 'success');
            
            // Wait briefly to allow user to see success, then transition screen
            setTimeout(() => {
                switchSection('analysis');
            }, 600);
        } else {
            showToast(data.message || 'Failed to calculate prediction.', 'error');
        }
    } catch (error) {
        console.error('Error fetching prediction:', error);
        showToast('Network error, please check connection.', 'error');
    } finally {
        // Reset Button State
        if (submitBtn) submitBtn.disabled = false;
        if (btnText) btnText.textContent = 'Predict Placement Probability';
        if (btnSpinner) btnSpinner.classList.add('hidden');
    }
}

async function handleBookingSubmit(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('btn-submit-booking');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Scheduling...';
    
    const payload = {
        name: document.getElementById('booking-name').value,
        email: document.getElementById('booking-email').value,
        topic: document.getElementById('booking-topic').value
    };

    try {
        const response = await fetch('/api/request-mentor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast(data.message, 'success');
            e.target.reset();
        } else {
            showToast(data.message || 'Scheduling failed.', 'error');
        }
    } catch (error) {
        console.error('Error booking session:', error);
        showToast('Network error, scheduling failed.', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

// ==========================================
// DYNAMIC DOM POPULATION
// ==========================================
function populateReportData(data, inputPayload) {
    // 1. Placement Probability Gauge Animation
    const probPercent = Math.round(data.placement_probability * 100);
    const displayProbEl = document.getElementById('display-prob');
    if (displayProbEl) {
        animateNumber(0, probPercent, 800, (v) => {
            displayProbEl.textContent = v + '%';
        });
    }
    
    const circle = document.getElementById('probability-gauge');
    if (circle) {
        const radius = circle.r.baseVal.value;
        const circumference = radius * 2 * Math.PI;
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        const offset = circumference - (probPercent / 100) * circumference;
        circle.style.strokeDashoffset = offset;
    }

    // 2. Readiness Text Description
    const textDescEl = document.getElementById('display-readiness-text');
    if (textDescEl) {
        if (probPercent > 80) {
            textDescEl.textContent = 'Ready for immediate recruitment drives. Top product fit!';
        } else if (probPercent > 50) {
            textDescEl.textContent = 'Moderate placement chances. Focus on key improvements.';
        } else {
            textDescEl.textContent = 'High probability of missing initial placement cycles. Major revisions needed.';
        }
    }

    // 3. Projected Package
    const salaryEl = document.getElementById('display-salary');
    if (salaryEl) {
        salaryEl.textContent = data.projected_salary;
    }

    // 4. What-If Scenarios
    const scenarioCont = document.getElementById('scenarios-container');
    if (scenarioCont) {
        scenarioCont.innerHTML = '';
        if (data.scenarios && data.scenarios.length > 0) {
            data.scenarios.forEach(sc => {
                const item = document.createElement('div');
                item.className = 'scenario-item';
                
                const percentPlaced = Math.round(sc.probability * 100);
                const percentImprove = Math.round(sc.improvement * 100);
                
                item.innerHTML = `
                    <div class="scenario-header">
                        <span class="scenario-title">${sc.scenario}</span>
                        <span class="scenario-impact">+${percentImprove}% Chance</span>
                    </div>
                    <div class="scenario-bar-bg">
                        <div class="scenario-bar-fill" style="width: ${percentPlaced}%"></div>
                    </div>
                `;
                scenarioCont.appendChild(item);
            });
        } else {
            scenarioCont.innerHTML = '<div class="no-scenarios">No improvement scenarios simulated (Your profile is already optimal).</div>';
        }
    }

    // 5. Draw Skills Radar Chart
    drawRadarChart(inputPayload);

    // 6. Profile Health Check Badges
    const healthCont = document.getElementById('metrics-status-container');
    if (healthCont) {
        healthCont.innerHTML = '';
        for (const metric in data.feedback) {
            const fd = data.feedback[metric];
            const item = document.createElement('div');
            item.className = 'metric-status-item';
            
            // Clean up name label
            let nameLabel = metric;
            if (metric === 'technical') nameLabel = 'Tech Skills';
            if (metric === 'experience') nameLabel = 'Experience';
            if (metric === 'cgpa') nameLabel = 'Academic GPA';
            
            item.innerHTML = `
                <div class="metric-status-header">
                    <span class="metric-status-name">${nameLabel}</span>
                    <span class="badge ${fd.class}">${fd.status}</span>
                </div>
                <p class="metric-status-desc">${fd.desc}</p>
            `;
            healthCont.appendChild(item);
        }
    }

    // 7. AI Roadmap Milestones
    const roadmapCont = document.getElementById('roadmap-timeline-container');
    if (roadmapCont) {
        roadmapCont.innerHTML = '';
        data.roadmap.forEach(step => {
            const node = document.createElement('div');
            node.className = 'roadmap-node';
            node.innerHTML = `
                <div class="roadmap-marker"></div>
                <div class="roadmap-content">
                    <h3>${step.phase}</h3>
                    <p class="roadmap-goal">${step.goal}</p>
                    <div class="roadmap-res"><i class="fa-solid fa-book"></i> Recommended: ${step.resources}</div>
                </div>
            `;
            roadmapCont.appendChild(node);
        });
    }

    // 8. Recommended Project Cards
    const projCont = document.getElementById('project-ideas-container');
    if (projCont) {
        projCont.innerHTML = '';
        data.project_ideas.forEach(proj => {
            const card = document.createElement('div');
            card.className = 'project-idea-card';
            card.innerHTML = `
                <div class="project-title-row">
                    <h4>${proj.title}</h4>
                    <span class="diff-badge">${proj.difficulty}</span>
                </div>
                <p class="project-desc">${proj.desc}</p>
                <div class="project-stack">
                    <i class="fa-solid fa-layer-group"></i>
                    <span>Stack: ${proj.stack}</span>
                </div>
            `;
            projCont.appendChild(card);
        });
    }

    // 9. High Priority Suggestions list
    const recCont = document.getElementById('recommendations-container');
    if (recCont) {
        recCont.innerHTML = '';
        data.recommendations.forEach(rec => {
            const iconMap = {
                'Critical': 'fa-solid fa-triangle-exclamation critical',
                'High': 'fa-solid fa-circle-exclamation high',
                'Medium': 'fa-solid fa-circle-info medium',
                'Low': 'fa-solid fa-lightbulb low'
            };
            const item = document.createElement('li');
            item.className = 'recommendation-item';
            item.innerHTML = `
                <i class="rec-icon ${iconMap[rec.priority] || 'fa-solid fa-circle-info'}"></i>
                <div class="rec-info">
                    <h4>${rec.title} <span class="badge ${rec.priority === 'Critical' ? 'danger' : 'warning'}" style="font-size:0.6rem">${rec.priority}</span></h4>
                    <p>${rec.desc}</p>
                </div>
            `;
            recCont.appendChild(item);
        });
    }
}

// ==========================================
// RADAR CHART DRAWING (CHART.JS)
// ==========================================
function drawRadarChart(payload) {
    const canvas = document.getElementById('skillRadarChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    // Scale academic GPA to % for radar scale (5.0 to 10.0 range mapped to 50 to 100)
    const academicPercent = Math.min(100, Math.max(20, (parseFloat(payload.cgpa) / 10.0) * 100));
    
    const userScores = [
        academicPercent,
        parseInt(payload.coding_score),
        parseInt(payload.dsa_score),
        parseInt(payload.webdev_score),
        parseInt(payload.comm_score)
    ];

    // Reference targets derived from successful placements in synthetic dataset
    const placementAverage = [82, 75, 78, 70, 75];

    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    // Is Light Mode Active?
    const isLight = document.body.classList.contains('light-mode');
    const labelColor = isLight ? '#475569' : '#94a3b8';
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.08)';

    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Academic (CGPA)', 'Coding Proficiency', 'DSA Foundation', 'Dev Stack Specialization', 'HR Communication'],
            datasets: [
                {
                    label: 'Your Skill Profile',
                    data: userScores,
                    fill: true,
                    backgroundColor: 'rgba(139, 92, 246, 0.2)',
                    borderColor: 'rgb(139, 92, 246)',
                    pointBackgroundColor: 'rgb(139, 92, 246)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(139, 92, 246)',
                    borderWidth: 2
                },
                {
                    label: 'Target Benchmark (Placed Average)',
                    data: placementAverage,
                    fill: true,
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderColor: 'rgb(6, 182, 212)',
                    pointBackgroundColor: 'rgb(6, 182, 212)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(6, 182, 212)',
                    borderWidth: 1.5,
                    borderDash: [4, 4]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: {
                        color: gridColor
                    },
                    grid: {
                        color: gridColor
                    },
                    pointLabels: {
                        color: labelColor,
                        font: {
                            family: 'Inter',
                            size: 10,
                            weight: '500'
                        }
                    },
                    ticks: {
                        color: labelColor,
                        backdropColor: 'transparent',
                        showLabelBackdrop: false,
                        stepSize: 20
                    },
                    min: 0,
                    max: 100
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: labelColor,
                        font: {
                            family: 'Inter',
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

// ==========================================
// MOCK SKILL ASSESSMENT QUIZ LOGIC
// ==========================================
function startQuiz() {
    currentQuizQuestionIndex = 0;
    quizAnswers = {};
    
    document.getElementById('quiz-start-view').classList.add('hidden');
    document.getElementById('quiz-question-view').classList.remove('hidden');
    document.getElementById('quiz-results-view').classList.add('hidden');
    
    showQuestion();
}

function showQuestion() {
    const question = QUIZ_QUESTIONS[currentQuizQuestionIndex];
    
    // Progress bar
    const progressPercent = ((currentQuizQuestionIndex) / QUIZ_QUESTIONS.length) * 100;
    document.getElementById('quiz-progress').style.width = `${progressPercent}%`;
    
    // Counter & tags
    document.getElementById('q-counter').textContent = `Question ${currentQuizQuestionIndex + 1} of ${QUIZ_QUESTIONS.length}`;
    document.getElementById('q-category').textContent = question.category;
    document.getElementById('q-text').textContent = question.text;
    
    // Build options
    const optionsContainer = document.getElementById('q-options');
    optionsContainer.innerHTML = '';
    
    question.options.forEach((opt, idx) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        if (quizAnswers[currentQuizQuestionIndex] === idx) {
            btn.classList.add('selected');
        }
        btn.textContent = opt.text;
        btn.onclick = () => selectOption(idx);
        optionsContainer.appendChild(btn);
    });
    
    // Nav buttons toggle
    const prevBtn = document.getElementById('btn-quiz-prev');
    const nextBtn = document.getElementById('btn-quiz-next');
    
    prevBtn.disabled = currentQuizQuestionIndex === 0;
    
    if (currentQuizQuestionIndex === QUIZ_QUESTIONS.length - 1) {
        nextBtn.textContent = 'Finish Quiz';
    } else {
        nextBtn.textContent = 'Next';
    }
}

function selectOption(optionIndex) {
    quizAnswers[currentQuizQuestionIndex] = optionIndex;
    
    // Refresh selection highlights
    const buttons = document.querySelectorAll('.option-btn');
    buttons.forEach((btn, idx) => {
        if (idx === optionIndex) {
            btn.classList.add('selected');
        } else {
            btn.classList.remove('selected');
        }
    });
}

function prevQuestion() {
    if (currentQuizQuestionIndex > 0) {
        currentQuizQuestionIndex--;
        showQuestion();
    }
}

function nextQuestion() {
    // Ensure an answer is selected
    if (quizAnswers[currentQuizQuestionIndex] === undefined) {
        showToast('Please select an option to proceed.', 'error');
        return;
    }
    
    if (currentQuizQuestionIndex < QUIZ_QUESTIONS.length - 1) {
        currentQuizQuestionIndex++;
        showQuestion();
    } else {
        // Evaluate quiz and show results
        calculateQuizScores();
    }
}

function calculateQuizScores() {
    let totals = { coding: 0, dsa: 0, comm: 0 };
    let counts = { coding: 0, dsa: 0, comm: 0 };
    
    QUIZ_QUESTIONS.forEach((q, qIdx) => {
        const selectedOptIdx = quizAnswers[qIdx];
        const scores = q.options[selectedOptIdx].score;
        
        for (const cat in scores) {
            totals[cat] += scores[cat];
            counts[cat]++;
        }
    });
    
    // Average scores
    const codingScore = counts.coding > 0 ? Math.round(totals.coding / counts.coding) : 50;
    const dsaScore = counts.dsa > 0 ? Math.round(totals.dsa / counts.dsa) : 50;
    const commScore = counts.comm > 0 ? Math.round(totals.comm / counts.comm) : 50;
    
    // Save locally to session
    window.quizScoresResult = {
        coding_score: codingScore,
        dsa_score: dsaScore,
        comm_score: commScore
    };
    
    // Display results
    document.getElementById('quiz-res-coding').textContent = `${codingScore}/100`;
    document.getElementById('quiz-res-dsa').textContent = `${dsaScore}/100`;
    document.getElementById('quiz-res-comm').textContent = `${commScore}/100`;
    
    document.getElementById('quiz-question-view').classList.add('hidden');
    document.getElementById('quiz-results-view').classList.remove('hidden');
}

function applyQuizScores() {
    if (!window.quizScoresResult) return;
    
    const scores = window.quizScoresResult;
    
    // Pre-fill predictor form
    const codingInput = document.getElementById('input-coding');
    const dsaInput = document.getElementById('input-dsa');
    const commInput = document.getElementById('input-comm');
    
    if (codingInput) {
        codingInput.value = scores.coding_score;
        document.getElementById('val-coding').textContent = scores.coding_score + '%';
    }
    if (dsaInput) {
        dsaInput.value = scores.dsa_score;
        document.getElementById('val-dsa').textContent = scores.dsa_score + '%';
    }
    if (commInput) {
        commInput.value = scores.comm_score;
        document.getElementById('val-comm').textContent = scores.comm_score + '%';
    }
    
    showToast('Quiz scores successfully populated to form!', 'success');
    
    // Go to predictor form and trigger submit
    switchSection('predictor');
    
    // Submit form automatically
    setTimeout(() => {
        const predForm = document.getElementById('prediction-form');
        if (predForm) {
            predForm.dispatchEvent(new Event('submit'));
        }
    }, 600);
}

function resetQuiz() {
    startQuiz();
}

// ==========================================
// ACCESSIBILITY & UTILITIES
// ==========================================
function initTheme() {
    const themeBtn = document.getElementById('theme-toggle');
    if (!themeBtn) return;
    
    // Read localstorage or dark theme default
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-mode');
        themeBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }
    
    themeBtn.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        const isLight = document.body.classList.contains('light-mode');
        
        themeBtn.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
        
        // Redraw radar chart to update label/grid colors
        if (radarChartInstance && isPredictionRun) {
            const cgpa = document.getElementById('input-cgpa').value;
            const coding = document.getElementById('input-coding').value;
            const dsa = document.getElementById('input-dsa').value;
            const webdev = document.getElementById('input-webdev').value;
            const comm = document.getElementById('input-comm').value;
            
            drawRadarChart({ cgpa, coding_score: coding, dsa_score: dsa, webdev_score: webdev, comm_score: comm });
        }
    });
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    toast.classList.remove('hidden');
    
    // Hide toast after 4 seconds
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}

function animateNumber(start, end, duration, callback) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        callback(value);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// ==========================================
// DB LOGS & STATS LOADER
// ==========================================
async function fetchDashboardStats() {
    try {
        const response = await fetch('/api/dashboard-stats');
        const data = await response.json();
        
        if (data.status === 'success') {
            const accEl = document.getElementById('stat-accuracy');
            const pkgEl = document.getElementById('stat-avg-package');
            const recEl = document.getElementById('stat-records');
            
            if (recEl && data.baseline) {
                const totalCalculations = data.baseline.total_records + data.diagnoses_run;
                recEl.textContent = totalCalculations.toLocaleString();
            }
            
            if (pkgEl && data.baseline && data.baseline.placed_ratio) {
                const avgLpa = (data.baseline.placed_ratio * 12.5).toFixed(1);
                pkgEl.textContent = `${avgLpa} LPA`;
            }
            
            if (accEl) {
                accEl.textContent = (data.baseline.placed_ratio * 100 || 89.6).toFixed(1) + '%';
            }
        }
    } catch (e) {
        console.error('Failed to fetch dashboard stats:', e);
    }
}

async function fetchPredictionHistory() {
    const tbody = document.getElementById('history-table-body');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        if (data.status === 'success' && data.history && data.history.length > 0) {
            tbody.innerHTML = '';
            data.history.forEach(row => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid var(--border-glass)';
                
                // Format timestamp
                const dateObj = new Date(row.timestamp + 'Z'); // Treat SQLite timestamp as UTC
                const timeString = dateObj.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) + 
                                   ' ' + dateObj.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
                
                const techAvg = Math.round((row.coding_score + row.dsa_score + row.webdev_score) / 3);
                const probPercent = Math.round(row.probability * 100);
                
                tr.innerHTML = `
                    <td style="padding: 12px 16px; font-size: 0.85rem; color: var(--text-muted);">${timeString}</td>
                    <td style="padding: 12px 16px; font-size: 0.88rem; font-weight: 600;">${row.cgpa.toFixed(2)}</td>
                    <td style="padding: 12px 16px; font-size: 0.88rem;"><span class="badge ${row.backlogs > 0 ? 'danger' : 'success'}" style="font-size:0.65rem; padding: 2px 6px;">${row.backlogs}</span></td>
                    <td style="padding: 12px 16px; font-size: 0.88rem;">${techAvg}%</td>
                    <td style="padding: 12px 16px; font-size: 0.88rem; font-weight: 700; color: ${probPercent > 80 ? 'var(--success)' : (probPercent > 50 ? 'var(--warning)' : 'var(--danger)')}">${probPercent}%</td>
                    <td style="padding: 12px 16px; font-size: 0.85rem; color: var(--secondary); font-weight: 600;">${row.salary_range}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error('Failed to fetch prediction history:', e);
    }
}

// Mock data has been removed. API calls will be used.

const GRADUATION_FEE_TOTAL = 1000;

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Class Distribution Chart
    const classDistributionChart = new Chart(document.getElementById('classDistributionChart'), {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Number of Students',
                data: [],
                backgroundColor: '#4CAF50',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Students per Class'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Initialize Payment Status Overview Chart
    const paymentOverviewChart = new Chart(document.getElementById('paymentOverviewChart'), {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Full Payment',
                    data: [],
                    backgroundColor: '#4CAF50',
                    borderWidth: 1
                },
                {
                    label: 'Partial Payment',
                    data: [],
                    backgroundColor: '#FFC107',
                    borderWidth: 1
                },
                {
                    label: 'No Payment',
                    data: [],
                    backgroundColor: '#F44336',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Payment Status by Class'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Fetch and update chart data
    async function updateCharts() {
        try {
            const response = await fetch('/api/class-stats');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const stats = await response.json();

            // Update class distribution chart
            classDistributionChart.data.labels = stats.classes;
            classDistributionChart.data.datasets[0].data = stats.studentCounts;
            classDistributionChart.update();

            // Update payment overview chart
            paymentOverviewChart.data.labels = stats.classes;
            paymentOverviewChart.data.datasets[0].data = stats.fullPayments;
            paymentOverviewChart.data.datasets[1].data = stats.partialPayments;
            paymentOverviewChart.data.datasets[2].data = stats.noPayments;
            paymentOverviewChart.update();
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }

    // Initial chart update
    await updateCharts();

    // Update charts when class or session changes
    classSelector.addEventListener('change', updateCharts);
    sessionSelector.addEventListener('change', updateCharts);

    const classSelector = document.getElementById('classSelector');
    const sessionSelector = document.getElementById('sessionSelector'); // Added session selector
    const statusFilter = document.getElementById('statusFilter');
    const generateReportBtn = document.getElementById('generateReportBtn');
    const reportFormatSelector = document.getElementById('reportFormat');
    
    const fullPaymentList = document.getElementById('fullPaymentList');
    const partialPaymentList = document.getElementById('partialPaymentList');
    const noPaymentList = document.getElementById('noPaymentList');

    const fullPaymentSection = document.getElementById('fullPaymentSection');
    const partialPaymentSection = document.getElementById('partialPaymentSection');
    const noPaymentSection = document.getElementById('noPaymentSection');
    const noStudentsMessage = document.getElementById('noStudentsMessage');
    const selectedClassNameHeader = document.getElementById('selectedClassName');

    // Populate class dropdown
    async function populateClasses() {
        try {
            const response = await fetch('/api/classes');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const classes = await response.json();

            classSelector.innerHTML = '<option value="">Select a Class</option>'; // Add a default placeholder option

            classes.forEach(cls => {
                const option = document.createElement('option');
                option.value = cls.id; // API should return {id: '...', name: '...'}
                option.textContent = cls.name;
                classSelector.appendChild(option);
            });

            // Populate sessions immediately
            try {
                const response = await fetch('/api/sessions');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const sessions = await response.json();

                sessionSelector.innerHTML = '<option value="">All Sessions</option>';

                if (sessions.length > 0) {
                    sessions.forEach(session => {
                        const option = document.createElement('option');
                        option.value = session.id;
                        option.textContent = session.name;
                        sessionSelector.appendChild(option);
                    });
                    sessionSelector.disabled = false;
                } else {
                    sessionSelector.innerHTML = '<option value="">No sessions available</option>';
                    sessionSelector.disabled = true;
                }
            } catch (error) {
                console.error('Error fetching sessions:', error);
                sessionSelector.innerHTML = '<option value="">Error loading sessions</option>';
                sessionSelector.disabled = true;
            }

            // Update when class changes
            classSelector.addEventListener('change', displayStudents);
        } catch (error) {
            console.error('Error fetching or populating classes:', error);
            classSelector.innerHTML = '<option value="">Error loading classes</option>';
            sessionSelector.disabled = true;
        }
    }

    // Display students based on selected class and filter
    async function displayStudents() {
        const selectedClassId = classSelector.value;
        const selectedSessionId = sessionSelector.value;
        const selectedFilter = statusFilter.value;

        clearStudentLists();

        // Handle "All Classes" case (empty classId)
        if (!selectedClassId && classSelector.options[0].value === '') {
            hideStudentSections();
            generateReportBtn.disabled = false;
            selectedClassNameHeader.textContent = 'All Classes';
            sessionSelector.disabled = false; // Keep session enabled for "All Classes"
            noStudentsMessage.style.display = 'none';
        } else {
            // If a class is selected
            if (sessionSelector.options.length > 1 && sessionSelector.options[0].value === "") { // more than just placeholder
                sessionSelector.disabled = false;
            } else if (sessionSelector.options.length === 1 && sessionSelector.options[0].value !== "") {
                sessionSelector.disabled = !(sessionSelector.options.length > 0 && sessionSelector.options[0].textContent !== 'Error loading sessions' && sessionSelector.options[0].textContent !== 'No sessions available');
            }

            const selectedOption = classSelector.options[classSelector.selectedIndex];
            selectedClassNameHeader.textContent = selectedOption ? selectedOption.text : '';
            generateReportBtn.disabled = false;
        }

        try {
            let studentApiUrl = `/api/students?classId=${encodeURIComponent(selectedClassId)}`;
            if (selectedSessionId) {
                studentApiUrl += `&sessionId=${encodeURIComponent(selectedSessionId)}`;
            }
            const response = await fetch(studentApiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const students = await response.json(); // API returns array of students: {id, name, graduation_fee_paid}
            
            let studentsToDisplay = [];
            let hasStudentsInAnyCategory = false;

            if (students.length === 0) {
                noStudentsMessage.textContent = 'No students found for this class.';
                noStudentsMessage.style.display = 'block';
                hideStudentSections();
                return;
            }

            students.forEach(student => {
                let category = '';
                if (student.graduation_fee_paid >= GRADUATION_FEE_TOTAL) {
                    category = 'full';
                } else if (student.graduation_fee_paid > 0) {
                    category = 'partial';
                } else {
                    category = 'none';
                }

                if (selectedFilter === 'all' || selectedFilter === category) {
                    studentsToDisplay.push({ ...student, category });
                }
            });

            if (studentsToDisplay.length === 0) { 
                 noStudentsMessage.textContent = 'No students match the current filter for this class.';
                 noStudentsMessage.style.display = 'block';
                 hideStudentSections();
            } else {
                noStudentsMessage.style.display = 'none';
                showStudentSections();
                
                studentsToDisplay.forEach(student => {
                    const listItem = document.createElement('li');
                    // Tailwind classes for the list item
                    listItem.className = 'flex justify-between items-center py-3 px-4 bg-white border-b border-gray-200 last:border-b-0 hover:bg-gray-50 rounded-md mb-1 shadow-sm';
                    
                    const studentNameSpan = document.createElement('span');
                    studentNameSpan.className = 'text-sm text-gray-700';
                    studentNameSpan.textContent = student.name;
                    listItem.appendChild(studentNameSpan);

                    const badge = document.createElement('span');
                    // Tailwind classes for the badge
                    let badgeBgColor = 'bg-gray-200';
                    let badgeTextColor = 'text-gray-700';
                    if (student.category === 'full') {
                        badgeBgColor = 'bg-green-100';
                        badgeTextColor = 'text-green-700';
                    } else if (student.category === 'partial') {
                        badgeBgColor = 'bg-yellow-100';
                        badgeTextColor = 'text-yellow-700';
                    } else if (student.category === 'none') {
                        badgeBgColor = 'bg-red-100';
                        badgeTextColor = 'text-red-700';
                    }
                    badge.className = `px-3 py-1 text-xs font-semibold ${badgeTextColor} ${badgeBgColor} rounded-full`;
                    badge.textContent = `KES ${parseFloat(student.graduation_fee_paid).toFixed(2)}`;
                    listItem.appendChild(badge);

                    if (student.category === 'full') {
                        fullPaymentList.appendChild(listItem);
                        fullPaymentSection.style.display = 'block';
                        hasStudentsInAnyCategory = true;
                    } else if (student.category === 'partial') {
                        partialPaymentList.appendChild(listItem);
                        partialPaymentSection.style.display = 'block';
                        hasStudentsInAnyCategory = true;
                    } else if (student.category === 'none') {
                        noPaymentList.appendChild(listItem);
                        noPaymentSection.style.display = 'block';
                        hasStudentsInAnyCategory = true;
                    }
                });

                // Hide sections if they have no children after filtering
                if (fullPaymentList.children.length === 0) fullPaymentSection.style.display = 'none';
                if (partialPaymentList.children.length === 0) partialPaymentSection.style.display = 'none';
                if (noPaymentList.children.length === 0) noPaymentSection.style.display = 'none';

                if (!hasStudentsInAnyCategory && studentsToDisplay.length > 0) { // This case means all students were filtered out
                     noStudentsMessage.textContent = 'No students match the current filter for this class.';
                     noStudentsMessage.style.display = 'block';
                } else if (!hasStudentsInAnyCategory && studentsToDisplay.length === 0 && students.length > 0) {
                    // This implies students exist for the class, but none match the filter (redundant with above, but good for clarity)
                    noStudentsMessage.textContent = 'No students match the current filter for this class.';
                    noStudentsMessage.style.display = 'block';
                }
            } // End of main 'else' for processing studentsToDisplay
            generateReportBtn.disabled = !hasStudentsInAnyCategory; // Enable/disable based on whether any students are shown
        } catch (error) {
            console.error(`Error fetching students for class ${selectedClassId}:`, error);
            noStudentsMessage.textContent = 'Error loading student data. Please try again.';
            noStudentsMessage.style.display = 'block';
            hideStudentSections();
            generateReportBtn.disabled = true;
        }
    }

    function clearStudentLists() {
        fullPaymentList.innerHTML = '';
        partialPaymentList.innerHTML = '';
        noPaymentList.innerHTML = '';
    }

    function hideStudentSections() {
        fullPaymentSection.style.display = 'none';
        partialPaymentSection.style.display = 'none';
        noPaymentSection.style.display = 'none';
        selectedClassNameHeader.textContent = '';
    }
    
    function showStudentSections() {
        // Visibility is controlled by displayStudents based on content and filter
    }

    // Event Listeners
    classSelector.addEventListener('change', async () => {
        sessionSelector.value = ''; // Reset session when class changes
        
        // Always enable the session selector when a class is selected
        sessionSelector.disabled = false;
        sessionSelector.innerHTML = '<option value="">All Sessions</option>'; // Clear and reset
        
        try {
            const response = await fetch('/api/sessions');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const sessions = await response.json();

            if (sessions.length > 0) {
                sessions.forEach(session => {
                    const option = document.createElement('option');
                    option.value = session.id;
                    option.textContent = session.name;
                    sessionSelector.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error fetching sessions:', error);
            sessionSelector.innerHTML = '<option value="">Error loading sessions</option>';
            sessionSelector.disabled = true;
        }
        
        displayStudents(); // Update the student list after session options are populated
    });
    sessionSelector.addEventListener('change', displayStudents);
    statusFilter.addEventListener('change', displayStudents);

generateReportBtn.addEventListener('click', () => {
    const selectedClassId = classSelector.value;
    const selectedFilter = statusFilter.value;
    const reportFormat = reportFormatSelector.value;

    const selectedSessionId = sessionSelector.value;

    // Allow "All Classes" case (empty classId)
    if (!selectedClassId && classSelector.options[0].value === '') {
        // This is the "All Classes" case - it's valid
    } else if (!selectedClassId) {
        // This means no class is selected (empty dropdown)
        alert('Please select a class first.');
        return;
    }
    // Construct URL for report generation
    let reportUrl = `/api/generate-report?classId=${encodeURIComponent(selectedClassId)}&statusFilter=${selectedFilter}&format=${reportFormat}`;
    if (selectedSessionId) {
        reportUrl += `&sessionId=${encodeURIComponent(selectedSessionId)}`;
    }
    window.location.href = reportUrl; // Trigger download
});

    // Initial setup
    populateClasses();
    hideStudentSections(); // Initially hide sections
    noStudentsMessage.style.display = 'none'; // Hide no students message initially
    // Enable report button by default since "All Classes" is valid
    generateReportBtn.disabled = false;
}); // Close DOMContentLoaded listener

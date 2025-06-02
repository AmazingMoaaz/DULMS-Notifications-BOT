/**
 * DULMS Notifications Bot Frontend Script
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const scraperForm = document.getElementById('scraperForm');
    const submitBtn = document.getElementById('submitBtn');
    const resultsCard = document.getElementById('resultsCard');
    const logOutput = document.getElementById('logOutput');
    const statusBadge = document.getElementById('statusBadge');
    const summaryContainer = document.getElementById('summaryContainer');
    const assignmentsTable = document.getElementById('assignmentsTable');
    const quizzesTable = document.getElementById('quizzesTable');
    
    // Form submission
    scraperForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form values
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const captchaApiKey = document.getElementById('captchaApiKey').value;
        const discordWebhook = document.getElementById('discordWebhook').value;
        
        // Validate form
        if (!username || !password || !captchaApiKey) {
            displayLog('Please fill in all required fields', 'error');
            return;
        }
        
        // Reset UI
        resetResults();
        
        // Show results area
        resultsCard.classList.remove('d-none');
        
        // Update UI
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        statusBadge.textContent = 'Running';
        statusBadge.className = 'badge bg-info';
        
        // Display initial log
        displayLog('Starting DULMS scraper...', 'info');
        
        // Call the API
        startScraper(username, password, captchaApiKey, discordWebhook);
    });
    
    /**
     * Starts the scraper process
     */
    function startScraper(username, password, captchaApiKey, discordWebhook) {
        // Create the request body
        const requestBody = {
            username: username,
            password: password,
            captcha_api_key: captchaApiKey,
        };
        
        // Add discord webhook if provided
        if (discordWebhook) {
            requestBody.discord_webhook = discordWebhook;
        }
        
        // Call the API to start scraper
        fetch('/api/v1/scraper/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`API returned status ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            displayLog(`Task started with ID: ${data.task_id}`, 'success');
            
            // Start listening for logs
            listenForLogs(data.task_id);
        })
        .catch(error => {
            displayLog(`Error starting task: ${error.message}`, 'error');
            updateStatus('error');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Try Again';
        });
    }
    
    /**
     * Listen for logs using Server-Sent Events
     */
    function listenForLogs(taskId) {
        const logSource = new EventSource(`/api/v1/scraper/logs/${taskId}`);
        
        // Log event
        logSource.addEventListener('log', function(event) {
            const logData = JSON.parse(event.data);
            displayLog(logData.message, logData.level.toLowerCase());
        });
        
        // Status event
        logSource.addEventListener('status', function(event) {
            const statusData = JSON.parse(event.data);
            updateStatus(statusData.status);
        });
        
        // Result event
        logSource.addEventListener('result', function(event) {
            const resultData = JSON.parse(event.data);
            showResults(resultData);
        });
        
        // Error event
        logSource.addEventListener('error', function(event) {
            if (event.data) {
                const errorData = JSON.parse(event.data);
                displayLog(`Error: ${errorData.message}`, 'error');
            } else {
                displayLog('Connection to log stream lost', 'error');
            }
            updateStatus('error');
            logSource.close();
        });
        
        // When the connection is closed
        logSource.addEventListener('close', function() {
            logSource.close();
            submitBtn.disabled = false;
            submitBtn.textContent = 'Check Again';
        });
    }
    
    /**
     * Display a log message
     */
    function displayLog(message, level = 'info') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        
        const logContent = logOutput.querySelector('.log-content');
        logContent.appendChild(logEntry);
        
        // Auto scroll to bottom
        logOutput.scrollTop = logOutput.scrollHeight;
    }
    
    /**
     * Update task status in UI
     */
    function updateStatus(status) {
        if (status === 'completed') {
            statusBadge.textContent = 'Completed';
            statusBadge.className = 'badge bg-success';
            displayLog('Task completed successfully', 'success');
        } else if (status === 'error') {
            statusBadge.textContent = 'Error';
            statusBadge.className = 'badge bg-danger';
        } else {
            statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusBadge.className = 'badge bg-info';
        }
    }
    
    /**
     * Show scraped results in the UI
     */
    function showResults(resultData) {
        // Show summary container
        summaryContainer.classList.remove('d-none');
        
        // Process assignments
        if (resultData.assignments && resultData.assignments.length > 0) {
            const table = createDataTable(resultData.assignments, ['title', 'course', 'deadline', 'days_remaining', 'status']);
            assignmentsTable.innerHTML = '';
            assignmentsTable.appendChild(table);
        } else {
            assignmentsTable.innerHTML = '<p>No assignments found</p>';
        }
        
        // Process quizzes
        if (resultData.quizzes && resultData.quizzes.length > 0) {
            const table = createDataTable(resultData.quizzes, ['title', 'course', 'deadline', 'days_remaining', 'status']);
            quizzesTable.innerHTML = '';
            quizzesTable.appendChild(table);
        } else {
            quizzesTable.innerHTML = '<p>No quizzes found</p>';
        }
    }
    
    /**
     * Create a table from data
     */
    function createDataTable(data, fields) {
        const table = document.createElement('table');
        table.className = 'table data-table';
        
        // Create header row
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        // Add headers
        const headers = {
            'title': 'Title',
            'course': 'Course',
            'deadline': 'Deadline',
            'days_remaining': 'Days Left',
            'status': 'Status'
        };
        
        fields.forEach(field => {
            const th = document.createElement('th');
            th.textContent = headers[field] || field.charAt(0).toUpperCase() + field.slice(1).replace('_', ' ');
            headerRow.appendChild(th);
        });
        
        // Add link header
        const linkHeader = document.createElement('th');
        linkHeader.textContent = 'Link';
        headerRow.appendChild(linkHeader);
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create table body
        const tbody = document.createElement('tbody');
        
        data.forEach(item => {
            const row = document.createElement('tr');
            
            // Add row class based on days remaining
            if (item.days_remaining !== null) {
                if (item.days_remaining <= 0) {
                    row.classList.add('deadline-urgent');
                } else if (item.days_remaining <= 2) {
                    row.classList.add('deadline-warning');
                }
            }
            
            fields.forEach(field => {
                const td = document.createElement('td');
                
                if (field === 'status') {
                    td.textContent = item[field];
                    if (item[field].toLowerCase() === 'submitted' || item[field].toLowerCase() === 'completed') {
                        td.classList.add('status-completed');
                    } else {
                        td.classList.add('status-pending');
                    }
                } else if (field === 'days_remaining') {
                    td.textContent = item[field] !== null ? item[field] : 'N/A';
                } else {
                    td.textContent = item[field];
                }
                
                row.appendChild(td);
            });
            
            // Add link cell
            const linkCell = document.createElement('td');
            if (item.url) {
                const link = document.createElement('a');
                link.href = item.url;
                link.textContent = 'Open';
                link.target = '_blank';
                linkCell.appendChild(link);
            } else {
                linkCell.textContent = 'N/A';
            }
            row.appendChild(linkCell);
            
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        return table;
    }
    
    /**
     * Reset the results area
     */
    function resetResults() {
        const logContent = logOutput.querySelector('.log-content');
        logContent.innerHTML = '';
        summaryContainer.classList.add('d-none');
        assignmentsTable.innerHTML = '';
        quizzesTable.innerHTML = '';
    }
});

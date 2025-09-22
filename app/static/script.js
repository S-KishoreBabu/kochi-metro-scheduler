// In app/static/script.js

function openTab(tabName) {
    let tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
    }
    let tabButtons = document.getElementsByClassName("tab-button");
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].className = tabButtons[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    event.currentTarget.className += " active";
}

function displayEligibilityGrid(scheduleData) {
    const gridContainer = document.getElementById('eligibilityGridContainer');
    gridContainer.innerHTML = '';
    const ELIGIBLE_IMG_URL = "https://ik.imagekit.io/khfpxrcgz/icons8-train-64.png?updatedAt=1758482866598";
    const INELIGIBLE_IMG_URL = "https://ik.imagekit.io/khfpxrcgz/icons8-train-64%20(1).png?updatedAt=1758482866322";

    scheduleData.forEach(train => {
        const isEligible = train.is_eligible;
        const imageUrl = isEligible ? ELIGIBLE_IMG_URL : INELIGIBLE_IMG_URL;
        const statusClass = isEligible ? 'eligible' : 'ineligible';
        const statusText = isEligible ? 'Eligible' : 'Ineligible';
        const trainCard = document.createElement('div');
        trainCard.className = `train-card ${statusClass}`;
        trainCard.innerHTML = `
            <img src="${imageUrl}" alt="Train ${train.train_id}">
            <div class="train-id">${train.train_id}</div>
            <div class="status ${statusClass}">${statusText}</div>
        `;
        gridContainer.appendChild(trainCard);
    });
}

// In app/static/script.js

function displayRankedTable(scheduleData) {
    const tableBody = document.getElementById('scheduleTableBody');
    tableBody.innerHTML = '';
    scheduleData.filter(train => train.is_eligible).forEach(train => {
        const brandScore = train.brand_score !== -1 ? `${train.brand_score.toFixed(0)}%` : 'N/A';
        
        // --- THIS IS THE FIX: Multiply by 100 ---
        const suitabilityScore = train.suitability_score !== -1 
            ? `${(train.suitability_score * 100).toFixed(1)}%` 
            : 'N/A';

        tableBody.innerHTML += `<tr>
            <td>${train.rank}</td>
            <td><b>${train.train_id}</b></td>
            <td>${brandScore}</td>
            <td>${train.mileage} km</td>
            <td>${train.shunting_cost} units</td>
            <td><b>${suitabilityScore}</b></td>
            <td>
                <div class="info-icon">ⓘ
                    <span class="tooltip">${train.explanation}</span>
                </div>
            </td>
        </tr>`;
    });
}

function displayBrandingDetails(scheduleData) {
    const tableBody = document.getElementById('brandingTableBody');
    tableBody.innerHTML = '';
    scheduleData.forEach(train => {
        // --- CORRECTED LOGIC ---
        // Format score as a percentage only if it's a valid score (not -1)
        const brandScore = train.brand_score !== -1 
            ? `${train.brand_score.toFixed(0)}%` 
            : 'N/A';

        tableBody.innerHTML += `<tr>
            <td>${train.train_id}</td>
            <td>${train.branding_type || 'N/A'}</td>
            <td>${train.total_hours_required != null ? train.total_hours_required : 'N/A'}</td>
            <td>${train.hours_accomplished_total != null ? train.hours_accomplished_total : 'N/A'}</td>
            <td>${brandScore}</td>
        </tr>`;
    });
}

// In app/static/script.js

function displaySuitabilityGrid(scheduleData) {
    const gridContainer = document.getElementById('suitabilityGridContainer');
    gridContainer.innerHTML = '';
    scheduleData.forEach(train => {
        const isEligible = train.is_eligible;
        const score = train.suitability_score;
        let batteryClass = '', batteryWidth = 0, scoreText = '';
        
        if (isEligible) {
            // --- THIS IS THE FIX: Multiply score by 100 ---
            const scorePercent = score * 100;
            batteryWidth = scorePercent;
            scoreText = `Score: ${scorePercent.toFixed(1)}%`;

            if (scorePercent > 70) { batteryClass = 'high'; } 
            else if (scorePercent > 40) { batteryClass = 'medium'; } 
            else { batteryClass = 'low'; }
        } else {
            batteryClass = 'ineligible';
            batteryWidth = 0;
            scoreText = 'Ineligible';
        }
        
        const batteryCard = document.createElement('div');
        batteryCard.className = 'battery-card';
        batteryCard.innerHTML = `
            <div class="train-id">${train.train_id}</div>
            <div class="battery-container">
                <div class="battery-level ${batteryClass}" style="width: ${batteryWidth}%;"></div>
            </div>
            <div class="score-text">${scoreText}</div>
        `;
        gridContainer.appendChild(batteryCard);
    });
}

function displayDepotLayout(depotData) {
    const depotContainer = document.getElementById('depotGridContainer');
    depotContainer.innerHTML = '';
    depotContainer.className = 'depot-container';
    const bays = {};
    depotData.forEach(train => {
        if (!bays[train.bay_number]) { bays[train.bay_number] = []; }
        bays[train.bay_number].push(train);
    });
    for (const bayNumber in bays) {
        const bayDiv = document.createElement('div');
        bayDiv.className = 'depot-bay';
        let trainsHTML = `<div class="bay-label">Bay ${bayNumber}</div>`;
        bays[bayNumber].sort((a, b) => a.position_in_bay - b.position_in_bay);
        bays[bayNumber].forEach(train => {
            // --- NEW: Logic to determine the border color class ---
            let statusClass = 'ineligible'; // Default
            if (train.is_eligible) {
                statusClass = 'eligible'; // Green for eligible
                // If brand_score is high, it's a priority
                if (train.brand_score > 75) {
                    statusClass = 'must-run'; // Blue for high priority
                }
            }
            trainsHTML += `<div class="train-block ${statusClass}">${train.train_id}</div>`;
        });
        bayDiv.innerHTML = trainsHTML;
        depotContainer.appendChild(bayDiv);
    }
}

// In app/static/script.js

// --- Add this function to the end of the file ---
function displayHistoryTable(historyData) {
    const table = document.getElementById('historyTable');
    const tableBody = document.getElementById('historyTableBody');
    const messageDiv = document.getElementById('historyMessage');
    
    tableBody.innerHTML = ''; // Clear previous results
    messageDiv.textContent = ''; // Clear previous messages
    
    if (historyData.message) {
        // Display "No history found" message
        messageDiv.textContent = historyData.message;
        table.style.display = 'none';
        return;
    }

    // If we have data, show the table and populate it
    table.style.display = 'table';
    historyData.forEach(rec => {
        // Convert score from 0-1 to 0-100%
        const scorePercent = (rec.suitability_score * 100).toFixed(1);
        tableBody.innerHTML += `<tr>
            <td>${rec.recommended_rank}</td>
            <td><b>${rec.train_id}</b></td>
            <td>${scorePercent}%</td>
        </tr>`;
    });
}


// In app/static/script.js

// --- FINAL, UNIFIED Main Execution Block ---
document.addEventListener('DOMContentLoaded', function() {
    // --- PART 1: Load the main dashboard on page load ---
    document.querySelector('.tab-button').click();
    
    fetch('/api/get_schedule')
        .then(response => response.json())
        .then(data => {
            console.log("Schedule data received:", data);
            if (Array.isArray(data)) {
                displayEligibilityGrid(data);
                displayRankedTable(data);
                displayBrandingDetails(data);
                displaySuitabilityGrid(data);
            } else {
                console.error("API did not return an array for schedule data:", data);
            }
        })
        .catch(error => console.error('Error fetching schedule data:', error));

    fetch('/api/get_depot_layout')
        .then(response => response.json())
        .then(data => {
            console.log("Depot data received:", data);
            if (Array.isArray(data)) {
                displayDepotLayout(data);
            } else {
                console.error("API did not return an array for depot data:", data);
            }
        })
        .catch(error => console.error('Error fetching depot layout:', error));
    
    // --- PART 2: Set up the listener for the history button ---
    document.getElementById('fetchHistoryBtn').addEventListener('click', function() {
        const dateInput = document.getElementById('historyDate');
        const selectedDate = dateInput.value;

        if (!selectedDate) {
            document.getElementById('historyMessage').textContent = 'Please select a date.';
            return;
        }

        fetch(`/api/get_history?date=${selectedDate}`)
            .then(response => response.json())
            .then(data => {
                console.log(`History data for ${selectedDate}:`, data);
                displayHistoryTable(data);
            })
            .catch(error => {
                console.error('Error fetching history:', error);
                document.getElementById('historyMessage').textContent = 'An error occurred while fetching data.';
            });
    });
});
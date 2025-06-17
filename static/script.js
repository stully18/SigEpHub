// --- Google Sheets API Configuration ---
const API_KEY = 'AIzaSyDkgtJlraDbzyxGiex4zyMvVuB-GSrX7rw'; // Replace with your actual API Key
const SPREADSHEET_ID = '12ZcH3BaGC-J_96nF-8ujTmb_2D5SXVZJt1nN5gBsLac'; // Replace with your Spreadsheet ID
const SHEET_NAME = 'Sperm_Points'; // Replace with your Sheet Name (e.g., "Leaderboard")
const RANGE = 'A:B'; // *** UPDATED: Now A:B for Player Name and Points ***

// --- DOM Elements ---
const leaderboardTableBody = document.querySelector('#leaderboard-table tbody');
const lastUpdatedSpan = document.getElementById('last-updated');
const loadingMessage = document.querySelector('.leaderboard .loading-message');
const errorMessage = document.querySelector('.leaderboard .error-message');

/**
 * Fetches leaderboard data from Google Sheets and updates the table.
 */
async function fetchLeaderboardData() {
    loadingMessage.style.display = 'block'; // Show loading message
    errorMessage.style.display = 'none';    // Hide error message
    leaderboardTableBody.innerHTML = '';    // Clear existing data

    const url = `https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}/values/${SHEET_NAME}!${RANGE}?key=${API_KEY}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const rows = data.values;

        if (rows && rows.length > 1) { // Assuming first row is headers
            const leaderboardData = rows.slice(1); // Get data rows

            // Sort data by points in descending order before displaying
            // Assuming points are in the second column (index 1)
            leaderboardData.sort((a, b) => (parseInt(b[1]) || 0) - (parseInt(a[1]) || 0));

            leaderboardData.forEach(row => {
                // *** UPDATED: Only Player Name (index 0) and Points (index 1) ***
                const playerName = row[0] || 'N/A';
                const points = row[1] || '0'; // Default to 0 if points are missing

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${playerName}</td>
                    <td>${points}</td>
                `;
                leaderboardTableBody.appendChild(tr);
            });
            lastUpdatedSpan.textContent = new Date().toLocaleTimeString(); // Update last updated time
        } else {
            leaderboardTableBody.innerHTML = '<tr><td colspan="2">No leaderboard data found.</td></tr>'; // *** UPDATED colspan ***
            lastUpdatedSpan.textContent = new Date().toLocaleTimeString();
        }
    } catch (error) {
        console.error("Error fetching leaderboard data:", error);
        errorMessage.style.display = 'block'; // Show error message
        leaderboardTableBody.innerHTML = ''; // Clear table on error
        lastUpdatedSpan.textContent = "Failed";
    } finally {
        loadingMessage.style.display = 'none'; // Hide loading message
    }
}

// --- Initial Load ---
fetchLeaderboardData();

// --- Refresh Every Hour ---
const ONE_HOUR = 60 * 60 * 1000;
setInterval(fetchLeaderboardData, ONE_HOUR);